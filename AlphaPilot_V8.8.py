# -*- coding: utf-8 -*-
# AlphaPilot V8.5-DelayedStop (延迟止损版)
# 核心变更：
# 1. [硬止损优化] 硬止损执行时间从 09:36 推迟至 09:45。
#    - 理由：避免早盘剧烈波动导致的误杀，给个股 9 分钟的缓冲期。
# 2. 保留全链路调试日志与文件防御机制。
# 3. 策略参数维持 V8.3 激进加仓逻辑。

import os
import time
import datetime
import json
import shutil
import threading
import math
import sys

try:
    from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
    from xtquant.xttype import StockAccount
    from xtquant import xtconstant, xtdata
except ImportError:
    print("[致命] 无法导入 xtquant 模块。请在 QMT 终端内运行。")
    sys.exit(1)

# ================= 配置区域 =================
QMT_PATH = r"D:\迅投QMT交易终端 华林证券模拟版\userdata_mini"
ACCOUNT_ID = "10100000030"

# --- [路径架构] ---
# 获取当前脚本所在目录作为项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIGNAL_DIR_INPUT = os.path.join(BASE_DIR, "signals")
PROCESSED_DIR_INPUT = os.path.join(SIGNAL_DIR_INPUT, "processed")

BASE_DIR_SAFE = BASE_DIR
SIGNAL_DIR_SAFE = os.path.join(BASE_DIR_SAFE, "signals")
STATE_FILE = os.path.join(SIGNAL_DIR_SAFE, "yesterday_holdings.json")

# --- [策略参数：精英名单 (竞价)] ---
ELITE_PROFIT_THRESHOLD = 0.13  # 精英筛选阈值
AUCTION_SELL_RATIO = 0.95      # 竞价卖出报价系数

# --- [策略参数：无限加仓 (盘中)] ---
LEVEL_1_THRESHOLD = 9000.0     
LEVEL_2_THRESHOLD = 18000.0    
REPEAT_PROTECT_SECONDS = 540   # 重复下单保护时间
MIN_ORDER_VALUE = 15000         # 最小下单金额

# --- [资金策略] ---
SINGLE_ORDER_CASH_RATIO = 0.8   # 每次买入可用现金比例
FIXED_ORDER_AMOUNT = 50000.0    # 单次买入金额上限

# --- [策略参数：风控] ---
STOP_LOSS_RATIO = 0.08         # 硬止损阈值 (-1.8%)
STOP_LOSS_CHECK_INTERVAL = 5    # 止损检查频率
STOP_LOSS_START_TIME = "1045"   # 【新增】硬止损开始执行时间 (设为 0955 即 9:55 后执行)
# 如果想彻底关闭硬止损，请将下面的 ENABLE_HARD_STOP 设为 False
ENABLE_HARD_STOP = True         

# ===========================================

# === 全局变量 ===
xt_trader = None
acc = None
stop_flag = False

elite_sell_list = {} 
pos_lock = threading.Lock()

rocket_stage = 0
has_fired_level_1 = False
has_fired_level_2 = False
last_reset_time = 0

order_history = {}
history_lock = threading.Lock()

stop_loss_triggered = {}
stop_loss_lock = threading.Lock()

last_force_save_time = 0
loop_counter = 0
auction_executed_today = False
last_date = ""

def log(msg):
    """格式化日志输出"""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    try:
        print("[{}] {}".format(ts, str(msg)))
        sys.stdout.flush() 
    except Exception:
        pass

def ensure_dirs():
    """确保所有必要目录存在"""
    dirs = [PROCESSED_DIR_INPUT, SIGNAL_DIR_SAFE]
    for d in dirs:
        if not os.path.exists(d):
            try:
                os.makedirs(d)
                log("[初始化] 创建目录：{}".format(d))
            except Exception as e:
                log("[错误] 创建目录失败 {}: {}".format(d, str(e)))

