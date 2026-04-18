# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 核心配置文件
包含止损阈值、账户ID、QMT路径等关键配置

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: V8.95 保守版
"""

import os
import datetime

# ================= 基础路径配置 =================

# 1. QMT 终端路径 (连接接口用)
# 【重要】新环境：睿智融科版，Python解释器位于 bin.x64 目录
QMT_PATH = r"D:\迅投极速交易终端 睿智融科版\userdata_mini"
ACCOUNT_ID = "13392077558"

# 2. 项目代码根目录 (自动获取，位于 mpython 或项目目录下)
# 当前文件路径：D:\...\AlphaPilot_Pro\config\settings.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# CURRENT_DIR = D:\...\AlphaPilot_Pro\config
BASE_DIR_CODE = os.path.dirname(CURRENT_DIR)
# BASE_DIR_CODE = D:\...\AlphaPilot_Pro （项目根目录）

# ================= [路径架构] - 按你的要求定义 =================

# --- A. 信号输入区 (位于项目根目录 signals 文件夹) ---
# 【重要】监听脚本会将信号文件保存到此目录
SIGNAL_DIR_INPUT = os.path.join(BASE_DIR_CODE, "signals")
# 归档目录自动设在信号目录下的 processed 子文件夹
SIGNAL_DIR_PROCESSED = os.path.join(SIGNAL_DIR_INPUT, "processed")

# --- B. 核心安全区 (位于项目根目录，存储状态和日志) ---
BASE_DIR_SAFE = BASE_DIR_CODE
# 状态文件 (精英名单) 存放在这里
STATE_FILE = os.path.join(BASE_DIR_SAFE, "yesterday_holdings.json")

# 日志文件也建议存放在安全区，方便查看，不占用代码目录
LOG_DIR = os.path.join(BASE_DIR_SAFE, "logs")

# 代码目录内部的数据目录（用于存储延时策略等数据）
DATA_DIR = os.path.join(BASE_DIR_CODE, "data") 

# ================= 策略参数配置 (V8.5 实战版) =================

# --- [精英名单策略] ---
ELITE_PROFIT_THRESHOLD = 0.13  # 精英筛选阈值（浮盈 >13%）
AUCTION_SELL_RATIO = 0.95      # 竞价卖出报价系数（现价 95%）

# --- [无限加仓策略] ---
LEVEL_1_THRESHOLD = 80000.0     # 一级火箭触发阈值（浮盈 9000）
LEVEL_2_THRESHOLD = 160000.0    # 二级火箭触发阈值（浮盈 18000）
REPEAT_PROTECT_SECONDS = 540   # 重复下单保护时间（9 分钟）
MIN_ORDER_VALUE = 15000        # 最小下单金额

# --- [资金策略 - V8.5 核心] ---
SINGLE_ORDER_CASH_RATIO = 0.8   # 每次买入可用现金比例（80%）
FIXED_ORDER_AMOUNT = 50000.0    # 单次买入金额上限（5 万元）

# --- [仓位管理] ---
INITIAL_CAPITAL_RATIO = 0.5     # 初始仓位比例（50% 总资金）
MAX_STOCK_COUNT = 20            # 最大持仓股票数量

# --- [风控策略] ---
# 【动态止损参数 - V8.95 保守版】
STOP_LOSS_MONITOR_THRESHOLD = 0.008     # 止损监控触发阈值（-0.8%开始监控）
STOP_LOSS_LEVEL1_THRESHOLD = 0.017      # 一级止损阈值（-1.7%减半仓）
STOP_LOSS_LEVEL2_THRESHOLD = 0.035      # 二级止损阈值（-3.5%清仓）
STOP_LOSS_CHECK_INTERVAL = 5            # 止损检查频率（每 5 秒）
STOP_LOSS_START_TIME = "1045"           # 硬止损开始执行时间（10:45 后）
STOP_LOSS_END_TIME = "1450"             # 硬止损结束执行时间（14:50 前），避开尾盘集合竞价
ENABLE_HARD_STOP = True                 # 硬止损开关
EARLIEST_EXECUTION_TIME = 952           # 动态止盈最早执行时间（09:52），避开开盘剧烈波动

# --- [基础参数] ---
HEARTBEAT_INTERVAL = 3          # 主循环心跳间隔（秒）

# ================= 延时策略参数 =================
# 延时策略检查间隔（秒），与主循环同步
DELAYED_STRATEGY_CHECK_INTERVAL = 3
