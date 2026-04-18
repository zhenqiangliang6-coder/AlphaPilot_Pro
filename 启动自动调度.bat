@echo off
chcp 936 >nul
setlocal
title AlphaPilot Pro - Auto Scheduler (Py3.11)

REM ========================================
REM   AlphaPilot Pro 自动化调度器启动脚本
REM   
REM   作者: Alphapilot智能体团队
REM   成员: 梁子羿 (广东外语外贸大学), 侯沣睿 (惠州城市职业学院), 梁茹真 (北京工商大学)
REM   联系: 497720537@qq.com | 13392077558
REM ========================================

echo ========================================
echo   AlphaPilot Pro 自动化调度器
echo   运行环境: Python 3.11
echo   目标目录: Desktop\ESC
echo ========================================
echo.

REM 1. 定义 Python 3.11 路径 (根据刚才查询结果填入)
set "MY_PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe"

REM 2. 定义调度器脚本路径 (桌面 ESC 目录)
set "SCHEDULER_SCRIPT=C:\Users\Administrator\Desktop\ESC\auto_scheduler.py"

REM 3. 检查文件是否存在
if not exist "%SCHEDULER_SCRIPT%" (
    echo [错误] 找不到调度器脚本！
    echo [路径] %SCHEDULER_SCRIPT%
    pause
    exit /b
)

echo [系统] 正在启动自动化调度器...
echo [提示] 准备加载 auto_scheduler.py
echo.

REM 4. 启动调度器
"%MY_PYTHON%" "%SCHEDULER_SCRIPT%"

pause