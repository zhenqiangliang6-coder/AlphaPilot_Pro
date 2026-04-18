@echo off
chcp 65001 >nul
title AlphaPilot Pro - QMT Strategy Launcher

REM ========================================
REM   AlphaPilot Pro - Main Strategy Script
REM   
REM   Author: Alphapilot Agent Team
REM   Members: 
REM     - Liang Ziyi (Guangdong University of Foreign Studies)
REM     - Hou Fengrui (Huizhou City Vocational College)
REM     - Liang Ruzhen (Beijing Technology and Business University)
REM   Contact: 497720537@qq.com | 13392077558
REM   Environment: Ruizhi Rongke Edition
REM ========================================

echo ========================================
echo   AlphaPilot Pro is preparing to start...
echo   Environment: XunTou Jisu Trading Terminal
echo ========================================

REM 1. Switch to project directory
cd /d "D:\AlphaPilot_Pro"

REM 2. Clean all cache files
echo [System] Cleaning Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc >nul 2>&1

REM 3. Find and start QMT Python interpreter
echo [System] Detecting QMT Python environment...
set "QMT_BASE=D:\迅投极速交易终端 睿智融科版"
set "QMT_PYTHON="

REM Check if base directory exists
if not exist "%QMT_BASE%" (
    echo ERROR: QMT base directory not found!
    echo Path: %QMT_BASE%
    pause
    exit /b 1
)

REM Try Python paths for new environment
if exist "%QMT_BASE%\bin.x64\python.exe" (
    set "QMT_PYTHON=%QMT_BASE%\bin.x64\python.exe"
) else if exist "%QMT_BASE%\bin.x64\pythonw.exe" (
    set "QMT_PYTHON=%QMT_BASE%\bin.x64\pythonw.exe"
) else if exist "%QMT_BASE%\mpython\python.exe" (
    set "QMT_PYTHON=%QMT_BASE%\mpython\python.exe"
)

if "%QMT_PYTHON%"=="" (
    echo ERROR: QMT Python interpreter not found!
    echo.
    echo Please check the following paths:
    echo   - %QMT_BASE%\bin.x64\python.exe
    echo   - %QMT_BASE%\bin.x64\pythonw.exe
    echo   - %QMT_BASE%\mpython\python.exe
    echo.
    pause
    exit /b 1
)

echo Found QMT Python: %QMT_PYTHON%
echo.

REM 4. Verify xtquant module
echo [System] Verifying xtquant module...
"%QMT_PYTHON%" -c "import xtquant; print('xtquant module available')" 2>nul
if errorlevel 1 (
    echo ERROR: xtquant module not available!
    echo.
    echo Please ensure:
    echo 1. QMT trading terminal is logged in
    echo 2. Using QMT built-in Python interpreter
    echo.
    pause
    exit /b 1
)
echo.

REM 5. Start main program
echo [System] Starting AlphaPilot Pro core engine...
echo ----------------------------------------
"%QMT_PYTHON%" main.py

pause
