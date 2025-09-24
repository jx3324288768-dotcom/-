@echo off
echo 正在设置文件权限...
echo.

REM 设置批处理文件权限
echo 设置启动脚本权限...
icacls start_server.bat /grant Everyone:F >nul 2>&1
icacls install_service.bat /grant Everyone:F >nul 2>&1
icacls create_desktop_shortcut.bat /grant Everyone:F >nul 2>&1

echo ✅ 权限设置完成！
echo.
echo 现在您可以：
echo 1. 双击 start_server.bat 启动系统
echo 2. 双击 create_desktop_shortcut.bat 创建桌面快捷方式
echo 3. 双击 install_service.bat 安装为系统服务
echo.

pause


