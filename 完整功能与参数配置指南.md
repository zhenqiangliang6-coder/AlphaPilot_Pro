# AlphaPilot Pro 完整功能与参数配置指南

> **最后更新**：2026-04-06  
> **适用版本**：V8.5 实战版  
> **运行环境**：阿里云 ECS + QMT 交易终端

---

## 👥 开发团队

**Alphapilot智能体团队**

### 团队成员
- **梁子羿** - 广东外语外贸大学数字运营系人工智能
- **侯沣睿** - 惠州城市职业学院大数据筛选  
- **梁茹真** - 北京工商大学

### 联系方式
- 📧 邮箱：497720537@qq.com
- 📱 电话：13392077558

---

## 📋 目录

1. [快速参数修改指南](#1-快速参数修改指南)
2. [各策略功能详解](#2-各策略功能详解)
3. [配置文件位置与修改方法](#3-配置文件位置与修改方法)
4. [常见问题速查](#4-常见问题速查)

---

## 1. 快速参数修改指南

### 🔥 最常用的参数修改位置

| 要修改的内容 | 文件路径 | 参数名称 | 默认值 | 说明 |
|------------|---------|---------|--------|------|
| **买入量比门槛** | `strategies/signal_strategy.py` | `_decide_action()` 方法 | VR ≥ 1.8 | 第 148 行 |
| **卖出席比门槛** | `strategies/signal_strategy.py` | `_decide_action()` 方法 | VR ≥ 2.0 | 第 158 行 |
| **止损比例** | `config/settings.py` | `STOP_LOSS_RATIO` | 0.08 (8%) | 第 51 行 |
| **单次买入金额上限** | `strategies/signal_strategy.py` | `FIXED_ORDER_AMOUNT` | 50000 | 第 181 行 |
| **最小下单金额** | `strategies/signal_strategy.py` | `MIN_ORDER_VALUE` | 15000 | 第 184 行 |
| **延时策略量比** | `data/stock_personalities.json` | `min_volume_ratio` | 18.0 | 按股票配置 |
| **延时天数** | `data/stock_personalities.json` | `delay_days` | 1 | 按股票配置 |
| **目标日量比门槛** | `data/stock_personalities.json` | `target_day_min_vr` | 0.2 | 按股票配置 |
| **保底买入时间** | `strategies/delayed_strategy.py` | `check_and_execute()` | 14:39 | 约第 175 行 |

---

### 📝 详细修改步骤

#### ① 修改即时买入/卖出席比（signal_strategy.py）

**文件位置**：`C:\迅投QMT交易终端 华林证券模拟版\mpython\strategies\signal_strategy.py`

**修改位置**：第 124-134 行

```
def _decide_action(self, action, vr, index_change):
    if index_change is None:
        if action == "BUY": return False
        index_change = 0.0
    
    if action == "BUY":
        # 正常行情：量比 ≥ 1.8
        if -0.12 <= index_change <= 1.8 and vr >= 1.8: return True  # ← 修改这里
        # 下跌行情：量比 ≥ 3.5
        if -1.8 <= index_change < -0.12 and vr >= 3.5: return True  # ← 修改这里
        return False
    else:  # SELL
        # 正常行情：量比 ≥ 2.0
        if -0.12 <= index_change <= 1.8 and vr >= 2.0: return True  # ← 修改这里
        # 下跌行情：量比 ≥ 1.6
        if -1.8 <= index_change < -0.12 and vr >= 1.6: return True  # ← 修改这里
        return False
```

**修改方法**：
1. 用记事本打开文件
2. 找到第 124-134 行
3. 修改 `vr >= 1.8` 中的 `1.8` 为你想要的值
4. 保存文件，**无需重启程序**（热更新）

---

#### ② 修改止损参数（settings.py）

**文件位置**：`D:\AlphaPilot_Pro\config\settings.py`

**修改位置**：第 48-53 行

```python
# --- [风控策略] ---
STOP_LOSS_RATIO = 0.08          # 硬止损阈值（-8%）← 修改这里，如改为 0.10 就是 10%
STOP_LOSS_CHECK_INTERVAL = 5    # 止损检查频率（每 5 秒）
STOP_LOSS_START_TIME = "1045"   # 硬止损开始执行时间（10:45 后）
ENABLE_HARD_STOP = True         # 硬止损开关（改为 False 可关闭）
```

**修改方法**：
1. 打开 `settings.py`
2. 修改对应参数的值
3. 保存文件，**重启程序生效**

---

#### ③ 修改延时策略参数（stock_personalities.json）

**文件位置**：`D:\AlphaPilot_Pro\data\stock_personalities.json`

**示例配置**：
```
{
    "603538.SH": {
        "name": "美诺华",
        "type": "delayed",
        "delay_days": 1,
        "min_volume_ratio": 18.0,
        "target_day_min_vr": 0.2,
        "super_high_volume_ratio": 30.0,
        "note": "经典慢涨股，信号后 1 天涨停"
    },
    "300626.SZ": {
        "name": "华测导航",
        "type": "delayed",
        "delay_days": 6,
        "min_volume_ratio": 5.16,
        "target_day_min_vr": 0.2,
        "note": "涨停前 6 天量比最大信号触发（量比=5.16）"
    },
    "000001.SZ": {
        "name": "平安银行",
        "type": "delayed",
        "delay_days": 3,
        "min_volume_ratio": 20.0,
        "target_day_min_vr": 0.2,
        "super_high_volume_ratio": 30.0,
        "note": "稳健型慢涨股"
    },
    "default": {
        "type": "immediate",
        "min_volume_ratio": 1.5
    }
}
```

**参数说明**：
- `type`: "delayed" = 延时策略，"immediate" = 即时买入
- `delay_days`: 等待天数（自然日，跳过周末）
- `min_volume_ratio`: 等待期量比门槛（建议 18.0-25.0）
- `target_day_min_vr`: 目标日量比门槛（建议 0.2，抓最低点）
- `super_high_volume_ratio`: 提前触发量比门槛（建议 30.0，防止假突破）

**修改方法**：
1. 打开 JSON 文件
2. 添加或修改股票配置
3. 保存文件，**无需重启**（自动热更新）

---

## 2. 各策略功能详解

### 🎯 策略 1：信号策略（Signal Strategy）

**作用**：处理即时信号，根据大盘和量比智能过滤

**工作流程**：
1. 从 `C:\Users\Administrator\Desktop\ESC\signals\` 读取信号文件
2. 判断大盘涨跌幅
3. 根据量比决定是否买入/卖出
4. 计算仓位并下单
5. 归档已处理信号

**关键参数**：

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| 买入量比（正常） | signal_strategy.py | 1.8 | 大盘平稳时的买入门槛 |
| 买入量比（下跌） | signal_strategy.py | 3.5 | 大盘下跌时的高门槛 |
| 卖出席比（正常） | signal_strategy.py | 2.0 | 大盘平稳时的卖出门槛 |
| 卖出席比（下跌） | signal_strategy.py | 1.6 | 大盘下跌时的低门槛 |
| 重复保护时间 | settings.py | 540秒 | 同一股票9分钟内不重复下单 |

**日志标识**：`[信号分流]`、`[过滤]`、`[仓位]`、`[归档]`

---

### ⏰ 策略 2：延时策略（Delayed Strategy）⭐

**作用**：捕捉慢涨股，过滤假突破

**工作流程**：
1. 信号到达 → 检查是否为"delayed"类型股票
2. 量比达标 → 加入观察名单
3. 等待 N 天（自然日） → 期间监听超强信号
4. 到达目标日 → 使用实时价格买入
5. 买入成功 → 从观察名单移除

**关键参数**：

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| 延时天数 | stock_personalities.json | 1 | 等待天数（自然日） |
| 等待期量比 | stock_personalities.json | 18.0 | 加入观察的门槛 |
| 提前触发量比 | stock_personalities.json | 30.0 | 等待期超强信号门槛（防假突破） |
| 目标日量比 | stock_personalities.json | 0.2 | 目标日最低门槛（抓最低点） |
| 保底买入时间 | delayed_strategy.py | 14:39 | 目标日 14:39 后必须买入 |

**策略逻辑详解**：

#### 1️⃣ 等待期内（未到期）
- ❌ **坚决不买入**（防止提前买入到高点）
- ✅ 只有量比 >= 30.0 的超强信号才提前触发
- 📊 目的：`super_high_volume_ratio = 30.0` 设置极高，就是为了防止提前买入

#### 2️⃣ 到期日当天 - 两种买入路径

**路径 A：信号优先（抓最低点）**
```
到期日当天
    ↓
出现新信号且量比 >= target_day_min_vr (0.2)
    ↓
立即买入（捕捉当日最低点）✅
```

**路径 B：保底机制（防止踏空）**
```
到期日当天 14:39
    ↓
无论有无信号、无论量比多少
    ↓
必须买入（保底执行）✅
```

**修改保底时间的方法**：
1. 打开 `strategies/delayed_strategy.py`
2. 找到 [check_and_execute()](file://d:\AlphaPilot_Pro\strategies\delayed_strategy.py#L146-L200) 方法（约第 175 行）
3. 修改 `if now_time < "1439":` 中的时间
   - 改为 `11:15` → `if now_time < "1115":`
   - 改为 `14:39` → `if now_time < "1439":`
4. 保存文件，同步到 ECS，重启程序

**修改目标日量比门槛的方法**：
1. 打开 `data/stock_personalities.json`
2. 找到对应股票，修改 `target_day_min_vr` 值
   - 例如：`"target_day_min_vr": 0.2` 改为 `0.5`（更严格）
   - 或改为 `0.1`（更宽松）
3. 保存文件，**立即生效**（热更新）

**日志标识**：`[延时过滤]`、`[延时策略]`、`[信号分流]`

**状态文件**：`data/delayed_watchlist.json`（系统自动维护）

---

### 🚀 策略 3：火箭加仓策略（Rocket Boost）

**作用**：盈利达标后自动加仓，放大收益

**工作流程**：
1. 计算所有持仓总浮盈
2. 浮盈 ≥ 9000 元 → 一级点火（加仓 1 只）
3. 浮盈 ≥ 18000 元 → 二级点火（加仓 2 只）
4. 选择浮盈最高的股票加仓 50% 仓位

**关键参数**：

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| 一级触发阈值 | settings.py | 9000 | 浮盈达到 9000 元触发 |
| 二级触发阈值 | settings.py | 18000 | 浮盈达到 18000 元触发 |
| 加仓比例 | rocket_boost.py | 50% | 原持仓的 50% |
| 重复保护 | settings.py | 540秒 | 9 分钟内不重复加仓 |

**日志标识**：`[火箭]`

---

### 🛡️ 策略 4：硬止损策略（Stop Loss）

**作用**：自动控制亏损，防止深度套牢

**工作流程**：
1. 每 5 秒检查一次持仓
2. 10:45 后开始执行
3. 亏损 ≥ 8% → 自动卖出
4. 跌停保护：不低于跌停价

**关键参数**：

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| 止损比例 | settings.py | 0.08 (8%) | 亏损 8% 触发 |
| 检查频率 | settings.py | 5秒 | 每 5 秒检查一次 |
| 开始时间 | settings.py | "1045" | 10:45 后执行 |
| 止损开关 | settings.py | True | False 可关闭 |

**日志标识**：`[止损]`

---

### 💰 策略 5：集合竞价策略（Auction Strategy）

**作用**：早盘竞价卖出精英名单股票

**执行时间**：09:15-09:25

**工作流程**：
1. 读取精英名单（浮盈 > 13% 的持仓）
2. 获取最新价格
3. 以 95% 价格卖出
4. 跌停保护

**关键参数**：

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| 精英筛选阈值 | settings.py | 0.13 (13%) | 浮盈 >13% 入选 |
| 竞价卖出系数 | settings.py | 0.95 | 以 95% 价格卖出 |

**日志标识**：`[竞价]`

---

## 3. 配置文件位置与修改方法

### 📁 核心配置文件清单

| 文件 | 路径 | 用途 | 修改后是否需要重启 |
|------|------|------|------------------|
| **settings.py** | `config/settings.py` | 全局参数配置 | ✅ 需要重启 |
| **stock_personalities.json** | `data/stock_personalities.json` | 个股交易性格 | ❌ 自动热更新 |
| **delayed_watchlist.json** | `data/delayed_watchlist.json` | 延时观察名单 | ❌ 系统维护，勿手动改 |
| **yesterday_holdings.json** | 项目根目录 | 精英名单 | ❌ 系统维护 |

---

### 🔧 settings.py 完整参数说明

**文件位置**：`D:\AlphaPilot_Pro\config\settings.py`

```
# ================= 策略参数配置 =================

# --- [精英名单策略] ---
ELITE_PROFIT_THRESHOLD = 0.13  # 精英筛选阈值（浮盈 >13%）
AUCTION_SELL_RATIO = 0.95      # 竞价卖出报价系数（现价 95%）

# --- [火箭加仓策略] ---
LEVEL_1_THRESHOLD = 9000.0     # 一级火箭触发阈值（浮盈 9000）
LEVEL_2_THRESHOLD = 18000.0    # 二级火箭触发阈值（浮盈 18000）
REPEAT_PROTECT_SECONDS = 540   # 重复下单保护时间（9 分钟）
MIN_ORDER_VALUE = 15000        # 最小下单金额

# --- [资金策略] ---
SINGLE_ORDER_CASH_RATIO = 0.8   # 每次买入可用现金比例（80%）
FIXED_ORDER_AMOUNT = 50000.0    # 单次买入金额上限（5 万元）

# --- [仓位管理] ---
INITIAL_CAPITAL_RATIO = 0.5     # 初始仓位比例（50% 总资金）
MAX_STOCK_COUNT = 20            # 最大持仓股票数量

# --- [风控策略] ---
STOP_LOSS_RATIO = 0.08          # 硬止损阈值（-8%）
STOP_LOSS_CHECK_INTERVAL = 5    # 止损检查频率（每 5 秒）
STOP_LOSS_START_TIME = "1045"   # 硬止损开始执行时间（10:45 后）
ENABLE_HARD_STOP = True         # 硬止损开关

# --- [基础参数] ---
HEARTBEAT_INTERVAL = 3          # 主循环心跳间隔（秒）
DELAYED_STRATEGY_CHECK_INTERVAL = 3  # 延时策略检查间隔（秒）
```

---

### 📊 stock_personalities.json 配置模板

**文件位置**：`C:\迅投QMT交易终端 华林证券模拟版\mpython\data\stock_personalities.json`

```
{
    "603538.SH": {
        "name": "美诺华",
        "type": "delayed",
        "delay_days": 1,
        "min_volume_ratio": 18.0,
        "super_high_volume_ratio": 25.0,
        "note": "经典慢涨股"
    },
    "000858.SZ": {
        "name": "五粮液",
        "type": "immediate",
        "min_volume_ratio": 1.5,
        "note": "即时买入型"
    },
    "default": {
        "type": "immediate",
        "min_volume_ratio": 1.5
    }
}
```

**配置规则**：
- 股票代码格式：`603538.SH` 或 `000858.SZ`
- `type` 必须是 "delayed" 或 "immediate"
- `default` 配置适用于未单独配置的股票
- 修改后**立即生效**，无需重启

---

## 4. 常见问题速查

### ❓ 如何修改买入量比？

**答**：打开 `strategies/signal_strategy.py`，找到第 124-134 行的 `_decide_action()` 方法，修改 `vr >= 1.8` 中的数字即可。

---

### ❓ 如何修改延时策略的等待天数？

**答**：打开 `data/stock_personalities.json`，找到对应股票，修改 `delay_days` 的值。保存后**立即生效**。

---

### ❓ 如何修改到期日保底买入时间（如改为 11:15）？

**答**：
1. 打开 `strategies/delayed_strategy.py`
2. 找到 [check_and_execute()](file://d:\AlphaPilot_Pro\strategies\delayed_strategy.py#L146-L200) 方法（约第 175 行）
3. 找到代码：`if now_time < "1439":`
4. 修改时间：
   - 改为 `11:15` → `if now_time < "1115":`
   - 改为 `14:00` → `if now_time < "1400":`
5. 保存文件，同步到 ECS，**重启程序生效**

---

### ❓ 如何修改目标日量比门槛？

**答**：
1. 打开 `data/stock_personalities.json`
2. 找到对应股票，修改 `target_day_min_vr` 的值
   - 例如：`"target_day_min_vr": 0.2` 改为 `0.5`（更严格，只在量比更高时买入）
   - 或改为 `0.1`（更宽松）
3. 保存文件，**立即生效**（热更新）

**注意**：如果某只股票没有配置 `target_day_min_vr`，会使用默认值 0.2

---

### ❓ 如何关闭止损功能？

**答**：打开 `config/settings.py`，将 `ENABLE_HARD_STOP = True` 改为 `False`，保存后**重启程序**。

---

### ❓ 延时策略没有生效怎么办？

**检查清单**：
1. ✅ 股票是否在 `stock_personalities.json` 中配置了 `type: "delayed"`？
2. ✅ 信号量比是否达到 `min_volume_ratio` 要求？
3. ✅ 日志中是否有 `[延时过滤]` 或 `[延时策略]` 输出？
4. ✅ 信号文件是否正确放在 `signals` 目录？

---

### ❓ 如何查看当前观察名单？

**答**：打开 `data/delayed_watchlist.json` 文件，里面记录了所有正在观察的股票。

---

### ❓ 日志在哪里查看？

**答**：日志文件位置：
```
C:\Users\Administrator\Desktop\AlphaPilot_Cloud\logs\run_2026-04-06.log
```

也可以在 QMT 界面直接查看"策略日志"标签页。

---

### ❓ 修改配置后不生效？

**可能原因**：
1. 文件未保存到正确位置（检查路径）
2. JSON 格式错误（检查逗号、引号）
3. 部分参数需要重启程序（如 settings.py）
4. 代码未同步到 ECS（检查远程文件是否更新）

---

### ❓ 如何测试策略是否正常工作？

**方法**：在信号目录创建测试文件
```
C:\Users\Administrator\Desktop\ESC\signals\test.txt
```

内容：
```json
{"code": "603538.SH", "action": "BUY", "price": 50.0, "volume_ratio": 20.0}
```

观察日志是否出现：
```
[延时过滤] 603538.SH 量比达标
[延时策略] 603538.SH 已加入观察名单
```

---

## 📞 技术支持

如遇到问题，请提供以下信息：
1. 错误日志截图
2. 修改的配置文件内容
3. 问题发生的时间点

---

**文档版本**：V1.1  
**更新日期**：2026-04-06  
**维护者**：AlphaPilot 开发团队

**更新日志**：
- V1.1 (2026-04-06)：
  - ✅ 添加到期日保底买入时间配置说明（14:39）
  - ✅ 添加目标日量比门槛使用说明（target_day_min_vr）
  - ✅ 完善延时策略两种买入路径说明（信号优先 + 保底机制）
  - ✅ 更新参数修改位置行号
- V1.0 (2026-04-06)：初始版本
