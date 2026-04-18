# AlphaPilot Pro - QMT 最终实战总结与部署指南

**文档日期：** 2026-04-14  
**项目名称：** AlphaPilot Pro（模块化量化交易策略系统）  
**运行环境：** QMT 内置 Python + 极简模式客户端  
**项目路径：** `D:\迅投QMT交易终端 华林证券模拟版\mpython`  
**文档状态：** ✅ 生产级稳定版（已适配本地路径 + 延时策略防延期修复）

---

## 🚀 核心架构与运行模式

### 1. 独立进程运行模式（彻底解决假死）
*   **原理**：将策略主循环（`while True`）移出 QMT 策略编辑器，通过命令行调用 QMT 自带的 Python 解释器独立运行。
*   **优势**：避免阻塞 QMT 单线程事件驱动模型，确保行情订阅不中断、界面不卡死。
*   **依赖**：必须保持 QMT 极简模式客户端登录在线，以提供交易通道（`userdata_mini`）。

### 2. 模块化结构
*   **主入口**：[`main.py`](file://d:\迅投QMT交易终端%20华林证券模拟版\mpython\main.py) - 负责心跳调度、内存回收、状态持久化。
*   **配置中心**：[`config/settings.py`](file://d:\迅投QMT交易终端%20华林证券模拟版\mpython\config\settings.py) - 统一管理路径、阈值及时间窗口。
*   **工具库**：[`utils/helpers.py`](file://d:\迅投QMT交易终端%20华林证券模拟版\mpython\utils\helpers.py) - 包含大盘数据获取（带保活逻辑）及时间判断。

---

## 🛠️ 最新稳定性优化 (2026-04-14)

| 优化项 | 实施细节 | 解决的问题 |
| :--- | :--- | :--- |
| **延时策略防重入** | 在 [`process_signal`](file://d:\迅投QMT交易终端%20华林证券模拟版\mpython\strategies\delayed_strategy.py#L100-L185) 中增加目标日状态检查 | 防止同一股票在目标日当天收到重复信号时自动延期 |
| **原始触发门槛** | 在 [`check_and_execute`](file://d:\迅投QMT交易终端%20华林证券模拟版\mpython\strategies\delayed_strategy.py#L196-L293) 中使用 `trigger_volume_ratio` | 确保使用加入名单时的个性化量比门槛，而非固定阈值 |
| **无条件清理机制** | 目标日当天无论买入成功与否，均从观察名单移除 | 彻底杜绝因买入失败导致的"自动更新日期"死循环 |
| **决策终态原则** | 目标日必须完成决策（买入或放弃），严禁顺延 | 防止错失最佳买点，避免优质信号被浪费 |

### 🔧 延时策略核心修复说明

**问题背景：**
- 原逻辑在目标日当天如果量比达标会执行买入，但如果买入失败或未成交，股票仍留在观察名单中
- 第二天继续检查时发现已过期，导致 `signal_date` 和 `target_date` 自动顺延到下一天
- 更严重的是，如果同一天收到新的 BUY 信号，会直接覆盖原有记录，造成"自动更新日期"的现象
- 这导致本应在当天买入的股票被无限期推迟，错失最佳买点甚至涨停机会

**三层防护体系：**

1. **第一层：防重入保护** ([`process_signal`](file://d:\迅投QMT交易终端%20华林证券模拟版\mpython\strategies\delayed_strategy.py#L100-L185))
   ```python
   # 如果股票已在观察名单中且今天是目标日，拒绝重新加入
   if code in watchlist and today >= existing_target_date:
       logger.log("[延时策略-拒绝重复] 已在观察名单中且今天是目标日，拒绝重新加入")
       return False  # 直接拒绝，不执行后续写入
   ```

2. **第二层：使用原始触发门槛** ([`check_and_execute`](file://d:\迅投QMT交易终端%20华林证券模拟版\mpython\strategies\delayed_strategy.py#L196-L293))
   ```python
   # 使用加入名单时记录的 trigger_volume_ratio，而非固定的 0.2
   original_trigger_vr = item.get('trigger_volume_ratio', 0)
   if current_vr >= original_trigger_vr:
       # 立即买入
   ```

3. **第三层：无条件清理机制** ([`check_and_execute`](file://d:\迅投QMT交易终端%20华林证券模拟版\mpython\strategies\delayed_strategy.py#L196-L293)) ⭐⭐⭐
   ```python
   # 路径 A（信号优先）：无论成功与否，都清除
   success = self._execute_buy(code, item)
   if success:
       logger.log("[延时策略-成功] {} 买入订单已提交".format(code))
   else:
       logger.log("[延时策略-失败] {} 买入订单提交失败，但仍会清除记录（防止延期）".format(code))
   codes_to_remove.append(code)  # ← 无条件清除
   
   # 路径 B（保底机制）：同样无条件清除
   codes_to_remove.append(code)
   ```

**核心理念：**
> **目标日当天必须完成决策，无论成败都要翻篇。**
> 
> 如果买入失败，说明当天没有机会，不应该无限期等待。
> 如果需要再次交易，应该等待新的信号。

**日志验证示例：**

✅ **正常买入：**
```
[延时策略-信号优先] 301018.SZ 量比 2.84 >= 原始门槛 0.84，立即买入
[下单] 301018.SZ 买入 500 股 @ 116.13 元 (量比: 2.84)
[延时策略-成功] 301018.SZ 买入订单已提交
[延时策略-清理] 已从观察名单移除 1 只股票（无论成败，目标日结束必须清除）
```

✅ **买入失败但不会延期：**
```
[延时策略-信号优先] 301018.SZ 量比 2.84 >= 原始门槛 0.84，立即买入
[仓位] 301018.SZ 现金不足 (剩 5000.00)
[延时策略-失败] 301018.SZ 买入订单提交失败，但仍会清除记录（防止延期）
[延时策略-清理] 已从观察名单移除 1 只股票（无论成败，目标日结束必须清除）
```

✅ **拒绝重复信号：**
```
[延时策略-拒绝重复] 301018.SZ 已在观察名单中且今天是目标日，拒绝重新加入，避免自动延期
[延时策略-拒绝重复] 现有记录: signal_date=2026-04-13, target_date=2026-04-14
```

---

## 🛠️ 历史稳定性优化 (2026-04-15)

| 优化项 | 实施细节 | 解决的问题 |
| :--- | :--- | :--- |
| **路径迁移** | 从阿里云ESC迁移到本地 `D:\迅投极速交易终端 睿智融科版` | 适配新环境，使用相对路径自动计算 |
| **行情接口保活** | 在 [`get_index_change_percent`](file://d:\迅投极速交易终端%20睿智融科版\utils\helpers.py#L52-L85) 中增加 `xtdata.subscribe_whole_quote` | 防止长时间运行后返回空字典 `{}` 的"假死"现象 |
| **强制内存回收** | 主循环每 50 分钟执行一次 `gc.collect()` | 缓解 Python 在 Windows 下的内存碎片堆积 |
| **状态保存隔离** | 拆分大盘日志与精英名单保存的时间戳变量 | 确保状态文件严格按 10 分钟间隔原子写入，防冲突 |
| **止盈时间过滤** | 增加 [`is_after_take_profit_start`](file://d:\迅投极速交易终端%20睿智融科版\utils\helpers.py#L40-L50) 校验（默认 09:50） | 避开开盘剧烈波动，防止动态止盈误触发 |
| **路径安全加固** | 主入口强制执行 `os.chdir` 并配置相对路径 | 消除因工作目录不确定导致的相对路径失效 |

---

## ⚙️ 关键配置说明

### 1. 路径配置（已自动适配）
所有路径已改为**相对路径**，基于项目根目录自动计算：
```python
# config/settings.py 中的配置会自动适配
SIGNAL_DIR_INPUT = os.path.join(BASE_DIR_CODE, "signals")
LOG_DIR = os.path.join(BASE_DIR_CODE, "logs")
STATE_FILE = os.path.join(BASE_DIR_CODE, "yesterday_holdings.json")
```

**唯一需要手动配置的是 QMT_PATH：**
```python
QMT_PATH = r"D:\迅投极速交易终端 睿智融科版\userdata_mini"
```

### 2. 动态止盈时间
在 [`config/settings.py`](file://d:\迅投极速交易终端%20睿智融科版\config\settings.py) 中设置：
`EARLIEST_EXECUTION_TIME = 950` （即 09:50 开始执行三级止盈）

### 3. 硬性止损窗口
*   **开始时间**：`STOP_LOSS_START_TIME = "1045"`
*   **结束时间**：`STOP_LOSS_END_TIME = "1450"` （避开尾盘集合竞价）

### 4. 资金管理红线
*   **单笔上限**：50,000 元
*   **现金缓冲**：保留 2% 可用资金
*   **最小订单**：15,000 元

---

## 📦 部署与启动清单

### ⚠️ 重要提示：为什么不能在普通 Python 中运行？

本项目依赖 `xtquant` 模块，这是 **QMT 交易终端的专有接口**。因此：
- ❌ **不能**使用系统安装的 Python（如 Python 3.11）
- ✅ **必须**使用 QMT 自带的 Python 解释器
- ✅ **必须**保持 QMT 客户端登录在线

如果你看到错误：`ModuleNotFoundError: No module named 'xtquant'`，说明你使用了错误的 Python 环境。

### 第一步：清理缓存（必做）
每次更新代码后，必须删除所有 `__pycache__` 文件夹。

**一键脚本会自动完成此步骤！**

### 第二步：使用一键脚本启动（推荐）

双击运行项目根目录下的 **`启动AlphaPilot.bat`**。

该脚本会：
1. ✅ 自动清理 Python 缓存
2. ✅ 自动查找 QMT Python 解释器
3. ✅ 验证 xtquant 模块是否可用
4. ✅ 启动策略引擎

### 第三步：手动启动（备选方案）

如果一键脚本无法找到 QMT Python，可以手动指定路径：

```batch
REM 打开命令提示符，执行以下命令：
cd /d "D:\AlphaPilot_Pro"

REM 使用 QMT Python 运行（根据实际路径调整）
"D:\迅投极速交易终端 睿智融科版\bin.x64\python.exe" main.py
```

或者尝试其他常见路径：
```batch
"D:\迅投极速交易终端 睿智融科版\mpython\python.exe" main.py
"D:\迅投极速交易终端 睿智融科版\python\python.exe" main.py
```

### 第四步：验证运行状态

观察控制台或日志文件（`logs/` 目录），确认出现以下标识：
1. `[成功] 交易引擎初始化完成`
2. `[大盘] 上证指数：XX%` （持续输出证明行情保活成功）
3. `[维护] 已执行强制垃圾回收` （每 50 分钟出现一次）

---

## 🔍 常见问题排查

### Q1: 提示 "ModuleNotFoundError: No module named 'xtquant'"
**原因**：使用了系统 Python 而非 QMT Python  
**解决**：使用一键启动脚本，或手动指定 QMT Python 路径

### Q2: 找不到 QMT Python 解释器
**解决**：检查以下常见位置：
- `D:\迅投极速交易终端 睿智融科版\bin.x64\python.exe`
- `D:\迅投极速交易终端 睿智融科版\mpython\python.exe`
- `D:\迅投极速交易终端 睿智融科版\python\python.exe`
- 查看 QMT 安装目录下的 `bin.x64`、`mpython` 或 `python` 文件夹

### Q3: 路径相关错误
**解决**：运行以下命令验证路径配置：
```bash
python -c "from config import settings; print('QMT_PATH:', settings.QMT_PATH); print('SIGNAL_DIR:', settings.SIGNAL_DIR_INPUT)"
```

### Q4: QMT 客户端未登录
**症状**：程序启动后立即退出或无法连接账户  
**解决**：确保 QMT 极简模式客户端已登录且在线

---

## 💡 专家经验总结：QMT 对接三大铁律

1.  **永远不要信任文件系统同步**：修改代码后，清除缓存 + 完全重启是铁律。
2.  **行情接口必须主动保活**：`xtdata` 不会自动重连，必须在获取数据前调用订阅接口。
3.  **配置与状态必须分离**：静态参数用 JSON（热更新），动态状态用独立文件（持久化）。
4.  **【新增】必须使用 QMT 自带 Python**：系统 Python 缺少 `xtquant` 模块，无法运行策略。

---

## 📝 路径迁移记录

### 迁移历史
- **第一次迁移**：从阿里云ESC迁移到本地华林证券模拟版
- **第二次迁移（当前）**：适配睿智融科版新环境

### 当前环境配置
```
项目路径：D:\AlphaPilot_Pro
QMT路径：D:\迅投极速交易终端 睿智融科版
Python路径：D:\迅投极速交易终端 睿智融科版\bin.x64\python.exe（首选）
```

### 改进点
- ✅ 使用相对路径，自动适配任何安装位置
- ✅ 创建一键启动脚本，简化运行流程
- ✅ 添加详细的路径验证和错误提示
- ✅ 支持多版本QMT环境的Python路径自动检测

---

**结语：**  
经过多轮深度优化、路径迁移和延时策略防延期修复，AlphaPilot Pro 已具备极强的长时运行稳定性和策略执行可靠性。本版本已全面适配睿智融科版新环境，请严格遵循上述部署流程，祝实战顺利！

**—— 顶级 QMT 专家 & Alphapilot AI 智能体协作团队，2026-04-15**
