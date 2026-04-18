@echo off
chcp 65001 >nul
title AlphaPilot Pro - Environment Check Tool (Ruizhi Rongke Edition)

REM ========================================
REM   AlphaPilot Pro - Environment Check Script
REM   
REM   Author: Alphapilot Agent Team
REM   Version: V8.95 Conservative Edition
REM   Date: 2026-04-15
REM   Environment: Ruizhi Rongke Edition
REM ========================================

echo ========================================
echo   AlphaPilot Pro Environment Check Tool
echo   Environment: XunTou Jisu Trading Terminal
echo ========================================
echo.

REM Switch to project directory
cd /d "D:\AlphaPilot_Pro"

REM Find QMT Python interpreter
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

REM Try Python paths for new environment (by priority)
if exist "%QMT_BASE%\bin.x64\python.exe" (
    set "QMT_PYTHON=%QMT_BASE%\bin.x64\python.exe"
) else if exist "%QMT_BASE%\bin.x64\pythonw.exe" (
    set "QMT_PYTHON=%QMT_BASE%\bin.x64\pythonw.exe"
) else if exist "%QMT_BASE%\mpython\python.exe" (
    set "QMT_PYTHON=%QMT_BASE%\mpython\python.exe"
) else if exist "%QMT_BASE%\python\python.exe" (
    set "QMT_PYTHON=%QMT_BASE%\python\python.exe"
)

if "%QMT_PYTHON%"=="" (
    echo ERROR: QMT Python interpreter not found!
    echo.
    echo Please check the following paths:
    echo   - %QMT_BASE%\bin.x64\python.exe
    echo   - %QMT_BASE%\bin.x64\pythonw.exe
    echo   - %QMT_BASE%\mpython\python.exe
    echo   - %QMT_BASE%\python\python.exe
    echo.
    pause
    exit /b 1
)

echo Found QMT Python: %QMT_PYTHON%
echo.

REM Run environment check script
echo ========================================
echo   Starting environment check...
echo ========================================
echo.

"%QMT_PYTHON%" 检测环境_睿智融科版.py

pause
