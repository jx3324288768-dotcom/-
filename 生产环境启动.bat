@echo off
chcp 65001 >nul
echo 正在启动阳昶产量记录管理系统（生产环境）...
echo.

cd /d "%~dp0"

echo 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误：Python未安装或未添加到系统路径
    pause
    exit /b 1
)

echo.
echo 检查依赖包...
python -c "import flask; print('Flask已安装')" 2>nul
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
)

echo.
echo 检查gunicorn...
python -c "import gunicorn; print('gunicorn已安装')" 2>nul
if errorlevel 1 (
    echo 正在安装gunicorn...
    pip install gunicorn
)

echo.
echo 启动生产环境服务器...
echo 服务器地址：http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.

set FLASK_ENV=production
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 web_app:app

echo.
echo 服务器已停止
pause