# ========= [核心功能 1] 状态持久化 =========
def save_yesterday_positions():
    """智能保存逻辑：仅将浮盈 > 12% 的股票写入精英名单"""
    global xt_trader, acc, elite_sell_list
    
    if not xt_trader or not acc:
        return

    try:
        positions = xt_trader.query_stock_positions(acc)
        new_elite_list = {}
        
        if positions:
            codes = [p.stock_code for p in positions if p.volume > 0]
            tick_data = {}
            
            if codes:
                try:
                    tick_data = xtdata.get_full_tick(codes) or {}
                except Exception as e:
                    log("[保存] 行情数据异常，使用成本价作为 fallback: " + str(e))
            
            count_selected = 0
            for p in positions:
                if p.volume <= 0: continue
                    
                code = p.stock_code
                cost = getattr(p, 'open_price', 0.0)
                current_price = tick_data.get(code, {}).get('lastPrice', 0.0)
                
                if current_price <= 0: current_price = cost 
                
                if cost > 0:
                    profit_ratio = (current_price - cost) / cost
                    if profit_ratio > ELITE_PROFIT_THRESHOLD:
                        new_elite_list[code] = {
                            'volume': p.volume,
                            'profit_ratio': round(profit_ratio, 4),
                            'close_price': current_price,
                            'cost_price': cost
                        }
                        count_selected += 1
            
            elite_sell_list = new_elite_list
            log("[保存] 扫描 {} 只持仓，{} 只入选精英名单".format(len(codes), count_selected))
        else:
            elite_sell_list = {}

        temp_file = STATE_FILE + ".tmp"
        data_to_save = {
            'update_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
            'positions': elite_sell_list,
            'strategy': 'ELITE_6PCT_AUCTION',
            'threshold': ELITE_PROFIT_THRESHOLD
        }
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        os.rename(temp_file, STATE_FILE)
        
        log("[保存] 文件已更新 (名单数量：{})".format(len(elite_sell_list)))
        
    except Exception as e:
        log("[错误] 保存文件发生严重错误： " + str(e))

def load_yesterday_positions():
    """加载昨晚生成的精英名单"""
    global elite_sell_list
    if not os.path.exists(STATE_FILE):
        elite_sell_list = {}
        log("[初始化] 未找到精英名单文件，初始化为空。")
        return
    
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            elite_sell_list = data.get('positions', {})
        
        if elite_sell_list:
            log("[初始化] 成功加载精英名单：{} 只股票".format(len(elite_sell_list)))
        else:
            log("[初始化] 名单为空")
            
    except Exception as e:
        log("[警告] 加载文件失败，重置为空： " + str(e))
        elite_sell_list = {}

# ========= [核心功能 2] 集合竞价盲卖 =========
def execute_call_auction_sell():
    """执行逻辑：读取精英名单，以现价 95% 挂单卖出"""
    global xt_trader, acc, elite_sell_list
    
    if not xt_trader or not acc or not elite_sell_list:
        return

    log("[竞价] >>> 开始执行 [精英名单] 集合竞价卖出...")
    
    current_positions = xt_trader.query_stock_positions(acc) or []
    current_hold_map = {p.stock_code: p for p in current_positions if p.volume > 0}
    
    sell_count = 0
    codes_to_sell = list(elite_sell_list.keys())
    
    for code in codes_to_sell:
        data = elite_sell_list[code]
        profit_info = data.get('profit_ratio', 0)
        
        if code not in current_hold_map:
            with pos_lock:
                if code in elite_sell_list: del elite_sell_list[code]
            continue
            
        pos = current_hold_map[code]
        if pos.can_use_volume <= 0: continue
            
        tick = xtdata.get_full_tick([code])
        current_price = tick.get(code, {}).get('lastPrice', 0.0)
        if current_price == 0.0: current_price = tick.get(code, {}).get('open', 0.0)
            
        if current_price > 0:
            sell_price = round(current_price * AUCTION_SELL_RATIO, 2)
        else:
            sell_price = data.get('close_price', 0.0)
            
        limit_down = tick.get(code, {}).get('limitDown', 0.0)
        if limit_down > 0 and sell_price < limit_down:
            sell_price = limit_down
            
        try:
            xt_trader.order_stock_async(
                acc, code, xtconstant.STOCK_SELL, 
                pos.can_use_volume, 
                xtconstant.FIX_PRICE, sell_price,
                "ELITE_AUCTION_SELL", 
                "AUTO_" + str(int(time.time()))
            )
            log("[成功] 竞价卖出：{} {} 股 @ {}".format(code, pos.can_use_volume, sell_price))
            sell_count += 1
            
            with pos_lock:
                if code in elite_sell_list: del elite_sell_list[code]
                    
        except Exception as e:
            log("[错误] 竞价卖出失败 {}: {}".format(code, str(e)))
            
    log("[汇总] 竞价阶段结束：成功 {} 单".format(sell_count))

