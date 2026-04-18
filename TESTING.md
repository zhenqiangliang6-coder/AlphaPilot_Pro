# 测试指南 - AlphaPilot Pro

## 🧪 测试清单

### 1️⃣ 环境验证测试

#### 测试1.1：路径配置验证
```bash
python -c "from config import settings; print('QMT_PATH:', settings.QMT_PATH); print('SIGNAL_DIR:', settings.SIGNAL_DIR_INPUT); print('LOG_DIR:', settings.LOG_DIR)"
```

**预期结果：**
```
QMT_PATH: D:\迅投QMT交易终端 华林证券模拟版\userdata_mini
SIGNAL_DIR: D:\迅投QMT交易终端 华林证券模拟版\mpython\signals
LOG_DIR: D:\迅投QMT交易终端 华林证券模拟版\mpython\logs
```

#### 测试1.2：目录存在性验证
```bash
python -c "import os; from config import settings; dirs = [settings.SIGNAL_DIR_INPUT, settings.LOG_DIR, settings.DATA_DIR]; [print(f'✅ {d}' if os.path.exists(d) else f'❌ {d}') for d in dirs]"
```

**预期结果：**
```
✅ D:\迅投QMT交易终端 华林证券模拟版\mpython\signals
✅ D:\迅投QMT交易终端 华林证券模拟版\mpython\logs
✅ D:\迅投QMT交易终端 华林证券模拟版\mpython\data
```

---

### 2️⃣ QMT Python 环境测试

#### 测试2.1：运行检测工具
双击运行：`检测QTMPython.bat`

**预期结果：**
- ✅ 找到 QMT Python 解释器路径
- ✅ xtquant 模块可用
- 显示 Python 版本信息

#### 测试2.2：手动验证 xtquant
使用检测到的 QMT Python 路径执行：
```bash
"D:\迅投QMT交易终端 华林证券模拟版\python\python.exe" -c "import xtquant; print('✅ xtquant 可用')"
```

**预期结果：**
```
✅ xtquant 可用
```

---

### 3️⃣ 启动脚本测试

#### 测试3.1：一键启动脚本
双击运行：`启动AlphaPilot.bat`

**预期流程：**
1. ✅ [1/3] 清理 Python 缓存
2. ✅ [2/3] 检测 QMT Python 环境
3. ✅ [3/3] 验证 xtquant 模块
4. 🚀 启动 AlphaPilot Pro 策略引擎

**预期输出：**
```
========================================
  AlphaPilot Pro - 一键启动脚本
========================================

[1/3] 清理 Python 缓存...
✅ 缓存清理完成

[2/3] 检测 QMT Python 环境...
✅ 找到 QMT Python: D:\迅投QMT交易终端 华林证券模拟版\python\python.exe

[3/3] 验证 xtquant 模块...
✅ xtquant 模块可用

========================================
  启动 AlphaPilot Pro 策略引擎
  按 Ctrl+C 可停止运行
========================================

============================================================
启动 AlphaPilot Pro (模块化版本)
============================================================
[成功] 交易引擎初始化完成
[大盘] 上证指数：X.XX%
```

---

### 4️⃣ 功能模块测试

#### 测试4.1：配置模块导入
```bash
"D:\迅投QMT交易终端 华林证券模拟版\python\python.exe" -c "from config import settings; print('✅ config 模块正常')"
```

#### 测试4.2：工具模块导入（需要 QMT 环境）
```bash
"D:\迅投QMT交易终端 华林证券模拟版\python\python.exe" -c "from utils.helpers import is_auction_time, is_trading_time; print('✅ utils.helpers 模块正常'); print('竞价时间判断:', is_auction_time('0920')); print('交易时间判断:', is_trading_time('1000'))"
```

**预期结果：**
```
✅ utils.helpers 模块正常
竞价时间判断: True
交易时间判断: True
```

---

### 5️⃣ 集成测试

#### 测试5.1：完整启动测试
1. 确保 QMT 客户端已登录
2. 运行 `启动AlphaPilot.bat`
3. 观察至少 2 分钟

**检查点：**
- [ ] 程序成功启动，无报错
- [ ] 看到 `[成功] 交易引擎初始化完成`
- [ ] 每 30 秒输出一次大盘指数
- [ ] 日志文件在 `logs/` 目录生成
- [ ] 状态文件 `yesterday_holdings.json` 存在

#### 测试5.2：信号处理测试
1. 在 `signals/` 目录创建一个测试信号文件
2. 等待程序处理（最多 3 秒）
3. 检查文件是否移动到 `signals/processed/`

**示例信号文件：** `test_signal.json`
```json
{
    "stock_code": "600000.SH",
    "action": "buy",
    "price": 10.5,
    "volume": 1000
}
```

---

### 6️⃣ 压力测试

#### 测试6.1：长时间运行测试
让程序连续运行 2 小时以上，检查：
- [ ] 内存占用稳定（无明显增长）
- [ ] 每 50 分钟执行一次垃圾回收
- [ ] 日志文件正常写入
- [ ] 无崩溃或假死现象

#### 测试6.2：日期切换测试
跨越交易日边界运行，检查：
- [ ] 自动识别新交易日
- [ ] 精英名单重新加载
- [ ] 每日计数器重置

---

## 🐛 故障排查

### 问题1：ModuleNotFoundError: No module named 'xtquant'

**诊断步骤：**
1. 确认使用的是 QMT Python 而非系统 Python
2. 运行 `检测QTMPython.bat` 验证环境
3. 确认 QMT 客户端已登录

**解决方案：**
- 使用一键启动脚本
- 或手动指定 QMT Python 路径

### 问题2：无法连接 QMT 账户

**诊断步骤：**
1. 检查 QMT 客户端是否在线
2. 验证 `config/settings.py` 中的 ACCOUNT_ID
3. 查看日志中的错误信息

**解决方案：**
- 重新启动 QMT 客户端并登录
- 确认账户 ID 正确（当前：10100000030）

### 问题3：路径相关错误

**诊断步骤：**
1. 运行路径配置验证测试
2. 检查所有必要目录是否存在
3. 确认 QMT_PATH 指向正确的 userdata_mini 目录

**解决方案：**
- 更新 `config/settings.py` 中的 QMT_PATH
- 运行 `ensure_dirs()` 创建缺失目录

---

## 📊 测试报告模板

```markdown
## 测试报告

**测试日期：** 2026-04-13  
**测试人员：** [你的名字]  
**QMT 版本：** [版本号]  
**Python 版本：** [版本号]

### 测试结果汇总
- 环境验证测试：✅ 通过 / ❌ 失败
- QMT Python 环境测试：✅ 通过 / ❌ 失败
- 启动脚本测试：✅ 通过 / ❌ 失败
- 功能模块测试：✅ 通过 / ❌ 失败
- 集成测试：✅ 通过 / ❌ 失败

### 发现的问题
1. [问题描述]
2. [问题描述]

### 建议改进
1. [改进建议]
2. [改进建议]
```

---

## ✅ 测试完成清单

在正式使用前，请确保：
- [ ] 所有环境验证测试通过
- [ ] QMT Python 环境正常
- [ ] 一键启动脚本可以成功运行
- [ ] 程序能持续运行 10 分钟以上无错误
- [ ] 日志文件正常生成
- [ ] 大盘数据能正常获取
- [ ] QMT 客户端保持在线

**全部通过后，即可投入实战使用！** 🎉