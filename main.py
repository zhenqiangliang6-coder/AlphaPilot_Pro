# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 主程序入口
基于QMT交易终端的模块化量化交易策略系统

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: V8.95 保守版
"""

import os
import sys

# 【环境修复】自动添加 QMT xtquant 库路径，解决睿智融科版调用系统 Python 导致的导入错误
QMT_LIB_PATH = r"D:\迅投极速交易终端 睿智融科版\bin.x64\Lib\site-packages"
if QMT_LIB_PATH not in sys.path and os.path.exists(QMT_LIB_PATH):
    sys.path.insert(0, QMT_LIB_PATH)

import time
import datetime
import threading
import gc  # 新增：用于定期内存清理
import traceback  # 新增：用于异常追踪

# 【专家级修复】强制切换工作目录到脚本所在目录
# 防止 QMT 以不同根目录启动导致相对路径失效
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from utils.logger import init_logger, get_logger
from utils.helpers import (
    ensure_dirs, is_auction_time, is_silent_time, is_trading_time,
    get_index_change_percent, is_after_take_profit_start  # 新增导入
)
from core.trader_engine import TraderEngine
from core.state_manager import StateManager
from strategies.auction_strategy import AuctionStrategy
from strategies.signal_strategy import SignalStrategy
from strategies.rocket_boost import RocketBoost
from strategies.delayed_strategy import DelayedStrategy  # 新增：延时策略
from risk.stop_loss import StopLossMonitor
from risk.dynamic_take_profit import DynamicTakeProfit  # 新增：动态止盈模块

log = None

def main_loop():
    global log
    
    # 初始化
    init_logger(settings.LOG_DIR)
    log = get_logger()
    ensure_dirs()
    
    log.log("="*60)
    log.log("启动 AlphaPilot Pro (模块化版本)")
    log.log("="*60)
    
    engine = TraderEngine()
    if not engine.start(int(time.time())):
        log.log("[致命] 引擎启动失败，退出")
        return

    state_mgr = StateManager(engine)
    auction_strat = AuctionStrategy(engine, state_mgr)
    signal_strat = SignalStrategy(engine)
    rocket_strat = RocketBoost(engine)
    delayed_strat = DelayedStrategy(engine)  # 新增：延时策略实例
    stop_loss_mon = StopLossMonitor(engine)
    take_profit_mon = DynamicTakeProfit(engine)  # 新增：动态止盈模块
    
    # 【新增】建立策略关联：让信号策略知道延时策略的存在
    signal_strat.set_delayed_strategy(delayed_strat)
    
    # 加载昨日状态
    state_mgr.load_elite_list()
    
    loop_counter = 0
    last_date = ""
    last_index_log_time = 0      # 拆分：大盘日志时间戳
    last_state_save_time = 0     # 拆分：状态保存时间戳
    last_gc_time = time.time()   # 新增：GC 执行时间戳
    
    while True:
        try:
            now = datetime.datetime.now()
            time_str = now.strftime("%H%M")
            today_str = now.strftime("%Y%m%d")
            
            # 日期切换
            if today_str != last_date:
                last_date = today_str
                auction_strat.reset_daily()
                state_mgr.load_elite_list()
                log.log("[日期] 新交易日：" + str(today_str))
            
            loop_counter += 1
            current_ts = time.time()

            # 1. 大盘日志（每30秒）
            if current_ts - last_index_log_time > 30:
                index_change = get_index_change_percent()
                if index_change is not None:
                    log.log("[大盘] 上证指数：{}%".format(index_change))
                last_index_log_time = current_ts

            # 2. 止损检查
            if loop_counter % settings.STOP_LOSS_CHECK_INTERVAL == 0:
                stop_loss_mon.check()

            # 3. 动态止盈检查（仅在 09:50 后执行，防止开盘波动误触发）
            if loop_counter % 10 == 0 and is_after_take_profit_start(time_str):
                take_profit_mon.check()

            # 4. 策略执行
            if is_auction_time(time_str):
                auction_strat.execute()
            elif is_silent_time(time_str):
                pass
            elif is_trading_time(time_str):
                delayed_strat.check_and_execute()
                signal_strat.process_files()
                delayed_strat.process_recent_signals()
                rocket_strat.check_and_fire()

            # 5. 状态保存（首次运行 + 每10分钟）
            if loop_counter == 2 or (current_ts - last_state_save_time > 600):
                state_mgr.save_elite_list()
                last_state_save_time = current_ts

            # 6. 内存回收（每50分钟执行一次，防止 QMT 接口假死）
            if current_ts - last_gc_time > 50 * 60:
                gc.collect()
                last_gc_time = current_ts
                log.log("[维护] 已执行强制垃圾回收")

            time.sleep(settings.HEARTBEAT_INTERVAL)
            
        except KeyboardInterrupt:
            log.log("[停止] 用户中断")
            break
        except Exception as e:
            log.log("[错误] 主循环异常：" + str(e))
            log.log(traceback.format_exc())
            time.sleep(5)
    
    # 清理
    state_mgr.save_elite_list()
    engine.stop()
    log.log("[结束] 程序完全停止")

if __name__ == "__main__":
    main_loop()