# ========= [核心功能 3] 信号处理与无限加仓 =========

def get_index_change_percent():
    """获取上证指数涨跌幅"""
    index_code = '000001.SH'
    try:
        tick_data = xtdata.get_full_tick([index_code])
        if not tick_data or index_code not in tick_data: return None
        data = tick_data[index_code]
        current_price = data.get('lastPrice', 0.0)
        open_price = data.get('open', 0.0)
        if current_price <= 0 or open_price <= 0: return None
        change_pct = (current_price - open_price) / open_price * 100.0
        if not math.isfinite(change_pct): return None
        return round(change_pct, 2)
    except Exception:
        return None

def check_hard_stop_loss():
    """
    盘中硬止损检查
    [重要修改] 增加了时间判断，仅在 STOP_LOSS_START_TIME 之后执行
    """
    if not ENABLE_HARD_STOP:
        return # 如果开关关闭，直接返回
        
    if not xt_trader or not acc: 
        return
    
    # [新增] 时间检查
    current_time_str = datetime.datetime.now().strftime("%H%M")
    if current_time_str < STOP_LOSS_START_TIME:
        # 如果还没到时间，不执行任何操作，也不打印日志，保持静默
        return
    
    try:
        positions = xt_trader.query_stock_positions(acc) or []
        check_codes = [p.stock_code for p in positions if p.volume > 0 and p.can_use_volume > 0]
        if not check_codes: return
        
        tick_data = xtdata.get_full_tick(check_codes) or {}
        now_time = time.time()
        triggered_count = 0
        
        for code in check_codes:
            pos = next((p for p in positions if p.stock_code == code), None)
            if not pos: continue
            
            cost_price = pos.open_price
            current_price = tick_data.get(code, {}).get('lastPrice', 0.0)
            limit_down = tick_data.get(code, {}).get('limitDown', 0.0)
            
            if current_price <= 0 or cost_price <= 0: continue
            
            loss_ratio = (cost_price - current_price) / cost_price
            if loss_ratio >= STOP_LOSS_RATIO:
                with stop_loss_lock:
                    if code in stop_loss_triggered and now_time - stop_loss_triggered[code] < 300:
                        continue
                
                log("[警报] 触发硬止损：{} 亏损 {:.2f}%! (时间>{})".format(code, loss_ratio*100, STOP_LOSS_START_TIME))
                sell_price = max(limit_down, round(current_price * 0.99, 2)) if limit_down > 0 else round(current_price * 0.99, 2)
                
                try:
                    xt_trader.order_stock_async(acc, code, xtconstant.STOCK_SELL, pos.can_use_volume,
                        xtconstant.FIX_PRICE, sell_price, "HARD_STOP", "EMERGENCY")
                    with stop_loss_lock:
                        stop_loss_triggered[code] = now_time
                    triggered_count += 1
                except Exception as e:
                    log("[错误] 止损报单失败：" + str(e))
                    
        if triggered_count > 0:
            log("[止损] 本轮共触发 {} 笔卖出。".format(triggered_count))
    except Exception as e:
        log("[错误] 止损检查异常：" + str(e))

def calculate_total_floating_profit():
    """计算总浮盈金额"""
    try:
        if not xt_trader or not acc: return 0.0
        positions = xt_trader.query_stock_positions(acc) or []
        codes = [p.stock_code for p in positions if p.volume > 0]
        if not codes: return 0.0
        tick_data = xtdata.get_full_tick(codes) or {}
        total = 0.0
        for p in positions:
            if p.volume <= 0: continue
            price = tick_data.get(p.stock_code, {}).get('lastPrice', 0.0)
            if price > 0:
                total += (price - p.open_price) * p.volume
        return total
    except:
        return 0.0

