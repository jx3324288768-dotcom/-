@echo off
echo 正在清理文件以准备Vercel部署...
echo.

REM 删除Windows批处理文件
echo 删除Windows批处理文件...
del "启动网站.bat" 2>nul
del "生产环境启动.bat" 2>nul
del "create_desktop_shortcut.bat" 2>nul
del "install_service.bat" 2>nul
del "setup_permissions.bat" 2>nul
del "诊断问题.bat" 2>nul
del "start_server.bat" 2>nul

REM 删除Linux脚本文件
echo 删除Linux脚本文件...
del "start_server.sh" 2>nul
del "install_service.sh" 2>nul

REM 删除本地配置文件
echo 删除本地配置文件...
del "pyrightconfig.json" 2>nul
rmdir /s /q ".vscode" 2>nul

REM 删除本地数据文件
echo 删除本地数据文件...
del "app_state.json" 2>nul
del "employees.json" 2>nul
del "records.csv" 2>nul
rmdir /s /q "instance" 2>nul
rmdir /s /q "__pycache__" 2>nul

REM 删除说明文档（可选）
echo 删除说明文档...
del "启动说明.md" 2>nul
del "环境说明.md" 2>nul
del "解决导入错误.md" 2>nul
del "GitHub推送指南.md" 2>nul

echo.
echo ✅ 清理完成！
echo.
echo 保留的核心文件：
echo - web_app.py (主应用)
echo - config.py (配置)
echo - requirements.txt (依赖)
echo - vercel.json (Vercel配置)
echo - api/index.py (Vercel入口)
echo - static/ (静态文件)
echo - templates/ (模板文件)
echo - README.md (说明文档)
echo.
echo 现在可以推送到GitHub并部署到Vercel了！
pause
