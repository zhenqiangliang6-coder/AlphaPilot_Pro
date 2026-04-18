@echo off
chcp 936 >nul
setlocal
title AlphaPilot - 监听启动器

REM ==========================================
REM   AlphaPilot Pro - 信号监听启动脚本
REM   
REM   作者: Alphapilot智能体团队
REM   成员: 梁子羿 (广东外语外贸大学), 侯沣睿 (惠州城市职业学院), 梁茹真 (北京工商大学)
REM   联系: 497720537@qq.com | 13392077558
REM ==========================================

REM ==========================================
REM 1. 定义监听目录
REM ==========================================
set "SIGNAL_SCRIPT=C:\Users\Administrator\Desktop\ESC"

REM ==========================================
REM 2. 启动监听程序
REM ==========================================
echo [系统] 正在启动 AlphaPilot 信号监听...
if exist "%SIGNAL_SCRIPT%\listener.py" (
    start "AlphaPilot 信号监听" python "%SIGNAL_SCRIPT%\listener.py"
    echo [系统] 监听程序已启动。
) else (
    echo [错误] 未找到 listener.py，请检查路径。
    pause
    exit /b
)

REM ==========================================
REM 3. 任务完成，自动关闭当前窗口
REM ==========================================
exit