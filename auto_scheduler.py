# -*- coding: utf-8 -*-
"""
AlphaPilot Pro 自動化調度器
功能：每個交易日早上 8:30 自動按順序執行三個啟動腳本

作者: Alphapilot智能体团队
成员: 
  - 梁子羿 (广东外语外贸大学数字运营系人工智能)
  - 侯沣睿 (惠州城市职业学院大数据筛选)
  - 梁茹真 (北京工商大学)
联系: 497720537@qq.com | 13392077558
版本: 1.0 (優化兼容性)
"""

import os
import sys
import time
import subprocess
import datetime
import logging
import traceback

# ==========================================
# 配置區域（可根據需要修改）
# ==========================================

# 【沙盒測試】已禁用 - 生產環境配置
# SCHEDULE_HOUR = 18
# SCHEDULE_MINUTE = 30

# 正常生產環境配置
SCHEDULE_HOUR = 8
SCHEDULE_MINUTE = 55

# 專案根目錄
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# 三個啟動腳本的路徑
BAT_FILES = [
    os.path.join(PROJECT_DIR, "1_启动QMT.bat"),
    os.path.join(PROJECT_DIR, "2_启动监听.bat"),
    os.path.join(PROJECT_DIR, "3_AlphaPilot.bat"),
]

# 日誌檔案路徑
LOG_FILE = os.path.join(PROJECT_DIR, "logs", "auto_scheduler.log")

# 檢查間隔（秒）：每 30 秒檢查一次是否到達執行時間
CHECK_INTERVAL = 30

# ==========================================
# 日誌配置
# ==========================================