def execute_rocket_boost(stage):
    """执行火箭加仓逻辑"""
    try:
        if not xt_trader or not acc: return

        positions = xt_trader.query_stock_positions(acc) or []
        valid_positions = [p for p in positions if p.volume > 0]
        if not valid_positions: return

        codes = [p.stock_code for p in valid_positions]
        tick_data = xtdata.get_full_tick(codes) or {}
        asset = xt_trader.query_stock_asset(acc)
        if not asset: return

        log("[火箭] >>> 触发 Stage {} 点火！".format(stage))
        success_count = 0
        
        for p in valid_positions:
            code = p.stock_code
            current_price = tick_data.get(code, {}).get('lastPrice', 0.0)
            if current_price <= 0: continue

            add_vol = p.volume if stage == 1 else int(p.volume / 2)
            add_vol = (add_vol // 100) * 100
            if add_vol < 100: continue

            required_cash = add_vol * current_price
            if required_cash > asset.cash:
                log("[火箭] {}: 现金不足".format(code))
                continue

            order_price = min(tick_data.get(code, {}).get('limitUp', 9999), round(current_price * 1.01, 2))

            try:
                xt_trader.order_stock_async(acc, code, xtconstant.STOCK_BUY, add_vol,
                    xtconstant.FIX_PRICE, order_price, "ROCKET_STAGE_{}".format(stage), "AUTO")
                log("[火箭] [成功] 加仓：{} {} 股 @ {}".format(code, add_vol, order_price))
                success_count += 1
            except Exception as e:
                log("[火箭] [错误] 加仓失败 {}: {}".format(code, str(e)))

        log("[火箭] <<< Stage {} 结束。成功：{}/{}".format(stage, success_count, len(valid_positions)))
    except Exception as e:
        log("[火箭] 顶层异常：{}".format(str(e)))

def check_rocket_reset():
    """检查并重置火箭状态机"""
    global rocket_stage, has_fired_level_1, has_fired_level_2, last_reset_time
    try:
        if not xt_trader or not acc: return
        positions = xt_trader.query_stock_positions(acc) or []
        active_count = len([p for p in positions if p.volume > 0])
        
        if active_count < 8 and rocket_stage != 0:
            if time.time() - last_reset_time > 300:
                log("[火箭复位] 持仓仅剩 {} 支，重置状态机".format(active_count))
                rocket_stage = 0
                has_fired_level_1 = False
                has_fired_level_2 = False
                last_reset_time = time.time()
    except:
        pass

def check_position_and_calculate_volume(code, action, price):
    """仓位计算与校验"""
    try:
        if not xt_trader or not acc:
            return False, 0, "交易接口未就绪"

        positions = xt_trader.query_stock_positions(acc) or []
        current_vol = 0
        has_position = False

        for p in positions:
            if p.stock_code == code:
                current_vol = p.volume
                has_position = True
                break

        if action == "BUY":
            if has_position:
                log(f"[仓位检查] {code} 已持有 {current_vol} 股，执行追加买入")

            asset = xt_trader.query_stock_asset(acc)
            if not asset: return False, 0, "资产查询失败"

            available_cash = asset.cash * 0.98 
            if available_cash < MIN_ORDER_VALUE:
                return False, 0, f"可用现金不足 (剩 {available_cash:.2f})"

            target_cash = available_cash * SINGLE_ORDER_CASH_RATIO
            if FIXED_ORDER_AMOUNT > 0 and target_cash > FIXED_ORDER_AMOUNT:
                target_cash = FIXED_ORDER_AMOUNT
            
            if target_cash < MIN_ORDER_VALUE:
                target_cash = available_cash
                
            raw_vol = target_cash / price
            vol = int(raw_vol // 100) * 100

            if vol < 100:
                if available_cash >= price * 100:
                     vol = 100
                else:
                    return False, 0, f"现金不足以买入 1 手 (需 {price*100:.2f})"

            if vol * price > available_cash:
                vol = int(available_cash / price // 100) * 100
                if vol < 100: return False, 0, "现金极度不足"

            log(f"[仓位计算] {code} 计划买入 {vol} 股 (约 {vol*price:.0f} 元)")
            return True, vol, "允许"
            
        else: # SELL
            pos = next((p for p in positions if p.stock_code == code), None)
            if not pos or pos.can_use_volume <= 0:
                return False, 0, "无可用持仓"
            return True, pos.can_use_volume, "允许"
            
    except Exception as e:
        return False, 0, "计算异常：" + str(e)

def check_repeat_protection(code, action):
    """重复下单保护"""
    key = "{}_{}".format(code, action)
    now = time.time()
    with history_lock:
        if key in order_history:
            elapsed = now - order_history[key]
            if elapsed < REPEAT_PROTECT_SECONDS:
                return False, "保护中 (剩余{}s)".format(int(REPEAT_PROTECT_SECONDS - elapsed))
        order_history[key] = now
        return True, "通过"

def decide_action(action, vr, index_change):
    """
    【核心策略】决策引擎：根据时间、量比(VR)、大盘涨跌决定 买/卖
    返回 True 表示允许操作，False 表示拦截（不执行）
    
    参数:
        action: 信号动作 ("BUY" 或 "SELL")
        vr: 量比 (Volume Ratio)
        index_change: 上证指数涨跌幅 (%)
    """
    
    # 1. 获取当前时间 (格式 HHMM，例如 "0936", "1450")
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M")
    
    # 2. 定义交易时段
    # 上午段：09:36 (开盘后) 到 11:35 (午盘前)
    is_morning = "0935" <= current_time <= "1135"
    # 下午段：13:00 (开盘后) 到 15:00 (收盘前)
    is_afternoon = "1300" <= current_time <= "1500"
    
    # 【时间过滤】如果不是上午或下午的交易时间，直接拒绝所有操作
    if not (is_morning or is_afternoon):
        return False 

    # 3. 处理大盘数据缺失的情况
    # 如果获取不到大盘涨跌幅 (index_change 为 None)
    if index_change is None:
        # 如果是买入信号：为了安全，没有大盘数据禁止买入
        if action == "BUY": 
            return False
        # 如果是卖出信号：默认大盘没动 (0.0)，允许继续判断量比
        index_change = 0.0
    
    # ================= [买入逻辑 BUY] =================
    if action == "BUY":
        # --- 红线规则：大盘暴跌保护 ---
        # 如果大盘跌幅超过 -0.80% (单边大跌)，禁止任何买入 (防止接飞刀)
        if index_change < -0.80: 
            return False 

        # --- 上午买入策略 (09:36 - 11:35) ---
        if is_morning:
            # 条件：大盘平稳 (-0.3% ~ +1.8%) 且 量比非常强劲 (>= 1.8)
            # 解释：早盘波动大，必须要求极高的量比确认主力强势介入
            if -0.55 <= index_change <= 1.8 and vr >= 4.3:
                return True
            # 其他情况一律不买
            return False
            
        # --- 下午买入策略 (13:00 - 15:00) ---
        if is_afternoon:
            # 情况 A：大盘平稳 (-0.3% ~ +1.8%)
            # 条件：量比 >= 1.6 即可 (下午趋势较明，门槛可适当降低)
            if -0.55 <= index_change <= 1.8 and vr >= 4.3: 
                return True
            
            # 情况 B：大盘微跌 (-0.85% ~ -0.3%)
            # 条件：量比 >= 3.0 (需要更强的资金承接确认，防止抄底抄在半山腰)
            if -0.85 <= index_change < -0.55 and vr >= 5.0: 
                return True
            
            # 其他情况 (如大盘大涨>1.8% 怕追高，或量比不够) 一律不买
            return False 

    # ================= [卖出逻辑 SELL] =================
    else: # action == "SELL"
        # --- 上午卖出策略 (09:36 - 11:35) ---
        if is_morning:
            # 正常情况：只要量比 >= 0.6 (有流动性) 就允许卖出
            if vr >= 0.8: 
                return True
            # 特殊情况：即使量比低，如果大盘暴跌 (< -0.80%)，也要强制允许卖出 (止损/逃命)
            if index_change < -0.85 and vr >= 0.6: 
                return True
            return False
                
        # --- 下午卖出策略 (13:00 - 15:00) ---
        if is_afternoon:
            # 正常情况：量比 >= 1.2 允许卖出
            if vr >= 0.8: 
                return True
            # 特殊情况：如果大盘大跌 (< -1.0%)，无条件允许卖出 (不管量比多少，先跑再说)
            # 注意：这里原逻辑是 index_change < -0.5 直接返回 True，哪怕量比很低也能卖
            if index_change < -0.6: 
                return True
            return False

    # 默认返回 False (以防漏网之鱼)
    return False

def process_signal_files():
    """处理信号文件主逻辑 - [含详细调试日志]"""
    global rocket_stage, has_fired_level_1, has_fired_level_2
    
    # --- 火箭逻辑 ---
    total_profit = calculate_total_floating_profit()
    
    if rocket_stage == 0:
        if total_profit >= LEVEL_2_THRESHOLD:
            rocket_stage = 2; has_fired_level_1 = True; has_fired_level_2 = True
        elif total_profit >= LEVEL_1_THRESHOLD:
            rocket_stage = 1; has_fired_level_1 = True
    
    if loop_counter % 10 == 0:
        log("[状态] 阶段:{} | 浮盈:{:.2f}".format(rocket_stage, total_profit))

    if rocket_stage == 0 and not has_fired_level_1 and total_profit >= LEVEL_1_THRESHOLD:
        log("[火箭点火] !!! 触发一级点火")
        execute_rocket_boost(1)
        rocket_stage = 1; has_fired_level_1 = True
        save_yesterday_positions() 

    if rocket_stage == 1 and not has_fired_level_2 and total_profit >= LEVEL_2_THRESHOLD:
        log("[火箭点火] !!! 触发二级点火")
        execute_rocket_boost(2)
        rocket_stage = 2; has_fired_level_2 = True
        save_yesterday_positions()

    check_rocket_reset()
    
    # --- 信号文件处理 ---
    try:
        if not os.path.exists(SIGNAL_DIR_INPUT): return
        files = [f for f in os.listdir(SIGNAL_DIR_INPUT) if f.endswith(".txt")]
    except Exception as e:
        log("[错误] 读取信号目录失败：" + str(e))
        return
    
    if not files: return
    files.sort()
    
    index_change = get_index_change_percent()
    if index_change is not None:
        log("[大盘] 上证指数：{:.2f}%".format(index_change))
    
    processed_any = False
    
    for filename in files:
        path = os.path.join(SIGNAL_DIR_INPUT, filename)
        
        # [防御一] 文件读取重试机制
        content = ""
        read_success = False
        for attempt in range(2):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                read_success = True
                break
            except Exception as e:
                if attempt == 0:
                    time.sleep(0.5)
                    continue
                else:
                    log("[警告] 读取文件失败 (重试后仍失败) {}: {}".format(filename, str(e)))
                    break

        if not read_success or not content:
            continue

        lines = content.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # [防御二] 数据清洗
            if not line.startswith("{"):
                continue
            
            try:
                sig = json.loads(line)
            except Exception as e:
                continue
            
            code = sig.get("code")
            action = sig.get("action")
            price = float(sig.get("price", 0))
            vr = float(sig.get("volume_ratio", 0))
            
            if not code or not action: continue
            
            current_time_str = datetime.datetime.now().strftime("%H%M")
            
            # [调试 1] 时间窗口检查
            if not ("0936" <= current_time_str <= "1135" or "1300" <= current_time_str <= "1500"):
                continue

            # [调试 2] 策略过滤
            if not decide_action(action, vr, index_change):
                continue
            
            # [调试 3] 重复保护
            ok, reason = check_repeat_protection(code, action)
            if not ok:
                log(f"[拦截] 重复保护拦截: {code} {action}, 原因: {reason}")
                continue
            
            # [调试 4] 仓位/资金检查
            allow, vol, reason = check_position_and_calculate_volume(code, action, price)
            if not allow:
                log(f"[拦截] 仓位/资金计算失败: {code} {action}, 原因: {reason}")
                continue
            
            # --- 执行下单 ---
            order_type = xtconstant.STOCK_BUY if action == "BUY" else xtconstant.STOCK_SELL
            order_price = round(price * (1.01 if action == "BUY" else 0.99), 2)
            
            try:
                xt_trader.order_stock_async(acc, code, order_type, vol,
                    xtconstant.FIX_PRICE, order_price, "AlphaPilot_V8.5_DelayedStop", "AUTO")
                log("[成功] >>> 下单：{} {} {} 股 @ {}".format(code, action, vol, order_price))
                processed_any = True
            except Exception as e:
                log("[错误] 下单失败：" + str(e))
        
        # [防御三] 归档安全确认
        if os.path.exists(path):
            try:
                dest = os.path.join(PROCESSED_DIR_INPUT, filename)
                shutil.move(path, dest)
                
                if os.path.exists(path):
                    log("[严重] 文件移动疑似失败，强制重命名备份...")
                    backup_name = path + ".error_backup_" + str(int(time.time()))
                    os.rename(path, backup_name)
                else:
                    log("[归档] 文件已成功移入处理目录：{}".format(filename))
            except Exception as e:
                log("[错误] 归档失败：" + str(e))
                try:
                    error_name = path + ".processing_error"
                    os.rename(path, error_name)
                except:
                    pass

# ========= [主循环调度] =========
def process_logic_loop():
    global loop_counter, auction_executed_today, last_date, last_force_save_time
    
    now = datetime.datetime.now()
    current_time_str = now.strftime("%H%M")
    today_str = now.strftime("%Y%m%d")
    
    if today_str != last_date:
        last_date = today_str
        auction_executed_today = False
        load_yesterday_positions()
        log("[日期] 新交易日：{}, 精英名单已加载".format(today_str))

    try:
        loop_counter += 1
        
        # 2. 硬止损巡检
        # 逻辑已移至 check_hard_stop_loss 内部判断时间，这里保持调用即可
        if loop_counter % STOP_LOSS_CHECK_INTERVAL == 0:
            # 只要过了 09:36 就可以调用检查函数，函数内部会判断是否到了 09:45
            if "0936" <= current_time_str <= "1500":
                check_hard_stop_loss()

        # 3. 集合竞价模式
        if "0921" <= current_time_str <= "0925":
            if not auction_executed_today:
                log("[模式] 进入集合竞价时段，执行精英卖出...")
                execute_call_auction_sell()
                auction_executed_today = True
            return 

        # 4. 静默期
        if "0925" < current_time_str < "0936":
            return

        # 5. 连续竞价模式
        if current_time_str >= "0936":
            process_signal_files()
            
        # 6. 强制保存机制
        current_ts = time.time()
        if (loop_counter == 2) or (current_ts - last_force_save_time > 600):
            save_yesterday_positions()
            last_force_save_time = current_ts

    except Exception as e:
        log("[错误] 主循环异常： " + str(e))
        import traceback
        traceback.print_exc()

def monitor_thread_func():
    while not stop_flag:
        process_logic_loop()
        time.sleep(3)
    
    log("[关闭] 监控停止，执行最终保存...")
    save_yesterday_positions()

class MyCallback(XtQuantTraderCallback):
    def on_connected(self): log("[成功] QMT 交易服务连接成功")
    def on_disconnected(self): log("[错误] QMT 交易服务断开连接")
    def on_stock_order(self, order): pass
    def on_stock_trade(self, trade): log("[成交] 已执行：{} {} {} 股".format(trade.stock_code, trade.order_type, trade.volume))
    def on_order_error(self, order_error): log("[错误] 委托错误：{} - {}".format(order_error.stock_code, order_error.error_msg))

if __name__ == "__main__":
    log("=" * 60)
    log("启动 AlphaPilot V8.5-DelayedStop (延迟止损版)") 
    if ENABLE_HARD_STOP:
        log(f"[风控] 硬止损已开启，执行时间：{STOP_LOSS_START_TIME} 后")
    else:
        log("[风控] 硬止损已完全关闭")
    log("=" * 60)
    try:
        ensure_dirs()
        
        session_id = int(time.time())
        xt_trader = XtQuantTrader(QMT_PATH, session_id)
        cb = MyCallback()
        xt_trader.register_callback(cb)
        xt_trader.start()
        
        log("[初始化] 正在连接 QMT...")
        if xt_trader.connect() != 0:
            log("[错误] 连接 QMT 失败")
            raise SystemExit
            
        time.sleep(2)
        
        acc = StockAccount(ACCOUNT_ID, "STOCK")
        if xt_trader.subscribe(acc) != 0:
            log("[错误] 订阅账户失败")
            raise SystemExit
            
        log("[初始化] 账户订阅成功：{}".format(ACCOUNT_ID))
        
        t = threading.Thread(target=monitor_thread_func, daemon=True)
        t.start()
        
        log("[信息] 系统运行中... 等待信号...")
        
        xt_trader.run_forever()
        
    except KeyboardInterrupt:
        stop_flag = True
        log("[停止] 用户手动中断")
    except Exception as e:
        log("[错误] 发生严重异常： " + str(e))
    finally:
        if xt_trader:
            save_yesterday_positions()
            xt_trader.stop()
            log("[结束] 程序完全停止")