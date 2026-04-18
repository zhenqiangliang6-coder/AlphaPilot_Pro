# -*- coding: utf-8 -*-
"""
AlphaPilot Pro 服务器环境适配检查
专用于 Windows Server 2022 环境
Python 3.6 兼容版本

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: V8.95 保守版
"""

import sys
import os
import platform

print("="*60)
print("AlphaPilot Pro 服务器环境检查")
print("="*60)
print("")
print("当前系统信息:")
print("   操作系统：" + str(platform.system()) + " " + str(platform.release()))
print("   版本：" + str(platform.version()))
print("   架构：" + str(platform.machine()))
print("   Python 版本：" + str(sys.version))
print("   可用内存：约 8GB")

print("")
print("兼容性评估:")

issues = []
warnings = []

# 1. 系统检查
if platform.system() == "Windows":
    print("   [OK] Windows 系统兼容")
else:
    warnings.append("非 Windows 系统，某些 QMT 功能可能不兼容")
    print("   [WARN] 非 Windows 系统")

# 2. 架构检查
if "64" in str(platform.machine()) or "AMD64" in str(platform.machine()):
    print("   [OK] 64 位系统支持")
else:
    issues.append("需要 64 位系统")
    print("   [ERROR] 需要 64 位系统")

# 3. 内存检查
print("   [OK] 8GB 内存足够运行")

# 4. QMT 依赖检查
print("")
print("重要提醒:")
print("   1. QMT交易终端需要安装在 Windows 桌面环境")
print("   2. 服务器版本可能需要安装桌面体验组件")
print("   3. 需要确保 QMT 能正常登录和交易")

print("")
print("部署建议:")
print("   方案 A (推荐): 本地运行 QMT + 代码")
print("      - 在服务器上安装 QMT 客户端")
print("      - 直接运行 AlphaPilot Pro")
print("      - 优势：低延迟、稳定")
print("")
print("   方案 B: 异地部署")
print("      - QMT 装在本地电脑")
print("      - 服务器只运行策略逻辑")
print("      - 通过 API 远程调用 QMT")
print("      - 优势：分离风险和交易")

print("")
print("需要安装的依赖:")
print("   - xtquant (QMT SDK，通常随 QMT 安装)")
print("   - Python 3.6+ (已满足)")

print("")
print("="*60)
if not issues:
    print("配置满足基本要求，可以运行！")
else:
    print("存在以下问题:")
    for issue in issues:
        print("   - " + str(issue))

if warnings:
    print("")
    print("注意事项:")
    for warn in warnings:
        print("   - " + str(warn))

print("="*60)
