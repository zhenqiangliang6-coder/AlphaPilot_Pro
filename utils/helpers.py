# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 辅助工具函数模块
提供时间判断、大盘数据获取等通用功能

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: V8.95 保守版
"""

import os
import math
import datetime
from xtquant import xtdata
from config import settings
from utils.logger import get_logger

# 修复：移除模块级别的 logger 获取

def ensure_dirs():
    """确保所有必要目录存在 (包括桌面的信号目录)"""
    log = get_logger()  # 动态获取
    
    dirs = [
        settings.DATA_DIR, 
        settings.LOG_DIR, 
        settings.SIGNAL_DIR_INPUT, 
        settings.SIGNAL_DIR_PROCESSED
    ]
    for d in dirs:
        if not os.path.exists(d):
            try:
                os.makedirs(d)
                if log: log.log("[初始化] 创建目录：{}".format(d))
            except Exception as e:
                if log: log.log("[错误] 创建目录失败 {}: {}".format(d, e))

def is_auction_time(time_str):
    """集合竞价时间：09:15-09:25"""
    return "0915" <= time_str <= "0925"

def is_silent_time(time_str):
    """静默期：09:25-09:30（不进行交易）"""
    return "0925" < time_str < "0930"

def is_trading_time(time_str):
    """判断是否在交易时间内"""
    return ("0930" <= time_str <= "1130") or ("1300" <= time_str <= "2000")

def is_after_take_profit_start(time_str):
    """
    判断是否已过动态止盈启动时间。
    根据 QMT 对接实战总结，动态止盈默认在 09:50 后开始执行，以避开开盘剧烈波动。
    :param time_str: 格式为 HHMM 的字符串
    :return: True/False
    """
    try:
        return int(time_str) >= settings.EARLIEST_EXECUTION_TIME
    except Exception:
        return False

def get_index_change_percent():
    """获取上证指数涨跌幅 (供策略层调用)"""
    log = get_logger()
    
    index_code = "000001.SH"
    try:
        # 【关键修复】强制订阅以维持行情连接，防止因网络微动或超时导致的静默断开
        # 即使已订阅，重复调用也无副作用，但能有效刷新 QMT 内部状态
        xtdata.subscribe_whole_quote([index_code])
        
        tick_data = xtdata.get_full_tick([index_code])
        if not tick_data or index_code not in tick_data:
            log.log("[数据] 未获取到大盘数据")
            return None
        
        data = tick_data[index_code]
        current_price = data.get("lastPrice", 0.0)
        open_price = data.get("open", 0.0)
        
        if current_price <= 0 or open_price <= 0:
            log.log("[数据] 大盘价格无效：curr={}, open={}".format(current_price, open_price))
            return None
            
        change_pct = (current_price - open_price) / open_price * 100.0
        
        if not math.isfinite(change_pct):
            log.log("[数据] 大盘涨跌幅异常：{}".format(change_pct))
            return None
            
        return round(change_pct, 2)
    except Exception as e:
        if log: 
            log.log("[数据] 获取大盘指数失败：{}".format(e))
        return None


def is_weekend(date_str):
    """
    判断日期是否为周末
    
    Args:
        date_str: 日期字符串 (YYYY-MM-DD) 或 datetime 对象
    
    Returns:
        bool: True=周末，False=交易日
    """
    try:
        if isinstance(date_str, str):
            dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        else:
            dt = date_str
        
        return dt.weekday() >= 5  # 5=周六，6=周日
    except Exception:
        return False


def add_trading_days(start_date, days):
    """
    计算 N 个交易日后的日期（跳过周末）
    
    Args:
        start_date: 起始日期 (datetime 或 YYYY-MM-DD 字符串)
        days: 要增加的天数
    
    Returns:
        str: 目标日期 (YYYY-MM-DD)
    """
    log = get_logger()  # 动态获取
    
    try:
        if isinstance(start_date, str):
            dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        else:
            dt = start_date
        
        remaining_days = days
        while remaining_days > 0:
            dt += datetime.timedelta(days=1)
            # 跳过周末
            if dt.weekday() < 5:  # 周一到周五
                remaining_days -= 1
        
        return dt.strftime('%Y-%m-%d')
    except Exception as e:
        if log:
            log.log("[工具] 计算交易日失败：{}".format(e))
        # 简单加法作为后备
        if isinstance(start_date, str):
            dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        else:
            dt = start_date
        result = dt + datetime.timedelta(days=days)
        return result.strftime('%Y-%m-%d')