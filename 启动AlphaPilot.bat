@echo off
chcp 65001 >nul
REM ========================================
REM   AlphaPilot Pro - One-Click Start Script
REM   
REM   Author: Alphapilot Agent Team
REM   Members: 
REM     - Liang Ziyi (Guangdong University of Foreign Studies)
REM     - Hou Fengrui (Huizhou City Vocational College)
REM     - Liang Ruzhen (Beijing Technology and Business University)
REM   Contact: 497720537@qq.com | 13392077558
REM   Environment: Ruizhi Rongke Edition
REM ========================================
echo.
echo ========================================
echo   AlphaPilot Pro - One-Click Start
echo   Environment: XunTou Jisu Trading Terminal
echo ========================================
echo.

REM Switch to project directory
cd /d "D:\AlphaPilot_Pro"

REM Clean cache
echo [1/3] Cleaning Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc >nul 2>&1
echo Cache cleaned
echo.

REM Find QMT Python interpreter
echo [2/3] Detecting QMT Python environment...
set "QMT_BASE=D:\迅投极速交易终端 睿智融科版"
set "QMT_PYTHON="

REM Check if base directory exists
if not exist "%QMT_BASE%" (
    echo ERROR: QMT base directory not found!
    echo Path: %QMT_BASE%
    echo.
    pause
    exit /b 1
)

REM Try common paths for new environment
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

REM Verify xtquant module
echo [3/3] Verifying xtquant module...
"%QMT_PYTHON%" -c "import xtquant; print('xtquant module available')" 2>nul
if errorlevel 1 (
    echo ERROR: xtquant module not available!
    echo.
    echo Please ensure:
    echo 1. QMT trading terminal is logged in
    echo 2. Using QMT built-in Python interpreter
    echo 3. If needed, install xtquant:
    echo    "%QMT_PYTHON%" -m pip install xtquant
    echo.
    pause
    exit /b 1
)
echo.

echo ========================================
echo   Starting AlphaPilot Pro Strategy Engine
echo   Press Ctrl+C to stop
echo ========================================
echo.

REM Start main program
"%QMT_PYTHON%" main.py

echo.
echo ========================================
echo   Program exited
echo ========================================
pause
