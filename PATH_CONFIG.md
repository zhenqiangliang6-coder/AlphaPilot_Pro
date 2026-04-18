# 路径配置说明

## 📁 项目路径迁移完成（2026-04-15）

本项目已适配新的QMT环境：
```
D:\迅投极速交易终端 睿智融科版
```

## ✅ 已完成的更新

### 1. 配置文件更新

#### `config/settings.py`
- ✅ QMT_PATH: `D:\迅投极速交易终端 睿智融科版\userdata_mini`
- ✅ SIGNAL_DIR_INPUT: 使用相对路径 `项目根目录/signals`
- ✅ BASE_DIR_SAFE: 使用相对路径 `项目根目录`
- ✅ STATE_FILE: 使用相对路径 `项目根目录/yesterday_holdings.json`
- ✅ LOG_DIR: 使用相对路径 `项目根目录/logs`

### 2. 启动脚本更新

所有启动脚本已更新以支持新环境：
- ✅ `启动AlphaPilot.bat` - 推荐的一键启动脚本
- ✅ `启动 AlphaPilot.bat` - 备用启动脚本
- ✅ `3_AlphaPilot.bat` - 备用启动脚本
- ✅ `启动交易.py` - Python启动脚本

### 3. 目录结构

```
AlphaPilot_Pro/
├── signals/              # 信号输入目录
│   └── processed/        # 已处理信号归档
├── logs/                 # 日志文件目录
├── data/                 # 数据文件目录
├── config/               # 配置文件
├── core/                 # 核心模块
├── strategies/           # 策略模块
├── risk/                 # 风控模块
└── utils/                # 工具模块
```

## 🔧 路径配置原理

所有路径都使用 **相对路径** 和 **动态获取** 的方式：

```python
# 自动获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 基于项目根目录构建其他路径
SIGNAL_DIR_INPUT = os.path.join(BASE_DIR, "signals")
LOG_DIR = os.path.join(BASE_DIR, "logs")
```

### 优势：
1. ✅ **可移植性强** - 无论项目放在哪个盘符或目录，都能正常运行
2. ✅ **无需手动修改** - 迁移项目时无需修改任何路径配置
3. ✅ **避免硬编码** - 消除了绝对路径带来的维护问题

## ⚠️ 注意事项

### QMT_PATH 需要手动配置
由于QMT终端路径是固定的系统路径，如果QMT安装位置变化，需要手动更新：

**在以下文件中修改：**
- `config/settings.py` 第21行

```python
QMT_PATH = r"D:\迅投极速交易终端 睿智融科版\userdata_mini"
```

### Python解释器路径
新环境中Python解释器可能位于以下位置之一（启动脚本会自动检测）：
- `D:\迅投极速交易终端 睿智融科版\bin.x64\python.exe` （首选）
- `D:\迅投极速交易终端 睿智融科版\mpython\python.exe`
- `D:\迅投极速交易终端 睿智融科版\python\python.exe`

### 首次运行前检查
1. 确保 `signals/` 目录存在
2. 确保 `signals/processed/` 目录存在
3. 确保 `logs/` 目录存在
4. 确认QMT终端路径正确
5. 确认QMT客户端已登录

## 🚀 快速验证

运行以下命令验证路径配置：

```python
python -c "from config import settings; print('QMT_PATH:', settings.QMT_PATH); print('SIGNAL_DIR:', settings.SIGNAL_DIR_INPUT); print('LOG_DIR:', settings.LOG_DIR)"
```

预期输出：
```
QMT_PATH: D:\迅投极速交易终端 睿智融科版\userdata_mini
SIGNAL_DIR: D:\AlphaPilot_Pro\signals
LOG_DIR: D:\AlphaPilot_Pro\logs
```

## 📝 迁移历史

- **第一次迁移** (2026-04-13): 从阿里云ESC迁移到本地华林证券模拟版
- **第二次迁移** (2026-04-15): 适配睿智融科版新环境
  - 项目路径：`D:\AlphaPilot_Pro`
  - QMT路径：`D:\迅投极速交易终端 睿智融科版`
  - Python路径：优先使用 `bin.x64\python.exe`