def setup_logger():
    """配置日誌系統"""
    # 確保日誌目錄存在
    log_dir = os.path.join(PROJECT_DIR, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 創建 logger
    logger = logging.getLogger("AutoScheduler")
    logger.setLevel(logging.INFO)
    
    # 檔案處理器
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# ==========================================
# 核心功能函數
# ==========================================

def is_weekday():
    """
    判斷今天是否是工作日（週一到週五）
    
    【沙盒測試】已禁用 - 恢復生產環境配置
    """
    today = datetime.datetime.now().weekday()  # 0=週一, 6=週日
    
    # 【沙盒測試】已禁用 - 恢復生產環境配置
    # return True  # 測試模式：不限制工作日
    
    # 正常生產環境配置
    return today < 5  # 0-4 是工作日

def is_time_to_run():
    """判斷當前時間是否到達執行時間"""
    now = datetime.datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    # 判斷是否到達或超過目標時間
    if current_hour > SCHEDULE_HOUR:
        return True
    elif current_hour == SCHEDULE_HOUR and current_minute >= SCHEDULE_MINUTE:
        return True
    else:
        return False

def get_next_run_time():
    """計算下次執行時間"""
    now = datetime.datetime.now()
    target_time = now.replace(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE, second=0, microsecond=0)
    
    # 如果今天已經過了執行時間，或者今天是週末，則計算明天的時間
    # 注意：這裡的 is_weekday() 在測試模式下永遠返回 True，所以只會判斷時間
    if now >= target_time: # or not is_weekday(): 
        # 找到下一個工作日
        days_ahead = 1
        while True:
            next_day = now + datetime.timedelta(days=days_ahead)
            # 在測試模式下，每天都算工作日，所以直接使用
            # 正常模式下，只選 0-4 (週一到週五)
            if is_weekday() or next_day.weekday() < 5: 
                target_time = next_day.replace(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE, second=0, microsecond=0)
                break
            days_ahead += 1
    
    return target_time

def execute_bat_file(bat_path, logger):
    """
    執行單個 BAT 檔案
    
    參數：
    - bat_path: BAT 檔案的完整路徑
    - logger: 日誌記錄器
    
    返回：
    - True: 執行成功
    - False: 執行失敗
    """
    if not os.path.exists(bat_path):
        logger.error("[錯誤] 檔案不存在: {}".format(bat_path))
        return False
    
    try:
        logger.info("[執行] 正在運行: {}".format(os.path.basename(bat_path)))
        
        # 使用 subprocess 執行 BAT 檔案
        # creationflags=0x08000000 表示 CREATE_NO_WINDOW，隱藏視窗
        process = subprocess.Popen(
            bat_path,
            cwd=os.path.dirname(bat_path),
            #  creationflags=0x08000000, # Windows 專用：不顯示視窗
            shell=True # 確保 .bat 檔案能被正確解析
        )
        
        logger.info("[成功] {} 已啟動 (PID: {})".format(
            os.path.basename(bat_path), process.pid
        ))
        
        return True
        
    except Exception as e:
        logger.error("[錯誤] 執行 {} 失敗: {}".format(
            os.path.basename(bat_path), str(e)
        ))
        return False

def execute_all_scripts(logger):
    """
    按順序執行所有啟動腳本
    
    參數：
    - logger: 日誌記錄器
    """
    logger.info("=" * 30)
    logger.info("[調度] 開始執行 AlphaPilot Pro 啟動序列")
    logger.info("=" * 30)
    
    success_count = 0
    total_count = len(BAT_FILES)
    
    for i, bat_path in enumerate(BAT_FILES, 1):
        logger.info("[步驟 {}/{}] 處理: {}".format(i, total_count, os.path.basename(bat_path)))
        
        if execute_bat_file(bat_path, logger):
            success_count += 1
            
            # 【核心優化】每個腳本執行後等待 90 秒，確保功能完全啟動和就緒
            # 原因：
            # 1. QMT 啟動需要時間加載交易介面和行情數據
            # 2. 訊號監聽模組需要建立連接並開始監聽
            # 3. 主策略需要初始化所有模組並建立穩定連接
            if i < total_count:  # 最後一個腳本不需要等待
                logger.info("[等待] {} 已啟動，等待 60 秒確保完全就緒...".format(
                    os.path.basename(bat_path)
                ))
                
                # 倒數計時顯示（每 10 秒更新一次）
                for remaining in range(50, 0, -10):
                    time.sleep(10)
                    logger.info("[等待] 還剩 {} 秒...".format(remaining))
                
                logger.info("[就緒] {} 功能已完全啟動，繼續下一步".format(
                    os.path.basename(bat_path)
                ))
        else:
            logger.warning("[警告] {} 執行失敗，繼續下一步".format(
                os.path.basename(bat_path)
            ))
    
    logger.info("=" * 60)
    logger.info("[完成] 啟動序列執行完畢 (成功: {}/{})".format(success_count, total_count))
    logger.info("=" * 60)

def wait_until_next_run(logger):
    """
    等待到下次執行時間
    
    參數：
    - logger: 日誌記錄器
    """
    next_run = get_next_run_time()
    now = datetime.datetime.now()
    wait_seconds = (next_run - now).total_seconds()
    
    if wait_seconds > 0:
        logger.info("[等待] 下次執行時間: {}".format(next_run.strftime('%Y-%m-%d %H:%M:%S')))
        logger.info("[等待] 剩餘時間: {:.1f} 小時 ({:.0f} 秒)".format(
            wait_seconds / 3600, wait_seconds
        ))
        
        # 倒數計時顯示（每分鐘更新一次）
        remaining = int(wait_seconds)
        while remaining > 0:
            sleep_time = min(60, remaining)
            time.sleep(sleep_time)
            remaining -= sleep_time
            
            # 每 5 分鐘顯示一次剩余時間
            if remaining % 300 == 0 and remaining > 0:
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                logger.info("[等待] 還剩 {} 小時 {} 分鐘".format(hours, minutes))
    else:
        logger.warning("[警告] 計算出的等待時間為負數，立即執行")

def main():
    """主函數：自動化調度器入口"""
    # 初始化日誌
    logger = setup_logger()
    
    logger.info("=" * 60)
    logger.info("AlphaPilot Pro 自動化調度器 v1.0")
    logger.info("啟動時間: {}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    logger.info("計劃執行時間: 每個工作日 {}:{}".format(SCHEDULE_HOUR, SCHEDULE_MINUTE))
    logger.info("=" * 60)
    
    # 驗證 BAT 檔案是否存在
    logger.info("[檢查] 驗證啟動腳本...")
    all_exist = True
    for bat_path in BAT_FILES:
        if os.path.exists(bat_path):
            logger.info("[正常] 找到: {}".format(os.path.basename(bat_path)))
        else:
            logger.error("[錯誤] 缺失: {}".format(bat_path))
            all_exist = False
    
    if not all_exist:
        logger.error("[致命] 部分啟動腳本缺失，請檢查檔案路徑")
        logger.error("[提示] 按任意鍵退出...")
        input()  # Python 3 兼容 (原 raw_input)
        sys.exit(1)
    
    logger.info("[正常] 所有啟動腳本驗證通過")
    
    # 主迴圈
    while True:
        try:
            # 檢查今天是否是工作日
            if not is_weekday():
                next_run = get_next_run_time()
                logger.info("[跳過] 今天是週末，下次執行: {}".format(
                    next_run.strftime('%Y-%m-%d %H:%M:%S')
                ))
                wait_until_next_run(logger)
                continue
            
            # 檢查是否到達執行時間
            if is_time_to_run():
                logger.info("[觸發] 到達執行時間，開始啟動序列")
                execute_all_scripts(logger)
                
                # 執行完成後，等待到明天的執行時間
                logger.info("[完成] 今日任務已完成，等待明天...")
                wait_until_next_run(logger)
            else:
                # 還未到達執行時間，繼續等待
                wait_until_next_run(logger)
                
        except KeyboardInterrupt:
            logger.info("[中斷] 使用者按下 Ctrl+C，調度器停止")
            break
        except Exception as e:
            logger.error("[異常] 發生未知錯誤: {}".format(str(e)))
            logger.error("[異常] 錯誤詳情: {}".format(traceback.format_exc()))
            logger.info("[恢復] 60 秒後重試...")
            time.sleep(60)
    
    logger.info("[退出] 調度器已停止")

if __name__ == "__main__":
    main()