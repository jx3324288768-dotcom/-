@echo off
echo 正在启动阳昶产量记录管理系统...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖包...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误：依赖包安装失败
        pause
        exit /b 1
    )
)

REM 启动服务器
echo 启动Web服务器...
echo 服务器地址：http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.

python web_app.py

pause


