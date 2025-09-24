@echo off
echo 正在创建桌面快捷方式...
echo.

REM 获取当前目录
set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"

REM 获取桌面路径
for /f "tokens=2*" %%a in ('reg query "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop 2^>nul') do set "DESKTOP=%%b"

if "%DESKTOP%"=="" (
    echo 错误：无法获取桌面路径
    pause
    exit /b 1
)

REM 创建快捷方式
echo 创建启动快捷方式...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\阳昶产量记录系统.lnk'); $Shortcut.TargetPath = '%APP_DIR%\start_server.bat'; $Shortcut.WorkingDirectory = '%APP_DIR%'; $Shortcut.Description = '阳昶产量记录管理系统'; $Shortcut.Save()"

if exist "%DESKTOP%\阳昶产量记录系统.lnk" (
    echo ✅ 桌面快捷方式创建成功！
    echo 📁 位置：%DESKTOP%\阳昶产量记录系统.lnk
) else (
    echo ❌ 桌面快捷方式创建失败
)

echo.
echo 现在您可以通过以下方式启动系统：
echo 1. 双击桌面上的"阳昶产量记录系统"快捷方式
echo 2. 双击 start_server.bat 文件
echo 3. 在命令行中运行：python web_app.py
echo.

pause


