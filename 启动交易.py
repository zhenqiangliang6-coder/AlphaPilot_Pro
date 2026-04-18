# -*- coding: utf-8 -*-
"""
AlphaPilot Pro 快速启动脚本（新环境专用）
适用于 Windows + QMT 睿智融科版环境
Python 3.6 兼容版本

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: V8.95 保守版
【新环境】D:\迅投极速交易终端 睿智融科版
"""

import sys
import os
import time
from datetime import datetime

# 设置项目路径（新环境）
PROJECT_PATH = r'D:\AlphaPilot_Pro'

print("="*70)
print(" " * 15 + "AlphaPilot Pro 量化交易系统")
print(" " * 18 + "睿智融科版专用启动器")
print("="*70)
print("")

# 检查项目路径
if not os.path.exists(PROJECT_PATH):
    print("错误：项目路径不存在")
    print("   路径：" + PROJECT_PATH)
    print("")
    print("请确认:")
    print("1. QMT交易终端已正确安装")
    print("2. AlphaPilot_Pro 文件夹位于正确位置")
    raw_input("\n按回车键退出...")
    sys.exit(1)

print("项目路径：" + PROJECT_PATH)
print("")

# 添加到 Python 路径
if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

print("加载模块中...")
try:
    # 导入配置
    from config import settings
    print("   配置文件加载成功")
    
    # 导入主程序
    from main import main_loop
    print("   主程序加载成功")
    
    # 导入工具
    from utils.logger import init_logger, get_logger
    from utils.helpers import ensure_dirs
    print("   工具模块加载成功")
    
except Exception as e:
    print("   加载失败：" + str(e))
    print("")
    print("可能原因:")
    print("1. xtquant 库未正确安装")
    print("2. QMT交易终端未启动")
    print("3. Python 环境问题")
    raw_input("\n按回车键退出...")
    sys.exit(1)

print("")
print("="*70)
print("系统启动准备就绪")
print("="*70)
print("")
print("当前时间：" + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("账户 ID: " + str(settings.ACCOUNT_ID))
print("日志目录：" + str(settings.LOG_DIR))
print("信号目录：" + str(settings.SIGNAL_DIR_INPUT))
print("")

# 提示用户确认
print("重要检查清单:")
print("   [ ] QMT交易终端已启动并登录")
print("   [ ] 网络连接正常")
print("   [ ] 账户资金充足")
print("   [ ] 交易时间正确（A 股交易日）")
print("")

response = raw_input("是否继续启动？(输入 y 或 yes 继续，其他键取消): ")
if response.lower() not in ['y', 'yes', '是']:
    print("\n启动已取消")
    raw_input("按回车键退出...")
    sys.exit(0)

print("")
print("="*70)
print("系统启动中...")
print("="*70)
print("")

try:
    # 初始化日志
    ensure_dirs()
    init_logger(settings.LOG_DIR)
    log = get_logger()
    
    print("日志系统初始化完成")
    print("")
    
    # 开始主循环
    print("进入交易主循环...")
    print("   - 按 Ctrl+C 可停止程序")
    print("   - 日志将同时输出到屏幕和文件")
    print("")
    print("-"*70)
    
    # 运行主循环
    main_loop()
    
except KeyboardInterrupt:
    print("")
    print("-"*70)
    print("")
    print("程序已安全停止")
    print("")
    
except Exception as e:
    print("")
    print("-"*70)
    print("")
    print("程序异常退出：" + str(e))
    print("")
    print("请检查:")
    print("1. QMT 连接状态")
    print("2. 网络是否正常")
    print("3. 查看日志文件获取详细错误信息")
    print("")
    raw_input("按回车键退出...")
    sys.exit(1)

else:
    print("")
    print("="*70)
    print("程序正常运行结束")
    print("="*70)
    raw_input("按回车键退出...")
