@echo off
chcp 936 >nul
REM ========================================
REM   AlphaPilot Pro - QMT Python 环境检测工具
REM   
REM   作者: Alphapilot智能体团队
REM   成员: 梁子羿 (广东外语外贸大学), 侯沣睿 (惠州城市职业学院), 梁茹真 (北京工商大学)
REM   联系: 497720537@qq.com | 13392077558
REM ========================================
echo.
echo ========================================
echo   QMT Python 环境检测工具
echo ========================================
echo.

set "FOUND=0"

REM 检查常见路径
echo 正在搜索 QMT Python 解释器...
echo.

if exist "D:\迅投QMT交易终端 华林证券模拟版\python\python.exe" (
    echo ✅ 找到: D:\迅投QMT交易终端 华林证券模拟版\python\python.exe
    set "QMT_PYTHON=D:\迅投QMT交易终端 华林证券模拟版\python\python.exe"
    set "FOUND=1"
)

if exist "D:\迅投QMT交易终端 华林证券模拟版\bin.x64\python.exe" (
    echo ✅ 找到: D:\迅投QMT交易终端 华林证券模拟版\bin.x64\python.exe
    if "%FOUND%"=="0" set "QMT_PYTHON=D:\迅投QMT交易终端 华林证券模拟版\bin.x64\python.exe"
    set "FOUND=1"
)

if exist "C:\Program Files\国金证券QMT交易端\python\python.exe" (
    echo ✅ 找到: C:\Program Files\国金证券QMT交易端\python\python.exe
    if "%FOUND%"=="0" set "QMT_PYTHON=C:\Program Files\国金证券QMT交易端\python\python.exe"
    set "FOUND=1"
)

echo.
if "%FOUND%"=="0" (
    echo ❌ 未找到 QMT Python 解释器
    echo.
    echo 请手动查找以下位置：
    echo   1. QMT 安装目录下的 python 文件夹
    echo   2. QMT 安装目录下的 bin.x64 文件夹
    echo   3. 查看是否有 python.exe 或 python3.exe
    echo.
) else (
    echo ========================================
    echo   验证 xtquant 模块
    echo ========================================
    echo.
    "%QMT_PYTHON%" -c "import sys; print('Python 版本:', sys.version); import xtquant; print('✅ xtquant 模块可用')"
    if errorlevel 1 (
        echo.
        echo ⚠️  xtquant 模块不可用，可能需要启动 QMT 客户端
    )
)

echo.
echo ========================================
pause