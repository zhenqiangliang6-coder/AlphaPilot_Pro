# -*- coding: utf-8 -*-
"""
AlphaPilot Pro 环境检查脚本
在运行 AlphaPilot Pro 之前执行，检查所有必要的配置和依赖

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

print("="*60)
print("AlphaPilot Pro 环境检查")
print("="*60)

errors = []
warnings = []

# 1. 检查 Python 版本
print("\n[1] 检查 Python 版本...")
python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
print(f"    ✓ Python 版本：{python_version}")

# 2. 检查必要目录
print("\n[2] 检查项目结构...")
required_dirs = [
    'config',
    'core',
    'strategies',
    'risk',
    'utils'
]

for dir_name in required_dirs:
    if os.path.exists(dir_name):
        print(f"    ✓ {dir_name}/ 存在")
    else:
        errors.append(f"缺少必要目录：{dir_name}/")
        print(f"    ✗ {dir_name}/ 不存在")

# 3. 检查关键文件
print("\n[3] 检查关键文件...")
required_files = [
    'main.py',
    'config/settings.py',
    'core/trader_engine.py',
    'core/state_manager.py',
    'strategies/auction_strategy.py',
    'strategies/signal_strategy.py',
    'strategies/rocket_boost.py',
    'risk/stop_loss.py',
    'utils/helpers.py',
    'utils/logger.py'
]

for file_path in required_files:
    if os.path.exists(file_path):
        print(f"    ✓ {file_path}")
    else:
        errors.append(f"缺少关键文件：{file_path}")
        print(f"    ✗ {file_path} 不存在")

# 4. 检查 xtquant 库
print("\n[4] 检查 xtquant 库...")
try:
    import xtquant
    print(f"    ✓ xtquant 已安装")
    print(f"      路径：{xtquant.__file__}")
except ImportError as e:
    errors.append("xtquant 库未安装或无法导入")
    print(f"    ✗ xtquant 导入失败：{e}")

# 5. 检查配置文件
print("\n[5] 检查配置参数...")
try:
    from config import settings
    
    # 检查 QMT_PATH
    if os.path.exists(settings.QMT_PATH):
        print(f"    ✓ QMT 路径有效：{settings.QMT_PATH}")
    else:
        warnings.append(f"QMT 路径不存在：{settings.QMT_PATH}")
        print(f"    ⚠ QMT 路径不存在（请确认 QMT 已安装）")
    
    # 检查 ACCOUNT_ID
    if settings.ACCOUNT_ID:
        print(f"    ✓ 账户 ID: {settings.ACCOUNT_ID}")
    else:
        errors.append("账户 ID 为空")
        print(f"    ✗ 账户 ID 未配置")
    
    # 检查信号目录
    if os.path.exists(settings.SIGNAL_DIR_INPUT):
        print(f"    ✓ 信号目录存在：{settings.SIGNAL_DIR_INPUT}")
    else:
        warnings.append(f"信号目录不存在：{settings.SIGNAL_DIR_INPUT}")
        print(f"    ⚠ 信号目录不存在（程序将自动创建）")
    
    # 检查安全目录
    if os.path.exists(settings.BASE_DIR_SAFE):
        print(f"    ✓ 安全目录存在：{settings.BASE_DIR_SAFE}")
    else:
        warnings.append(f"安全目录不存在：{settings.BASE_DIR_SAFE}")
        print(f"    ⚠ 安全目录不存在（程序将自动创建）")
    
    # 检查策略参数
    print(f"\n    策略参数:")
    print(f"      - 精英利润阈值：{settings.ELITE_PROFIT_THRESHOLD*100}%")
    print(f"      - 竞价卖出比例：{settings.AUCTION_SELL_RATIO*100}%")
    print(f"      - 初始仓位比例：{settings.INITIAL_CAPITAL_RATIO*100}%")
    print(f"      - 最大持股数：{settings.MAX_STOCK_COUNT}")
    print(f"      - 止损比例：{settings.STOP_LOSS_RATIO*100}%")
    
except Exception as e:
    errors.append(f"配置文件加载失败：{e}")
    print(f"    ✗ 配置加载失败：{e}")

# 6. 检查 __init__.py 文件
print("\n[6] 检查模块初始化文件...")
init_files = [
    'config/__init__.py',
    'core/__init__.py',
    'strategies/__init__.py',
    'risk/__init__.py',
    'utils/__init__.py'
]

for init_file in init_files:
    if os.path.exists(init_file):
        print(f"    ✓ {init_file}")
    else:
        warnings.append(f"缺少模块初始化：{init_file}")
        print(f"    ⚠ {init_file} 不存在")

# 7. 总结
print("\n" + "="*60)
print("检查结果汇总")
print("="*60)

if errors:
    print(f"\n❌ 发现 {len(errors)} 个错误:")
    for err in errors:
        print(f"   - {err}")
else:
    print("\n✓ 没有发现错误")

if warnings:
    print(f"\n⚠️  发现 {len(warnings)} 个警告:")
    for warn in warnings:
        print(f"   - {warn}")
else:
    print("\n✓ 没有发现警告")

print("\n" + "="*60)

if not errors:
    print("✓ 环境检查通过！可以运行 AlphaPilot Pro")
    print("\n启动命令:")
    print("  python main.py")
    print("  或在 QMT 中运行：启动.py")
else:
    print("✗ 环境检查未通过，请先修复错误后再运行")

print("="*60)
