# -*- coding: utf-8 -*-
"""
AlphaPilot Pro 快速启动脚本（QMT 专用）
在 QMT Python 控制台中运行此脚本

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

# 添加项目路径
PROJECT_PATH = r'C:\迅投QMT交易终端 华林证券模拟版\mpython\AlphaPilot_Pro'
if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

print("="*60)
print("AlphaPilot Pro 启动器")
print("="*60)

try:
    # 导入主程序
    from main import main_loop
    
    print("[成功] 程序加载完成，开始运行...")
    print("-"*60)
    
    # 运行主循环
    main_loop()
    
except Exception as e:
    print(f"[错误] 启动失败：{e}")
    import traceback
    traceback.print_exc()
