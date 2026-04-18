# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 火箭加仓策略模块
根据盈利阈值（如8万、16万）触发分级加仓

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: V8.95 保守版
"""

from config import settings
from utils.logger import get_logger

# 修复：移除模块级别的 logger 获取，所有 f-string 改为 .format()

class RocketBoost:
    def __init__(self, engine):
        self.engine = engine
        self.stage = 0
        self.fired_l1 = False
        self.fired_l2 = False
        self.boosted_codes = set()  # 记录已加仓的股票

    def check_and_fire(self):
        """检查浮盈并执行火箭加仓"""
        log = get_logger()  # 动态获取
        
        # 计算总浮盈
        total_profit, profit_details = self._calc_profit()
        
        if total_profit <= 0:
            return
        
        log.log("[火箭] 当前总浮盈：{:.2f}元，阶段：{}".format(total_profit, self.stage))
        
        # 状态同步与触发
        if self.stage == 0 and total_profit >= settings.LEVEL_1_THRESHOLD:
            log.log("[火箭] 触发一级点火 (浮盈 {:.2f} >= {})".format(total_profit, settings.LEVEL_1_THRESHOLD))
            self._execute_boost(1, profit_details)
            self.stage = 1
            self.fired_l1 = True
            
        elif self.stage == 1 and total_profit >= settings.LEVEL_2_THRESHOLD:
            log.log("[火箭] 触发二级点火 (浮盈 {:.2f} >= {})".format(total_profit, settings.LEVEL_2_THRESHOLD))
            self._execute_boost(2, profit_details)
            self.stage = 2
            self.fired_l2 = True

    def _calc_profit(self):
        """计算所有持仓的总浮盈"""
        positions = self.engine.query_positions()
        if not positions:
            return 0.0, {}
        
        total_profit = 0.0
        profit_details = {}
        
        for pos in positions:
            if pos.volume <= 0:
                continue
            
            code = pos.stock_code
            volume = pos.volume
            open_price = getattr(pos, 'open_price', 0.0)
            
            # 获取最新价格
            ticks = self.engine.get_tick_data([code])
            current_price = ticks.get(code, {}).get('lastPrice', open_price)
            
            if open_price > 0 and current_price > 0:
                # 计算浮盈：(现价 - 成本价) * 数量
                profit = (current_price - open_price) * volume
                if profit > 0:
                    total_profit += profit
                    profit_details[code] = {
                        'volume': volume,
                        'cost': open_price,
                        'current': current_price,
                        'profit': profit
                    }
        
        return round(total_profit, 2), profit_details

    def _execute_boost(self, stage, profit_details):
        """
        执行加仓逻辑
        策略：选择浮盈最高的股票进行加仓
        """
        log = get_logger()  # 动态获取
        
        if not profit_details:
            log.log("[火箭] 无盈利持仓，跳过加仓")
            return
        
        # 按浮盈排序，选择最好的股票
        sorted_stocks = sorted(
            profit_details.items(), 
            key=lambda x: x[1]['profit'], 
            reverse=True
        )
        
        # 一级点火：加仓 1 只，二级点火：加仓 2 只
        boost_count = 1 if stage == 1 else 2
        
        for i, (code, data) in enumerate(sorted_stocks[:boost_count]):
            if code in self.boosted_codes:
                log.log("[火箭] {} 已加仓过，跳过".format(code))
                continue
            
            current_price = data['current']
            volume = data['volume']
            
            # 加仓数量：原持仓的 50%
            boost_volume = max(int(volume * 0.5 // 100) * 100, 100)
            
            if boost_volume < 100:
                log.log("[火箭] {} 加仓数量不足，跳过".format(code))
                continue
            
            # 检查现金是否足够
            asset = self.engine.query_asset()
            if not asset or boost_volume * current_price > asset.cash:
                log.log("[火箭] {} 现金不足，跳过加仓".format(code))
                continue
            
            # 执行买入
            order_price = round(current_price * 1.01, 2)  # 溢价 1% 确保成交
            if self.engine.order_stock(code, "BUY", boost_volume, order_price, "BOOST_L{}".format(stage)):
                self.boosted_codes.add(code)
                log.log("[火箭] L{} 加仓：{} 买入 {}股 @ {}".format(stage, code, boost_volume, order_price))
            else:
                log.log("[火箭] L{} 加仓失败：{}".format(stage, code))