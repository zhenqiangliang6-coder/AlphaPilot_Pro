# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 日志记录模块
负责系统运行日志的记录和管理

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: V8.95 保守版
"""

import sys
import datetime
import os

class Logger:
    def __init__(self, log_dir):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        # 修复：使用 .format() 替代 f-string，兼容 Python 3.6
        self.log_file = os.path.join(log_dir, "run_{}.log".format(datetime.date.today()))

    def log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        full_msg = "[{}] {}".format(ts, str(msg))
        try:
            print(full_msg)
            sys.stdout.flush()
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(full_msg + "\n")
        except Exception:
            pass

# 全局实例 (将在 main.py 中初始化)
logger = None

def get_logger():
    return logger

def init_logger(log_dir):
    global logger
    logger = Logger(log_dir)
    return logger