# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 新环境检测工具
用于验证睿智融科版QMT环境的配置是否正确

作者: Alphapilot智能体团队
版本: V8.95 保守版
日期: 2026-04-15
"""

import os
import sys
from datetime import datetime

print("="*70)
print(" " * 20 + "AlphaPilot Pro 环境检测工具")
print(" " * 22 + "睿智融科版专用")
print("="*70)
print("")
print("检测时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("")

# ==================== 检测项 1: 项目路径 ====================
print("[1/6] 检查项目路径...")
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
print("   当前路径: " + PROJECT_PATH)

if os.path.exists(PROJECT_PATH):
    print("   ✅ 项目路径存在")
else:
    print("   ❌ 项目路径不存在")
    sys.exit(1)
print("")

# ==================== 检测项 2: 必要目录 ====================
print("[2/6] 检查必要目录...")
required_dirs = [
    "signals",
    "signals/processed",
    "logs",
    "data",
    "config"
]

all_dirs_ok = True
for dir_name in required_dirs:
    dir_path = os.path.join(PROJECT_PATH, dir_name)
    if os.path.exists(dir_path):
        print("   ✅ " + dir_name)
    else:
        print("   ❌ " + dir_name + " (缺失)")
        all_dirs_ok = False
        # 自动创建缺失的目录
        try:
            os.makedirs(dir_path, exist_ok=True)
            print("      → 已自动创建")
        except Exception as e:
            print("      → 创建失败: " + str(e))

if all_dirs_ok:
    print("   ✅ 所有必要目录都存在")
else:
    print("   ⚠️  部分目录已自动创建")
print("")

# ==================== 检测项 3: QMT路径配置 ====================
print("[3/6] 检查QMT路径配置...")
try:
    from config import settings
    qmt_path = settings.QMT_PATH
    print("   配置的QMT路径: " + qmt_path)
    
    if os.path.exists(qmt_path):
        print("   ✅ QMT路径存在")
    else:
        print("   ❌ QMT路径不存在")
        print("   提示: 请检查 config/settings.py 中的 QMT_PATH 配置")
except Exception as e:
    print("   ❌ 无法加载配置: " + str(e))
print("")

# ==================== 检测项 4: Python解释器 ====================
print("[4/6] 检查Python解释器...")
python_exe = sys.executable
print("   当前Python: " + python_exe)

# 检查是否在QMT环境中
if "迅投" in python_exe or "QMT" in python_exe.upper() or "pythonw.exe" in python_exe.lower():
    print("   ✅ 使用的是QMT自带Python")
else:
    print("   ⚠️  可能不是QMT自带Python")
    print("   提示: 请使用启动脚本运行程序")
print("")

# ==================== 检测项 5: xtquant模块 ====================
print("[5/6] 检查xtquant模块...")
try:
    import xtquant
    print("   ✅ xtquant 模块可用")
    print("   版本信息: " + str(xtquant.__version__) if hasattr(xtquant, '__version__') else "   版本信息: 未知")
except ImportError as e:
    print("   ❌ xtquant 模块不可用")
    print("   错误: " + str(e))
    print("")
    print("   可能原因:")
    print("   1. 未使用QMT自带的Python解释器")
    print("   2. QMT客户端未登录")
    print("   3. xtquant模块未正确安装")
print("")

# ==================== 检测项 6: 关键文件 ====================
print("[6/6] 检查关键文件...")
critical_files = [
    "config/settings.py",
    "main.py",
    "data/stock_personalities.json"
]

all_files_ok = True
for file_name in critical_files:
    file_path = os.path.join(PROJECT_PATH, file_name)
    if os.path.exists(file_path):
        print("   ✅ " + file_name)
    else:
        print("   ❌ " + file_name + " (缺失)")
        all_files_ok = False

if all_files_ok:
    print("   ✅ 所有关键文件都存在")
else:
    print("   ❌ 部分关键文件缺失")
print("")

# ==================== 总结 ====================
print("="*70)
print("检测结果总结")
print("="*70)
print("")

if all_dirs_ok and all_files_ok:
    print("✅ 环境检测通过！可以正常运行 AlphaPilot Pro")
    print("")
    print("下一步操作:")
    print("1. 确保QMT客户端已登录")
    print("2. 双击运行 '启动AlphaPilot.bat'")
    print("3. 观察控制台输出和 logs/ 目录下的日志")
else:
    print("⚠️  环境检测发现问题，请先修复上述错误")
    print("")
    print("建议操作:")
    print("1. 检查缺失的目录和文件")
    print("2. 确认QMT路径配置正确")
    print("3. 使用QMT自带的Python解释器")

print("")
print("="*70)
print("检测完成")
print("="*70)
print("")
input("按回车键退出...")
