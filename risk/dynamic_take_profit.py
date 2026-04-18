# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 动态止盈模块（完全独立的三级止盈策略）

功能说明：
1. 第一级（快速止盈）：所有股票上涨 3% 后回落 1.3% 立即卖出
2. 第二级（波段止盈）：60/00 开头股票上涨 9% 后 12 分钟卖出
3. 第三级（强势股止盈）：68/30 开头股票上涨 18% 后 12 分钟卖出

设计原则：
- 完全独立于买入策略和其他卖出策略

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: V8.95 保守版
"""
import time
import datetime
import threading
from config import settings
from utils.logger import get_logger

class DynamicTakeProfit:
    def __init__(self, engine):
        self.engine = engine
        
        # 记录每只股票的止盈状态
        # 格式: {code: {
        #     'highest_profit': 0.0,      # 最高涨幅
        #     'peak_time': 0,             # 首次达到峰值的时间戳
        #     'triggered_level1': False,  # 是否已触发第一级
        #     'triggered_level2': False,  # 是否已触发第二级
        #     'triggered_level3': False   # 是否已触发第三级
        # }}
        self.profit_tracker = {}
        self.lock = threading.Lock()
        
        # 止盈参数配置
        # 第一级：所有股票
        self.level1_gain_threshold = 0.03    # 上涨 3%
        self.level1_gain_max = 0.65          # 涨幅上限 65%（超过此值不执行第一级，交由第二/三级处理）
        self.level1_drop_threshold = 0.013   # 回落 1.3%
        
        # 第二级：60/00 开头股票
        self.level2_gain_threshold = 0.09    # 上涨 9%
        self.level2_hold_minutes = 12        # 持有 12 分钟
        
        # 第三级：68/30 开头股票
        self.level3_gain_threshold = 0.18    # 上涨 18%
        self.level3_hold_minutes = 12        # 持有 12 分钟
        
        # 【可配置】动态止盈最早执行时间（HHMM格式）
        # 默认 09:35，避开开盘前5分钟的剧烈波动
        # 如需更早执行，可改为 "0930"；如需更晚，可改为 "1000" 等
        self.EARLIEST_EXECUTION_TIME = "0951"

    def _can_execute_now(self):
        """
        检查当前时间是否允许执行动态止盈
        
        返回：True=可以执行，False=未到执行时间
        
        【实盘修改指南】：
        - 如果想让动态止盈在 9:30 开盘后立即生效，将 EARLIEST_EXECUTION_TIME 改为 "0930"
        - 如果想延迟到 10:00 再执行，将 EARLIEST_EXECUTION_TIME 改为 "1000"
        - 如果想去掉时间限制（全天执行），直接返回 True
        """
        now = datetime.datetime.now()
        current_time = now.strftime("%H%M")
        
        # 判断当前时间是否早于最早执行时间
        if current_time < self.EARLIEST_EXECUTION_TIME:
            return False
        
        return True

    def check(self):
        """
        定期检查持仓，执行动态止盈
        
        调用时机：在主循环中定期调用（建议每 10-15 秒一次）
        
        【重要】时间过滤：
        - 仅在 EARLIEST_EXECUTION_TIME 之后执行（默认 09:35）
        - 避免开盘前5分钟剧烈波动导致误触发
        """
        log = get_logger()
        
        # 【时间检查】未到执行时间，直接跳过
        if not self._can_execute_now():
            # 可选：每分钟输出一次提示日志（避免刷屏）
            now = datetime.datetime.now()
            if now.second < 5:  # 每分钟的前5秒内输出
                log.log("[止盈] 当前时间 {} 早于最早执行时间 {}，暂不执行".format(
                    now.strftime("%H:%M"), 
                    self.EARLIEST_EXECUTION_TIME[:2] + ":" + self.EARLIEST_EXECUTION_TIME[2:]
                ))
            return
        
        positions = self.engine.query_positions()
        
        if not positions:
            return
        
        for pos in positions:
            if pos.volume <= 0:
                continue
            
            code = pos.stock_code
            volume = pos.volume
            open_price = getattr(pos, 'open_price', 0.0)
            
            if open_price <= 0:
                continue
            
            # 获取最新价格
            try:
                ticks = self.engine.get_tick_data([code])
                current_price = ticks.get(code, {}).get('lastPrice', open_price)
                
                if current_price <= 0:
                    current_price = open_price
            except Exception as e:
                log.log("[止盈] 获取 {} 行情失败: {}".format(code, e))
                continue
            
            # 计算当前盈亏比例
            profit_ratio = (current_price - open_price) / open_price
            
            # 更新止盈追踪状态
            self._update_tracker(code, profit_ratio)
            
            # 检查各级止盈条件
            self._check_level1(code, current_price, open_price, volume, profit_ratio)
            self._check_level2(code, current_price, open_price, volume, profit_ratio)
            self._check_level3(code, current_price, open_price, volume, profit_ratio)

    def _update_tracker(self, code, current_profit):
        """更新股票的最高涨幅记录"""
        # 【专家级修复】如果当前时间还没到最早执行时间，不记录峰值时间
        # 防止开盘前的剧烈波动导致计时器提前启动
        if not self._can_execute_now():
            return

        with self.lock:
            if code not in self.profit_tracker:
                self.profit_tracker[code] = {
                    'highest_profit': current_profit,
                    'peak_time': time.time(),
                    'triggered_level1': False,
                    'triggered_level2': False,
                    'triggered_level3': False
                }
            else:
                # 如果当前涨幅创新高，更新时间戳
                if current_profit > self.profit_tracker[code]['highest_profit']:
                    self.profit_tracker[code]['highest_profit'] = current_profit
                    self.profit_tracker[code]['peak_time'] = time.time()

    def _check_level1(self, code, current_price, open_price, volume, profit_ratio):
        """
        第一级止盈：所有股票上涨 3% 后回落 1.3% 立即卖出
        
        逻辑：
        1. 最高涨幅在 3% ~ 65% 之间（超过 65% 交由第二/三级处理）
        2. 当前涨幅 <= 最高涨幅 - 1.3%
        3. 尚未触发过第一级止盈
        """
        log = get_logger()
        
        with self.lock:
            if code not in self.profit_tracker:
                return
            
            tracker = self.profit_tracker[code]
            highest = tracker['highest_profit']
            
            # 检查是否已触发
            if tracker['triggered_level1']:
                return
            
            # 【新增】检查涨幅是否在有效范围内（3% ~ 65%）
            if highest > self.level1_gain_max:
                # 涨幅超过 65%，不执行第一级止盈，交由第二/三级处理
                return
            
            # 判断条件：最高涨过 3%，且当前回落了 1.3%
            if highest >= self.level1_gain_threshold:
                drop_from_peak = highest - profit_ratio
                if drop_from_peak >= self.level1_drop_threshold:
                    log.log("[止盈-快速] {} 触发第一级止盈 (最高涨幅: {:.2f}%, 当前涨幅: {:.2f}%, 回落: {:.2f}%)".format(
                        code, highest * 100, profit_ratio * 100, drop_from_peak * 100))
                    
                    # 执行卖出
                    if self._execute_sell(code, volume, current_price, "止盈-快速(3%回落1.3%)"):
                        tracker['triggered_level1'] = True
                        log.log("[止盈] {} 第一级止盈完成，从追踪列表移除".format(code))

    def _check_level2(self, code, current_price, open_price, volume, profit_ratio):
        """
        第二级止盈：60/00 开头股票上涨 9% 后 12 分钟卖出
        
        逻辑：
        1. 股票代码以 60 或 00 开头
        2. 当前涨幅 >= 9%
        3. 距离首次达到 9% 已过 12 分钟
        """
        log = get_logger()
        
        # 检查代码前缀
        code_prefix = code[:2]
        if code_prefix not in ['60', '00']:
            return
        
        with self.lock:
            if code not in self.profit_tracker:
                return
            
            tracker = self.profit_tracker[code]
            
            # 检查是否已触发
            if tracker['triggered_level2']:
                return
            
            # 判断是否达到涨幅阈值
            if profit_ratio >= self.level2_gain_threshold:
                # 首次达到，记录时间
                if tracker['peak_time'] == 0 or tracker['highest_profit'] < self.level2_gain_threshold:
                    tracker['peak_time'] = time.time()
                    tracker['highest_profit'] = max(tracker['highest_profit'], profit_ratio)
                    log.log("[止盈-波段] {} 首次达到第二级阈值 (涨幅: {:.2f}%)，开始计时 12 分钟".format(
                        code, profit_ratio * 100))
                    return
                
                # 计算持有时间
                hold_seconds = time.time() - tracker['peak_time']
                hold_minutes = hold_seconds / 60.0
                
                if hold_minutes >= self.level2_hold_minutes:
                    log.log("[止盈-波段] {} 触发第二级止盈 (涨幅: {:.2f}%, 持有时间: {:.1f} 分钟)".format(
                        code, profit_ratio * 100, hold_minutes))
                    
                    # 执行卖出
                    if self._execute_sell(code, volume, current_price, "止盈-波段(9%持有12分钟)"):
                        tracker['triggered_level2'] = True
                        log.log("[止盈] {} 第二级止盈完成，从追踪列表移除".format(code))

    def _check_level3(self, code, current_price, open_price, volume, profit_ratio):
        """
        第三级止盈：68/30 开头股票上涨 18% 后 12 分钟卖出
        
        逻辑：
        1. 股票代码以 68 或 30 开头（科创板/创业板）
        2. 当前涨幅 >= 18%
        3. 距离首次达到 18% 已过 12 分钟
        """
        log = get_logger()
        
        # 检查代码前缀
        code_prefix = code[:2]
        if code_prefix not in ['68', '30']:
            return
        
        with self.lock:
            if code not in self.profit_tracker:
                return
            
            tracker = self.profit_tracker[code]
            
            # 检查是否已触发
            if tracker['triggered_level3']:
                return
            
            # 判断是否达到涨幅阈值
            if profit_ratio >= self.level3_gain_threshold:
                # 首次达到，记录时间
                if tracker['peak_time'] == 0 or tracker['highest_profit'] < self.level3_gain_threshold:
                    tracker['peak_time'] = time.time()
                    tracker['highest_profit'] = max(tracker['highest_profit'], profit_ratio)
                    log.log("[止盈-强势] {} 首次达到第三级阈值 (涨幅: {:.2f}%)，开始计时 12 分钟".format(
                        code, profit_ratio * 100))
                    return
                
                # 计算持有时间
                hold_seconds = time.time() - tracker['peak_time']
                hold_minutes = hold_seconds / 60.0
                
                if hold_minutes >= self.level3_hold_minutes:
                    log.log("[止盈-强势] {} 触发第三级止盈 (涨幅: {:.2f}%, 持有时间: {:.1f} 分钟)".format(
                        code, profit_ratio * 100, hold_minutes))
                    
                    # 执行卖出
                    if self._execute_sell(code, volume, current_price, "止盈-强势(18%持有12分钟)"):
                        tracker['triggered_level3'] = True
                        log.log("[止盈] {} 第三级止盈完成，从追踪列表移除".format(code))

    def _execute_sell(self, code, volume, current_price, reason):
        """
        执行卖出操作
        
        参数：
        - code: 股票代码
        - volume: 卖出数量
        - current_price: 当前价格
        - reason: 止盈原因（用于日志记录）
        
        返回：True 成功，False 失败
        """
        log = get_logger()
        
        # 卖出价格：当前价格 * 0.99（略微让利，提高成交率）
        sell_price = round(current_price * 0.99, 2)
        
        log.log("[止盈执行] {} 卖出 {} 股 @ {} ({})".format(code, volume, sell_price, reason))
        
        try:
            success = self.engine.order_stock(code, "SELL", volume, sell_price, reason)
            
            if success:
                log.log("[止盈成功] {} 已卖出，原因: {}".format(code, reason))
                return True
            else:
                log.log("[止盈失败] {} 下单失败".format(code))
                return False
        except Exception as e:
            log.log("[止盈错误] {} 卖出异常: {}".format(code, e))
            return False

    def reset_tracker(self, code):
        """
        重置某只股票的止盈追踪（可选）
        
        使用场景：股票卖出后重新买入，需要重新追踪止盈
        """
        with self.lock:
            if code in self.profit_tracker:
                del self.profit_tracker[code]
