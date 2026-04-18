@echo off
chcp 936 >nul
setlocal
title AlphaPilot - QMT启动器

REM ==========================================
REM   AlphaPilot Pro - QMT启动脚本
REM   
REM   作者: Alphapilot智能体团队
REM   成员: 梁子羿 (广东外语外贸大学), 侯沣睿 (惠州城市职业学院), 梁茹真 (北京工商大学)
REM   联系: 497720537@qq.com | 13392077558
REM ==========================================

REM ==========================================
REM 1. 定义QMT路径
REM ==========================================
set "QMT_ROOT=C:\迅投QMT交易终端 华林证券模拟版"

REM ==========================================
REM 2. 启动 QMT 交易核心
REM ==========================================
echo [系统] 正在唤醒 QMT 交易终端核心...
if exist "%QMT_ROOT%\bin.x64\XtItClient.exe" (
    start "" "%QMT_ROOT%\bin.x64\XtItClient.exe"
    echo [系统] QMT 启动命令已发送。
) else (
    echo [错误] 未找到 QMT 启动程序！
    pause
    exit /b
)

REM ==========================================
REM 3. 智能等待：确保QMT完全就绪
REM ==========================================
echo [系统] 正在等待 QMT 进程完全启动...
echo [系统] (第一阶段：强制等待 60 秒，确保核心与接口完全加载)
timeout /t 60 /nobreak >nul

set "QMT_PROCESS_NAME=XtItClient.exe"
set "MAX_WAIT_SECONDS=30"
set "ELAPSED_SECONDS=0"

:wait_for_qmt
timeout /t 1 /nobreak >nul
set /a ELAPSED_SECONDS+=1

REM 【心跳反馈】每等待5秒，显示一次状态
set /a "HEARTBEAT=%ELAPSED_SECONDS% %% 5"
if %HEARTBEAT%==0 (
    echo [系统] (第二阶段：智能探测中...) 已等待 %ELAPSED_SECONDS% 秒
)

tasklist /FI "IMAGENAME eq %QMT_PROCESS_NAME%" 2>NUL | find /I /N "%QMT_PROCESS_NAME%">NUL
if "%ERRORLEVEL%"=="0" (
    echo [系统] 监测到 QMT 进程运行稳定 (共耗时 %ELAPSED_SECONDS% 秒)。
    goto qmt_started
)

if %ELAPSED_SECONDS% LSS %MAX_WAIT_SECONDS% (
    goto wait_for_qmt
)

echo [警告] 等待 QMT 启动超时，但将继续执行。

:qmt_started
REM 进程稳定后，再给它 10 秒完成最后的接口初始化
echo [系统] QMT 已就绪，正在等待交易接口初始化 (10秒缓冲期)...
timeout /t 10 /nobreak >nul
echo [系统] 缓冲结束，交易接口应已就绪。
echo ==========================================
echo [系统] QMT 启动完成！
echo ==========================================
pause