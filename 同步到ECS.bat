@echo off
chcp 936 >nul
REM ====================================================
REM   AlphaPilot Pro 代码同步脚本
REM   用于将本地修复的代码上传到阿里云 ECS
REM   
REM   作者: Alphapilot智能体团队
REM   成员: 梁子羿 (广东外语外贸大学), 侯沣睿 (惠州城市职业学院), 梁茹真 (北京工商大学)
REM   联系: 497720537@qq.com | 13392077558
REM ====================================================
echo.

:: 配置区域（请根据实际情况修改）
set LOCAL_DIR=d:\AlphaPilot_Pro
set REMOTE_USER=你的ECS用户名
set REMOTE_IP=你的ECS公网IP
set REMOTE_DIR=C:\迅投QMT交易终端 华林证券模拟版\mpython

echo [1/4] 准备同步文件...
echo.

:: 创建临时打包目录
set TEMP_DIR=%LOCAL_DIR%\sync_temp
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

:: 复制需要同步的核心文件
xcopy "%LOCAL_DIR%\config\settings.py" "%TEMP_DIR%\config\" /Y /I >nul
xcopy "%LOCAL_DIR%\utils\logger.py" "%TEMP_DIR%\utils\" /Y /I >nul
xcopy "%LOCAL_DIR%\utils\helpers.py" "%TEMP_DIR%\utils\" /Y /I >nul
xcopy "%LOCAL_DIR%\core\trader_engine.py" "%TEMP_DIR%\core\" /Y /I >nul
xcopy "%LOCAL_DIR%\risk\stop_loss.py" "%TEMP_DIR%\risk\" /Y /I >nul
xcopy "%LOCAL_DIR%\strategies\*.py" "%TEMP_DIR%\strategies\" /Y /I >nul
xcopy "%LOCAL_DIR%\main.py" "%TEMP_DIR%\" /Y >nul

echo [√] 已打包以下文件：
echo    - config/settings.py
echo    - utils/logger.py
echo    - utils/helpers.py
echo    - core/trader_engine.py
echo    - risk/stop_loss.py
echo    - strategies/*.py
echo    - main.py
echo.

:: 压缩为 zip
echo [2/4] 压缩文件...
powershell -Command "Compress-Archive -Path '%TEMP_DIR%\*' -DestinationPath '%TEMP_DIR%\AlphaPilot_Update.zip' -Force" >nul
echo [√] 压缩完成
echo.

echo [3/4] 生成上传命令...
echo.
echo ====================================================
echo 请将以下命令复制到本地 CMD 执行（需要安装 WinSCP 或 OpenSSH）：
echo ====================================================
echo.
echo 方式 1：使用 scp（推荐，需要安装 OpenSSH）
echo scp "%TEMP_DIR%\AlphaPilot_Update.zip" %REMOTE_USER%@%REMOTE_IP%:C:\temp\
echo.
echo 方式 2：使用远程桌面直接复制
echo    1. 打开远程桌面连接
echo    2. 复制文件："%TEMP_DIR%\AlphaPilot_Update.zip"
echo    3. 粘贴到 ECS 的 C:\temp\ 目录
echo.
echo ====================================================
echo.

echo [4/4] 请在 ECS 上执行以下解压命令：
echo.
echo powershell -Command "Expand-Archive -Path 'C:\temp\AlphaPilot_Update.zip' -DestinationPath '%REMOTE_DIR%' -Force"
echo.

echo ====================================================
echo 同步准备完成！
echo 临时文件位置：%TEMP_DIR%\
echo ====================================================
echo.

pause
