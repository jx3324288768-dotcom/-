@echo off
chcp 65001 >nul
echo 正在启动阳昶产量记录管理系统...
echo.

cd /d "%~dp0"

echo 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误：Python未安装或未添加到系统路径
    echo 请访问 https://www.python.org/downloads/ 下载安装Python
    pause
    exit /b 1
)

echo.
echo 检查依赖包...
python -c "import flask; print('Flask已安装')" 2>nul
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误：依赖包安装失败
        pause
        exit /b 1
    )
)

echo.
echo 启动Web服务器（开发环境）...
echo 服务器地址：http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.
echo ⚠️  注意：这是开发环境，适合测试和开发使用
echo    如需生产环境，请使用 "生产环境启动.bat"
echo.

python web_app.py

echo.
echo 服务器已停止
pause
