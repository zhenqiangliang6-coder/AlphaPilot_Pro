# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 信号驱动交易策略模块
读取外部信号文件自动执行买卖操作

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: V8.95 保守版
"""

import os
import json
import shutil
import time
import threading
from config import settings
from utils.logger import get_logger
from utils.helpers import get_index_change_percent

# 修复：移除模块级别的 logger 获取

class SignalStrategy:
    def __init__(self, engine):
        self.engine = engine
        self.order_history = {}
        self.history_lock = threading.Lock()
        # 新增：延时策略引用（可选，如果需要在信号处理时调用）
        self.delayed_strategy = None

    def set_delayed_strategy(self, delayed_strat):
        """设置延时策略实例（用于信号分流）"""
        self.delayed_strategy = delayed_strat

    def process_files(self):
        """
        处理信号文件（增强版）
        
        流程优化：
        1. 读取原始信号
        2. 如果配置了延时策略，先交给它过滤和分流
        3. 未被延时策略接收的信号，继续按原逻辑处理
        """
        log = get_logger()  # 动态获取
        
        if not os.path.exists(settings.SIGNAL_DIR_INPUT):
            log.log("[警告] 信号目录不存在：{}".format(settings.SIGNAL_DIR_INPUT))
            return
        
        try:
            files = [f for f in os.listdir(settings.SIGNAL_DIR_INPUT) if f.endswith(".txt")]
        except Exception as e:
            log.log("[错误] 读取信号目录失败：{}".format(e))
            return

        if not files:
            return

        # 获取大盘数据
        index_change = get_index_change_percent()
        if index_change is not None:
            log.log("[大盘] 上证指数：{}%".format(index_change))
        else:
            log.log("[大盘] 无法获取指数数据，可能影响买入决策")

        for filename in sorted(files):
            path = os.path.join(settings.SIGNAL_DIR_INPUT, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        continue
                    lines = content.split('\n')
                
                processed_any_in_file = False
                
                for line in lines:
                    if not line.strip(): continue
                    try:
                        sig = json.loads(line)
                        code = sig.get('code')
                        action = sig.get('action')
                        price = float(sig.get('price', 0))
                        vr = float(sig.get('volume_ratio', 0))
                        
                        if not code or not action: 
                            continue
                        
                        # 【关键修复】SELL 信号完全绕过延时策略，直接执行卖出逻辑
                        # 确保卖出不受任何策略拦截或过滤
                        if action == "SELL":
                            log.log("[卖出信号] {} 直接进入卖出流程，不经过延时策略".format(code))
                            if self._execute_signal(code, action, price, vr, index_change):
                                processed_any_in_file = True
                            continue
                        
                        # 【新增】BUY 信号优先交给延时策略处理
                        if self.delayed_strategy:
                            # 延时策略只处理 BUY 信号
                            # 如果返回 True，说明已加入观察名单，跳过即时处理
                            if self.delayed_strategy.process_signal(code, action, price, vr):
                                log.log("[信号分流] {} 已加入延时观察名单，跳过即时下单".format(code))
                                processed_any_in_file = True
                                continue
                            # 如果返回 False，说明被过滤或不是慢涨股，继续原逻辑
                        
                        # 执行核心判断链（原逻辑）
                        if self._execute_signal(code, action, price, vr, index_change):
                            processed_any_in_file = True
                            
                    except Exception as e:
                        log.log("[解析] JSON 错误 {}: {}".format(filename, e))
                
                # 无论是否下单，只要解析过就归档，防止重复处理
                if os.path.exists(path):
                    dest = os.path.join(settings.SIGNAL_DIR_PROCESSED, filename)
                    # 如果目标已存在，加时间戳防止覆盖
                    if os.path.exists(dest):
                        dest = os.path.join(settings.SIGNAL_DIR_PROCESSED, "{}_{}".format(int(time.time()), filename))
                    
                    shutil.move(path, dest)
                    log.log("[归档] {} -> processed".format(filename))
                
            except Exception as e:
                log.log("[错误] 处理文件 {} 失败：{}".format(filename, e))

    def _execute_signal(self, code, action, price, vr, index_change):
        """执行单个信号的完整判断与下单"""
        log = get_logger()  # 动态获取
        
        # 【专家优化】移除冗余的配置文件检查逻辑
        # 既然 main.py/process_files 已经先调用了 delayed_strat.process_signal，
        # 能走到这里说明该信号要么不是延时股，要么已被延时策略处理/过滤。
        # 此处不再重复尝试写入观察名单，保持逻辑单一职责，减少 I/O 冲突。
        
        # 1. 策略过滤 (大盘 + 量比)
        if not self._decide_action(action, vr, index_change):
            # log.log("[过滤] {} 不满足策略条件 (VR={}, Index={})".format(code, vr, index_change))
            return False
        
        # 2. 重复保护
        if not self._check_repeat_protection(code, action):
            log.log("[保护] {} {} 在保护期内，跳过".format(code, action))
            return False
        
        # 3. 仓位计算
        allow, vol, reason = self._check_position_and_calculate_volume(code, action, price)
        if not allow:
            log.log("[仓位] {} 计算失败：{}".format(code, reason))
            return False
        
        # 4. 执行下单
        order_price = round(price * (1.01 if action == "BUY" else 0.99), 2)
        if self.engine.order_stock(code, action, vol, order_price, "SIGNAL_V8"):
            return True
        
        return False

    def _decide_action(self, action, vr, index_change):
        """
        策略过滤核心逻辑：根据大盘涨跌幅、量比和时间段决定是否交易
        
        参数说明：
        - action: "BUY" 买入 或 "SELL" 卖出
        - vr: volume_ratio 量比（当前成交量 / 过去5天平均成交量）
        - index_change: 上证指数涨跌幅（如 -1.21 表示跌 1.21%，0.5 表示涨 0.5%）
        
        返回值：True 允许交易，False 拒绝交易
        
        【重要】时间段区分：
        - 上午（09:30-11:30）：使用较低的量比门槛
        - 下午（13:00-15:00）：使用较高的量比门槛（vr >= 3.0），避免午后虚假突破
        """
        import datetime
        
        # 获取当前时间，判断是上午还是下午
        now = datetime.datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        time_str = "{}{:02d}".format(current_hour, current_minute)
        
        # 判断时间段：上午 or 下午
        is_morning = ("0930" <= time_str <= "1130")
        is_afternoon = ("1300" <= time_str <= "2000")
        
        # 如果无法获取大盘数据
        if index_change is None:
            # 买入操作需要大盘数据，没有则拒绝
            if action == "BUY": 
                return False
            # 卖出操作不受大盘影响，默认允许
            index_change = 0.0
        
        # ==================== 买入策略 ====================
        if action == "BUY":
            # 【上午策略】市场活跃度高，使用标准量比门槛
            if is_morning:
                # 情况 1：大盘平稳或小幅上涨（-0.35% ~ +1.8%）
                # 此时市场情绪稳定，量比 >= 1.6 即可买入
                # 【可修改】vr >= 1.6 可调整为 1.5（更激进）或 2.0（更保守）
                if -0.35 <= index_change <= 1.8 and vr >= 2.3: 
                    return True
                
                # 情况 2：大盘小幅下跌（-1.8% ~ -0.35%）
                # 此时市场偏弱，需要更强的量比信号（>= 3.5）才敢买入
                # 【可修改】vr >= 3.5 可调整为 3.0（更激进）或 4.0（更保守）
                if -1.8 <= index_change < -0.35 and vr >= 3.5: 
                    return True
            
            # 【下午策略】市场活跃度下降，必须使用更高的量比门槛（vr >= 3.0）
            elif is_afternoon:
                # 情况 1：大盘平稳或小幅上涨（-0.35% ~ +1.8%）
                # 下午必须有更强的量能支撑，量比 >= 3.0 才买入
                # 【可修改】vr >= 3.0 是下午的最低门槛，可根据实盘调整
                if -0.35 <= index_change <= 1.8 and vr >= 3.0: 
                    return True
                
                # 情况 2：大盘小幅下跌（-1.8% ~ -0.35%）
                # 下午市场偏弱时，需要极强的量比信号（>= 4.5）才考虑买入
                # 【可修改】vr >= 4.5 可调整为 4.0（更激进）或 5.0（更保守）
                if -1.8 <= index_change < -0.35 and vr >= 4.5: 
                    return True
            
            # 其他情况：非交易时间、大盘暴跌（<-1.8%）或大涨（>1.8%）→ 拒绝买入
            return False
        
        # ==================== 卖出策略 ====================
        else:  # action == "SELL"
            # 【上午策略】
            if is_morning:
                # 情况 1：大盘平稳或小幅上涨（-0.35% ~ +1.8%）
                # 市场情绪稳定，量比 >= 1.2 说明有资金出逃，可以卖出
                # 【可修改】vr >= 1.2 可调整为 1.0（更敏感）或 1.5（更保守）
                if -0.35 <= index_change <= 1.8 and vr >= 1.5: 
                    return True
                
                # 情况 2：大盘小幅下跌（-1.8% ~ -0.35%）
                # 市场偏弱，量比 >= 1.0 就可以卖出（降低门槛，快速止盈止损）
                # 【可修改】vr >= 1.0 可调整为 0.8（更敏感）或 1.5（更保守）
                if -1.8 <= index_change < -0.35 and vr >= 1.0: 
                    return True
            
            # 【下午策略】
            elif is_afternoon:
                # 情况 1：大盘平稳或小幅上涨（-0.35% ~ +1.8%）
                # 下午卖出门槛略高，量比 >= 1.5 才卖出（避免过早清仓）
                # 【可修改】vr >= 1.5 可调整为 1.3（更敏感）或 1.8（更保守）
                if -0.35 <= index_change <= 1.8 and vr >= 1.5: 
                    return True
                
                # 情况 2：大盘小幅下跌（-1.8% ~ -0.35%）
                # 下午市场偏弱，量比 >= 1.3 就卖出（及时止损）
                # 【可修改】vr >= 1.3 可调整为 1.0（更敏感）或 1.8（更保守）
                if -1.8 <= index_change < -0.35 and vr >= 1.0: 
                    return True
            
            # 其他情况：非交易时间、大盘暴跌（<-1.8%）或大涨（>1.8%）→ 暂时不卖（观察）
            return False

    def _check_repeat_protection(self, code, action):
        key = "{}_{}".format(code, action)
        now = time.time()
        with self.history_lock:
            if key in self.order_history and now - self.order_history[key] < settings.REPEAT_PROTECT_SECONDS:
                return False
            self.order_history[key] = now
            return True

    def _check_position_and_calculate_volume(self, code, action, price):
        """
        检查仓位并计算下单数量 - V8.5 实战版本
        
        参数说明：
        - code: 股票代码（如 "600410.SH"）
        - action: "BUY" 买入 或 "SELL" 卖出
        - price: 信号触发价格
        
        返回值：
        - (True, volume, "允许"): 允许交易，volume 为买入/卖出股数
        - (False, 0, "原因"): 拒绝交易，返回拒绝原因
        """
        log = get_logger()  # 动态获取
        
        try:
            # 查询当前持仓
            positions = self.engine.query_positions()
            current_vol = 0
            has_position = False
            
            for p in positions:
                if p.stock_code == code:
                    current_vol = p.volume
                    has_position = True
                    break
            
            # ==================== 买入逻辑 ====================
            if action == "BUY":
                # 如果已经持有该股票，允许加仓
                if has_position:
                    log.log("[仓位检查] {} 已持有 {} 股，执行追加买入".format(code, current_vol))
                
                # 查询账户资产
                asset = self.engine.query_asset()
                if not asset:
                    return False, 0, "资产查询失败"
                
                # ==================== [V8.5 资金策略] ====================
                
                # 可用资金 = 现金 * 98%（保留 2% 缓冲，防止计算误差）
                # 【可修改】0.98 可调整为 0.95（保留 5% 缓冲）或 1.0（不保留缓冲）
                available_cash = getattr(asset, 'cash', 0) * 0.98
                
                # 每次买入使用可用资金的 80%（保留 20% 后续操作空间）
                # 【可修改】0.8 可调整为 0.7（更保守）或 0.9（更激进）
                SINGLE_ORDER_CASH_RATIO = 0.8
                
                # 单笔买入金额上限 50000 元（防止过度集中）
                # 【可修改】50000 可调整为 30000（更分散）或 80000（更集中）
                FIXED_ORDER_AMOUNT = 50000.0
                
                # 最小下单金额 15000 元（过滤小额交易，减少手续费占比）
                # 【可修改】15000 可调整为 10000 或 20000
                MIN_ORDER_VALUE = 15000
                
                # 如果可用资金连最小下单金额都不够，拒绝买入
                if available_cash < MIN_ORDER_VALUE:
                    return False, 0, "可用现金不足 (剩 {:.2f})".format(available_cash)
                
                # 计算目标买入金额 = 可用资金 * 80%
                target_cash = available_cash * SINGLE_ORDER_CASH_RATIO
                
                # 如果设置了固定上限，则取较小值（不超过 50000 元）
                if FIXED_ORDER_AMOUNT > 0 and target_cash > FIXED_ORDER_AMOUNT:
                    target_cash = FIXED_ORDER_AMOUNT
                
                # 保底检查：如果目标金额低于最小下单金额，使用全部可用现金
                if target_cash < MIN_ORDER_VALUE:
                    target_cash = available_cash
                
                # 计算买入数量（目标金额 / 股价）
                raw_vol = target_cash / price
                # 向下取整到 100 股的整数倍（A 股最小交易单位）
                vol = int(raw_vol // 100) * 100
                
                # 特殊处理：如果计算结果不足 100 股，但现金足够买 1 手
                if vol < 100:
                    if available_cash >= price * 100:
                        vol = 100
                        log.log("[仓位计算] {} 现金充足，强制买入 100 股".format(code))
                    else:
                        return False, 0, "现金不足以买入 1 手 (需 {:.2f})".format(price*100)
                
                # 最终资金校验：确保订单金额不超过可用资金
                order_value = vol * price
                if order_value > available_cash:
                    # 重新计算最大可买数量
                    vol = int(available_cash / price // 100) * 100
                    if vol < 100:
                        return False, 0, "现金极度不足"
                
                # 最小订单金额检查
                if order_value < MIN_ORDER_VALUE:
                    return False, 0, "金额过低 ({:.2f})".format(order_value)
                
                # 记录日志
                log.log("[仓位计算] {} 计划买入 {} 股 (约 {:.0f} 元)".format(code, vol, vol*price))
                return True, vol, "允许"

            # ==================== 卖出逻辑 ====================
            else:  # action == "SELL"
                # 查询可卖出数量（排除当天买入的部分）
                can_sell_vol = 0
                for p in positions:
                    if p.stock_code == code:
                        can_sell_vol = p.can_use_volume
                        break
                
                # 如果没有可用持仓，拒绝卖出
                if can_sell_vol <= 0:
                    return False, 0, "无可用持仓"
                
                # 允许卖出全部可用持仓
                return True, can_sell_vol, "允许卖出"
                
        except Exception as e:
            log.log("[错误] 仓位计算异常：{}".format(e))
            return False, 0, "计算异常：{}".format(e)