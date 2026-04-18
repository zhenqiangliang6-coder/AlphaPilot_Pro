# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 延时策略执行模块
支持特定时间窗口的延时交易逻辑

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
import datetime
from utils.logger import get_logger
from config import settings

class DelayedStrategy:
    def __init__(self, engine):
        self.engine = engine
        
        # --- 路径配置 ---
        mpython_root = os.path.dirname(os.path.dirname(__file__))
        self.personalities_file = os.path.join(mpython_root, "data", "stock_personalities.json")
        self.watchlist_file = os.path.join(mpython_root, "data", "delayed_watchlist.json")
        
        # 加载个性化配置
        self.stock_personalities = self._load_personalities()
        
        # 加载观察名单
        self.delayed_watchlist = self._load_watchlist()
        
        # 记录最后处理时间（用于信号去重）
        self.last_signal_time = {}

    def _load_personalities(self):
        logger = get_logger()
        if not os.path.exists(self.personalities_file):
            if logger: 
                logger.log("[错误] 配置文件未找到: " + str(self.personalities_file))
                logger.log("[提示] 请检查 data 文件夹下是否有 stock_personalities.json")
            return {}
        try:
            with open(self.personalities_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if logger: 
                logger.log("[成功] 加载配置文件: " + str(self.personalities_file))
            return data
        except Exception as e:
            if logger: 
                logger.log("[错误] 读取配置文件失败: " + str(e))
            return {}

    def _load_watchlist(self):
        logger = get_logger()
        if not os.path.exists(self.watchlist_file):
            empty_list = {"last_update": "", "watchlist": {}}
            self._save_watchlist(empty_list)
            if logger: 
                logger.log("[初始化] 创建空的观察名单文件")
            return empty_list
        try:
            with open(self.watchlist_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if logger: 
                count = len(data.get('watchlist', {}))
                logger.log("[初始化] 加载观察名单：" + str(count) + "只股票")
            return data
        except Exception as e:
            if logger: 
                logger.log("[警告] 加载观察名单失败，重置为空：" + str(e))
            return {"last_update": "", "watchlist": {}}

    def _save_watchlist(self, data=None):
        logger = get_logger()
        if data is None:
            data = self.delayed_watchlist
            
        # 更新时间戳
        data['last_update'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        temp_file = self.watchlist_file + ".tmp"
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # 原子替换
            if os.path.exists(self.watchlist_file):
                os.remove(self.watchlist_file)
            os.rename(temp_file, self.watchlist_file)
            if logger: 
                logger.log("[保存] 观察名单已更新：" + str(len(data.get('watchlist', {}))) + "只")
        except Exception as e:
            if logger: 
                logger.log("[错误] 保存观察名单失败：" + str(e))

    def _normalize_code(self, code):
        """
        标准化股票代码：用于匹配 stock_personalities.json 中的键名
        策略：如果带 .SH/.SZ 后缀，先尝试直接匹配；若失败则去后缀再匹配
        """
        if code in self.stock_personalities:
            return code
        
        # 尝试去掉后缀（如 688392.SH -> 688392）
        clean_code = code.split('.')[0]
        if clean_code in self.stock_personalities:
            return clean_code
            
        return code

    def process_signal(self, code, action, price, volume_ratio):
        """
        处理信号，判断是否加入延时观察名单
        
        重要原则：
        - 只处理 BUY 信号
        - SELL 信号直接返回 False，让信号继续走正常卖出流程
        - 严禁拦截或影响任何卖出操作
        - 【新增】如果股票已在观察名单中且今天是目标日，拒绝重复加入
        """
        logger = get_logger()
        
        # 1. 拒绝 SELL - 卖出不走延时策略，直接放行
        if action != "BUY":
            if logger: 
                logger.log("[延时策略] {} SELL信号不走延时流程，放行到正常卖出逻辑".format(code))
            return False
        
        # 2. 获取配置 (使用标准化后的代码进行匹配)
        match_code = self._normalize_code(code)
        config = self.stock_personalities.get(match_code, self.stock_personalities.get('default', {}))
        stock_type = config.get('type', 'immediate')
        
        if stock_type != 'delayed':
            return False

        # 3. 量比过滤
        min_vr = config.get('min_volume_ratio', 18.0)
        if volume_ratio < min_vr:
            if logger: 
                logger.log("[延时过滤] " + str(code) + " 量比不足")
            return False
        
        # 4. 【新增】检查是否已在观察名单中
        today = datetime.date.today()
        if code in self.delayed_watchlist.get('watchlist', {}):
            existing_item = self.delayed_watchlist['watchlist'][code]
            existing_target_date_str = existing_item.get('target_date', '')
            
            if existing_target_date_str:
                existing_target_date = datetime.datetime.strptime(existing_target_date_str, '%Y-%m-%d').date()
                
                # 如果今天已经是目标日，拒绝重复加入（防止自动延期）
                if today >= existing_target_date:
                    if logger:
                        logger.log("[延时策略-拒绝重复] {} 已在观察名单中且今天({})是目标日，拒绝重新加入，避免自动延期".format(
                            code, today.strftime('%Y-%m-%d')))
                        logger.log("[延时策略-拒绝重复] 现有记录: signal_date={}, target_date={}".format(
                            existing_item.get('signal_date'), existing_target_date_str))
                    return False
                
                # 如果还没到目标日，更新现有记录（可选：根据需求决定是否允许更新）
                if logger:
                    logger.log("[延时策略-已存在] {} 已在观察名单中，目标日={}，跳过重复信号".format(
                        code, existing_target_date_str))
                return False
            
        # 5. 加入名单 (依然使用原始 code 作为键，保持与 QMT API 一致)
        signal_date = datetime.date.today()
        delay_days = config.get('delay_days', 1)
        # 修复负数死循环
        delay_days = max(0, int(delay_days)) 
        target_date = self._calculate_target_date(signal_date, delay_days)
        
        watchlist_item = { 
            'name': config.get('name', code), 
            'action': 'BUY', 
            'signal_date': signal_date.strftime('%Y-%m-%d'), 
            'target_date': target_date.strftime('%Y-%m-%d'), 
            'trigger_price': price, 
            'trigger_volume_ratio': volume_ratio, 
            'status': 'waiting', 
            'delay_days': delay_days 
        } 
        
        self.delayed_watchlist['watchlist'][code] = watchlist_item
        self._save_watchlist() 
        
        if logger: 
            logger.log("[延时策略] " + str(code) + " 已加入观察名单")
        return True

    def _calculate_target_date(self, signal_date, delay_days):
        # 防死循环保护
        target = signal_date
        remaining = delay_days
        safety_counter = 0
        
        while remaining > 0 and safety_counter < 50: # 最多算50天
            target += datetime.timedelta(days=1)
            if target.weekday() < 5: # 跳过周末
                remaining -= 1
            safety_counter += 1
            
        return target

    def check_and_execute(self):
        """
        检查观察名单，判断是否到达目标日期并执行买入
        
        执行时机：
        - 由 main.py 主循环调用（在交易时段内）
        - 默认在主循环中每 5 秒检查一次（取决于 settings.HEARTBEAT_INTERVAL）
        
        策略逻辑：
        - 等待期（未到期）：坚决不买入（除非量比 >= 30.0 的超强信号，见 process_recent_signals）
        - 到期日当天：
          * 路径 A（信号优先）：出现新信号且量比 >= trigger_volume_ratio → 立即买入（抓最低点）
          * 路径 B（保底机制）：14:39 之后 → 必须买入（防止踏空）
        
        【重要修复】2026-04-14：
        - 目标日当天，如果量比达到 trigger_volume_ratio，应该立即买入并清除记录
        - 不应该延期到第二天，必须在当天完成交易
        - 【关键】无论买入成功与否，目标日结束后都必须清除记录，防止自动延期
        """
        logger = get_logger()
        watchlist = self.delayed_watchlist.get('watchlist', {})
        if not watchlist:
            return
            
        if logger: 
            logger.log("[延时策略] >>> 开始检查观察名单")
            
        today = datetime.date.today()
        now_time = datetime.datetime.now().strftime("%H%M")  # 当前时间（如 "1439"）
        codes_to_remove = []
        
        for code, item in watchlist.items():
            try:
                target_date_str = item.get('target_date', '')
                if not target_date_str: continue
                    
                target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
                
                if today >= target_date:
                    # ==================== 目标日执行逻辑 ====================
                    
                    # 【路径 A】信号优先：检查是否有新的高量比信号
                    # 尝试获取实时行情和量比
                    executed = False
                    try:
                        ticks = self.engine.get_tick_data([code])
                        if ticks and code in ticks:
                            current_vr = ticks[code].get('volumeRatio', 0)
                            current_price = ticks[code].get('lastPrice', 0)
                            
                            # 获取原始触发量比门槛（从加入名单时的配置）
                            original_trigger_vr = item.get('trigger_volume_ratio', 0)
                            
                            # 【关键修复】目标日当天，只要量比达到原始触发门槛，立即买入
                            # 不再使用 target_day_min_vr，而是使用原始的 trigger_volume_ratio
                            if original_trigger_vr > 0 and current_vr >= original_trigger_vr and current_price > 0:
                                logger.log("[延时策略-信号优先] {} 量比 {:.2f} >= 原始门槛 {:.2f}，立即买入".format(
                                    code, current_vr, original_trigger_vr))
                                success = self._execute_buy(code, item)
                                if success:
                                    logger.log("[延时策略-成功] {} 买入订单已提交".format(code))
                                else:
                                    logger.log("[延时策略-失败] {} 买入订单提交失败，但仍会清除记录（防止延期）".format(code))
                                # 【关键】无论成功与否，都标记为待清除
                                codes_to_remove.append(code)
                                executed = True
                    except Exception as e:
                        if logger:
                            logger.log("[警告] {} 获取行情失败: {}".format(code, e))
                    
                    # 如果路径 A 已经执行买入，跳过后续逻辑
                    if executed:
                        continue

                    # 【路径 B】保底机制：14:39 之后强制买入
                    if now_time >= "1439":
                        if logger:
                            logger.log("[延时策略-保底] {} 到达执行时间（14:39），执行保底买入".format(code))
                        success = self._execute_buy(code, item)
                        if success:
                            logger.log("[延时策略-保底成功] {} 买入订单已提交".format(code))
                        else:
                            logger.log("[延时策略-保底失败] {} 买入订单提交失败，但仍会清除记录（防止延期）".format(code))
                        # 【关键】无论成功与否，都标记为待清除
                        codes_to_remove.append(code)
                    else:
                        if logger:
                            logger.log("[延时策略] {} 未到保底时间（14:39）且量比不足，等待中...".format(code))
                        
            except Exception as e:
                if logger: 
                    logger.log("[错误] 处理股票异常：" + str(e))
                    
        # 清理名单
        for code in codes_to_remove:
            if code in self.delayed_watchlist['watchlist']:
                del self.delayed_watchlist['watchlist'][code]
        if codes_to_remove: 
            self._save_watchlist()
            if logger:
                logger.log("[延时策略-清理] 已从观察名单移除 {} 只股票（无论成败，目标日结束必须清除）".format(len(codes_to_remove)))

    def _execute_buy(self, code, item):
        """
        执行延时策略的买入操作
        
        参数说明：
        - code: 股票代码（如 "600410.SH"）
        - item: 观察名单中的股票信息（包含 trigger_price, trigger_volume_ratio 等）
        
        买入逻辑：
        1. 获取实时行情（优先使用最新价格）
        2. 如果无法获取实时行情，降级使用历史触发价
        3. 计算买入数量（遵循资金管理规范）
        4. 下单报价 = 实时价格 * 1.01（固定溢价 1%）
        5. 如果报价超过涨停价，自动修正为涨停价
        
        【重要】保底买入不进行量比过滤：
        - 保底机制的目的是"防止踏空"，必须确保成交
        - 量比检查只在"信号优先路径"中使用（抓最低点）
        - 保底路径直接使用实时价格买入，不检查量比
        """
        logger = get_logger()
        try:
            # ==================== 获取实时行情 ====================
            ticks = None
            try:
                ticks = self.engine.get_tick_data([code])
            except:
                pass
                
            current_price = 0
            limit_up = 0
            current_vr = 0  # 当前量比
            
            if ticks and code in ticks:
                current_price = ticks[code].get('lastPrice', 0)  # 最新成交价
                limit_up = ticks[code].get('highLimit', 0)       # 涨停价
                current_vr = ticks[code].get('volumeRatio', 0)   # 当前量比
                
            # 如果无法获取实时价格，降级使用历史触发价
            if current_price <= 0:
                current_price = item.get('trigger_price', 0)
                if logger: 
                    logger.log("[警告] {} 无法获取实时行情，使用历史触发价: {}".format(code, current_price))
                
            if current_price <= 0:
                if logger: 
                    logger.log("[错误] {} 价格无效，放弃买入".format(code))
                return False
            
            # ==================== 保底买入：跳过量比检查 ====================
            # 【关键修改】保底机制不进行量比过滤
            # 原因：
            # 1. 保底买入的目的是"防止踏空"，必须确保成交
            # 2. 下午14:39之后，量比可能为0（停牌或无成交），但这不应该阻止买入
            # 3. 量比检查应该在"信号优先路径"中使用（提前触发时抓最低点）
            # 4. 保底路径直接使用实时价格买入，不再检查量比
            
            # 如果需要保留量比日志（仅用于监控，不影响执行）：
            if current_vr == 0:
                if logger:
                    logger.log("[保底买入] {} 量比为0（可能停牌或无成交），但保底机制跳过检查，继续执行".format(code))
            else:
                if logger:
                    logger.log("[保底买入] {} 当前量比: {}（保底机制不检查量比）".format(code, current_vr))
            
            # ==================== 资产查询 ====================
            asset = self.engine.query_asset() 
            if not asset: 
                if logger: 
                    logger.log("[错误] {} 资产查询为空".format(code))
                return False
            
            # 可用资金 = 现金 * 98%（保留 2% 缓冲）
            available_cash = getattr(asset, 'cash', 0) * 0.98
            
            # ==================== 资金管理策略 ====================
            # 每次买入使用可用资金的 80%（保留 20% 后续操作空间）
            # 【可修改】0.8 可调整为 0.7（更保守）或 0.9（更激进）
            SINGLE_ORDER_CASH_RATIO = 0.8
            
            # 单笔买入金额上限 50000 元（防止过度集中）
            # 【可修改】50000 可调整为 30000（更分散）或 80000（更集中）
            FIXED_ORDER_AMOUNT = 50000.0
            
            # 最小下单金额 15000 元（过滤小额交易）
            # 【可修改】15000 可调整为 10000 或 20000
            MIN_ORDER_VALUE = 15000
            
            if available_cash < MIN_ORDER_VALUE:
                if logger: 
                    logger.log("[仓位] {} 现金不足 (剩 {:.2f})".format(code, available_cash))
                return False
                
            # 计算目标买入金额
            target_cash = min(available_cash * SINGLE_ORDER_CASH_RATIO, FIXED_ORDER_AMOUNT)
            if target_cash < MIN_ORDER_VALUE:
                target_cash = available_cash
                
            # 计算买入数量（向下取整到 100 股）
            vol = int((target_cash / current_price) // 100) * 100
            if vol < 100:
                if available_cash >= current_price * 100:
                    vol = 100
                else:
                    return False
                    
            if vol < 100:
                return False
                
            # ==================== 下单定价 ====================
            # 下单报价 = 实时价格 * 1.01（固定溢价 1%）
            # 【可修改】1.01 可调整为 1.005（更保守）或 1.02（更激进）
            order_price = round(current_price * 1.01, 2)
            
            # 如果报价超过涨停价，自动修正为涨停价
            if limit_up > 0 and order_price > limit_up:
                order_price = limit_up
                if logger: 
                    logger.log("[涨停保护] {} 报价修正为涨停价: {}".format(code, order_price))
                
            # ==================== 执行下单 ====================
            success = self.engine.order_stock(code, "BUY", vol, order_price, "DELAYED_V2")
            
            if logger: 
                logger.log("[下单] {} 买入 {} 股 @ {:.2f} 元 (量比: {})".format(code, vol, order_price, current_vr))
                
            return success
            
        except Exception as e:
            if logger: 
                logger.log("[异常] {} 买入失败: {}".format(code, str(e)))
            return False

    def execute(self):
        logger = get_logger()
        if not logger: return
        logger.log("---- 开始执行延时策略 ----")
        self.check_and_execute()
        logger.log("---- 执行结束 ----")

    def process_recent_signals(self):
        """
        处理最近收到的信号，判断是否需要提前触发买入
        这个方法由 signal_strategy 调用，用于信号驱动的提前触发机制
        """
        logger = get_logger()
        if not logger:
            return
        
        # 获取最近的信号文件（这里简化处理，实际应该从信号目录读取）
        # 由于信号已经被 signal_strategy 处理并归档，这里主要处理观察名单中的股票
        # 检查观察名单中是否有股票满足提前触发条件
        
        watchlist = self.delayed_watchlist.get('watchlist', {})
        if not watchlist:
            return
        
        today = datetime.date.today()
        
        for code, item in watchlist.items():
            try:
                # 只处理等待中的股票
                if item.get('status') != 'waiting':
                    continue
                
                target_date_str = item.get('target_date', '')
                if not target_date_str:
                    continue
                
                target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
                
                # 如果还没到目标日期，检查是否有超强信号可以提前触发
                if today < target_date:
                    # 获取当前行情
                    try:
                        ticks = self.engine.get_tick_data([code])
                        if ticks and code in ticks:
                            current_price = ticks[code].get('lastPrice', 0)
                            current_vr = ticks[code].get('volumeRatio', 0)
                            
                            # 获取配置
                            config = self.stock_personalities.get(code, self.stock_personalities.get('default', {}))
                            # 等待期的超高量比门槛（例如 25.0）
                            super_high_vr = config.get('super_high_volume_ratio', 30.0)
                            
                            # 如果出现超强量比信号，提前触发
                            if current_vr >= super_high_vr and current_price > 0:
                                logger.log("[延时策略] ★ {} 出现超强信号，提前触发！".format(code))
                                logger.log("[延时策略] 当前量比: {}, 门槛: {}".format(current_vr, super_high_vr))
                                
                                # 执行买入
                                success = self._execute_buy(code, item)
                                if success:
                                    # 从观察名单移除
                                    if code in self.delayed_watchlist['watchlist']:
                                        del self.delayed_watchlist['watchlist'][code]
                                    self._save_watchlist()
                    except Exception as e:
                        logger.log("[延时策略] 检查提前触发异常: {}".format(e))
                        
            except Exception as e:
                logger.log("[延时策略] 处理信号异常: {}".format(e))
