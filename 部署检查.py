# -*- coding: utf-8 -*-
"""
AlphaPilot Pro 部署验证工具
用于快速检查部署是否完整、配置是否正确
Python 3.6 兼容版本

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

PROJECT_PATH = r'C:\迅投QMT交易终端 华林证券模拟版\mpython\AlphaPilot_Pro'

print("="*70)
print(" " * 20 + "AlphaPilot Pro 部署验证")
print("="*70)
print("")

errors = []
warnings = []
success_count = 0

# 1. 检查项目路径
print("[1] 检查项目路径...")
if os.path.exists(PROJECT_PATH):
    print("   [OK] 项目路径存在：" + PROJECT_PATH)
    success_count += 1
else:
    print("   [ERROR] 项目路径不存在：" + PROJECT_PATH)
    errors.append("项目路径不存在")

print("")

# 切换到项目目录
os.chdir(PROJECT_PATH)

# 2. 检查核心文件
print("[2] 检查核心文件...")
core_files = [
    'main.py',
    'config/settings.py',
    'core/trader_engine.py',
    'core/state_manager.py',
    'strategies/delayed_strategy.py',
    'strategies/signal_strategy.py',
    'strategies/auction_strategy.py',
    'strategies/rocket_boost.py',
    'risk/stop_loss.py',
    'utils/helpers.py',
    'utils/logger.py'
]

for file_path in core_files:
    full_path = os.path.join(PROJECT_PATH, file_path)
    if os.path.exists(full_path):
        print("   [OK] " + file_path)
        success_count += 1
    else:
        print("   [ERROR] " + file_path + " (缺失)")
        errors.append("缺少核心文件：" + file_path)

print("")

# 3. 检查配置文件
print("[3] 检查配置文件...")
config_files = [
    ('data/stock_personalities.json', True),
    ('data/delayed_watchlist.json', True)
]

for file_path, required in config_files:
    full_path = os.path.join(PROJECT_PATH, file_path)
    if os.path.exists(full_path):
        print("   [OK] " + file_path)
        success_count += 1
    else:
        if required:
            print("   [WARN] " + file_path + " (不存在，将自动创建)")
            warnings.append("配置文件不存在：" + file_path)
        else:
            print("   [INFO] " + file_path + " (可选)")

print("")

# 4. 检查 Python 依赖
print("[4] 检查 Python 环境...")
print("   Python 版本：" + sys.version)

try:
    import xtquant
    print("   [OK] xtquant 已安装")
    success_count += 1
except ImportError as e:
    print("   [ERROR] xtquant 未安装：" + str(e))
    errors.append("xtquant 库未安装")

try:
    import json
    print("   [OK] json 模块正常")
    success_count += 1
except Exception as e:
    print("   [ERROR] json 模块异常：" + str(e))
    errors.append("json 模块不可用")

print("")

# 5. 检查配置参数
print("[5] 检查配置文件参数...")
try:
    from config import settings
    
    # 检查 QMT_PATH
    if os.path.exists(settings.QMT_PATH):
        print("   [OK] QMT 路径有效")
        success_count += 1
    else:
        print("   [WARN] QMT 路径不存在：" + str(settings.QMT_PATH))
        warnings.append("QMT 路径可能配置错误")
    
    # 检查 ACCOUNT_ID
    if settings.ACCOUNT_ID and len(settings.ACCOUNT_ID) > 0:
        print("   [OK] 账户 ID 已配置：" + str(settings.ACCOUNT_ID))
        success_count += 1
    else:
        print("   [ERROR] 账户 ID 未配置")
        errors.append("账户 ID 为空")
    
    # 检查策略参数
    if hasattr(settings, 'ELITE_PROFIT_THRESHOLD'):
        print("   [OK] 策略参数已配置")
        success_count += 1
    else:
        print("   [WARN] 部分策略参数可能缺失")
        warnings.append("策略参数配置不完整")
    
except Exception as e:
    print("   [ERROR] 配置文件加载失败：" + str(e))
    errors.append("配置文件加载失败")

print("")

# 6. 尝试导入主程序
print("[6] 测试主程序导入...")
try:
    # 临时添加路径
    if PROJECT_PATH not in sys.path:
        sys.path.insert(0, PROJECT_PATH)
    
    import main
    print("   [OK] 主程序可正常导入")
    success_count += 1
except Exception as e:
    print("   [ERROR] 主程序导入失败：" + str(e))
    errors.append("主程序导入失败")

print("")

# 7. 总结
print("="*70)
print("检查结果汇总")
print("="*70)
print("")
print("成功项：" + str(success_count) + " 个")

if warnings:
    print("\n警告：" + str(len(warnings)) + " 个")
    for warn in warnings:
        print("   - " + str(warn))

if errors:
    print("\n错误：" + str(len(errors)) + " 个")
    for err in errors:
        print("   - " + str(err))
else:
    print("\n没有发现致命错误！")

print("")
print("="*70)

# 给出建议
if not errors:
    print("部署验证通过！系统可以运行。")
    print("")
    print("下一步操作:")
    print("1. 确保 QMT交易终端已启动并登录")
    print("2. 运行 '启动交易.py' 开始交易")
    print("3. 观察日志输出，确认一切正常")
else:
    print("部署验证未通过，请先修复以下问题:")
    for err in errors:
        print("   - " + str(err))
    print("")
    print("修复后请重新运行本检查脚本。")

print("")
print("="*70)

# 如果有错误或警告，等待用户查看
if errors or warnings:
    raw_input("\n按回车键退出...")
