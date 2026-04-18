# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 集合竞价策略模块
参与早盘集合竞价交易

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
from core.state_manager import StateManager

# 修复：移除模块级别的 logger 获取

class AuctionStrategy:
    def __init__(self, engine, state_mgr: StateManager):
        self.engine = engine
        self.state_mgr = state_mgr
        self.executed_today = False

    def execute(self):
        """执行集合竞价卖出策略"""
        log = get_logger()  # 动态获取
        
        if self.executed_today:
            return
        
        if not self.state_mgr.elite_list:
            log.log("[竞价] 名单为空，跳过")
            self.executed_today = True
            return

        log.log("[竞价] >>> 开始执行精英名单卖出")
        positions = self.engine.query_positions()
        hold_map = {p.stock_code: p for p in positions if p.volume > 0}
        
        sold_count = 0
        failed_codes = []
        
        for code, data in list(self.state_mgr.elite_list.items()):
            if code not in hold_map:
                log.log("[竞价] " + str(code) + " 未找到持仓，从名单移除")
                del self.state_mgr.elite_list[code]
                continue
            
            pos = hold_map[code]
            if pos.can_use_volume <= 0:
                log.log("[竞价] " + str(code) + " 无可用数量，跳过")
                continue
            
            ticks = self.engine.get_tick_data([code])
            curr_price = ticks.get(code, {}).get('lastPrice', 0.0) if ticks else 0.0
            if curr_price == 0: 
                curr_price = data.get('close_price', 0.0)
            
            if curr_price <= 0:
                log.log("[竞价] " + str(code) + " 价格无效，跳过")
                continue
            
            sell_price = round(curr_price * settings.AUCTION_SELL_RATIO, 2)
            
            # 跌停保护
            limit_down = ticks.get(code, {}).get('limitDown', 0.0) if ticks else 0.0
            if limit_down > 0 and sell_price < limit_down:
                sell_price = limit_down
                log.log("[竞价] " + str(code) + " 触发跌停保护，使用跌停价：" + str(sell_price))

            if self.engine.order_stock(code, "SELL", pos.can_use_volume, sell_price, "AUCTION_ELITE"):
                sold_count += 1
                # 卖出后从内存移除
                del self.state_mgr.elite_list[code]
            else:
                failed_codes.append(code)
                log.log("[竞价] " + str(code) + " 下单失败")
        
        log.log("[竞价] 结束，成功 " + str(sold_count) + " 单，失败 " + str(len(failed_codes)) + " 单")
        self.state_mgr.save_elite_list() # 更新文件
        self.executed_today = True

    def reset_daily(self):
        self.executed_today = False