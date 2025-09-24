@echo off
chcp 65001 >nul
echo 阳昶产量记录管理系统 - 问题诊断
echo =====================================
echo.

cd /d "%~dp0"

echo 1. 检查当前目录：
echo %CD%
echo.

echo 2. 检查Python版本：
python --version
if errorlevel 1 (
    echo ❌ Python未安装或未添加到系统路径
    echo 解决方案：请访问 https://www.python.org/downloads/ 下载安装Python
    echo 安装时请勾选 "Add Python to PATH"
) else (
    echo ✅ Python已正确安装
)
echo.

echo 3. 检查pip版本：
pip --version
if errorlevel 1 (
    echo ❌ pip未安装
) else (
    echo ✅ pip已正确安装
)
echo.

echo 4. 检查Flask是否安装：
python -c "import flask; print('✅ Flask版本:', flask.__version__)" 2>nul
if errorlevel 1 (
    echo ❌ Flask未安装
    echo 正在安装Flask...
    pip install flask flask-sqlalchemy python-dotenv
) else (
    echo ✅ Flask已安装
)
echo.

echo 5. 检查项目文件：
if exist "web_app.py" (
    echo ✅ web_app.py 存在
) else (
    echo ❌ web_app.py 不存在
)
echo.

if exist "requirements.txt" (
    echo ✅ requirements.txt 存在
) else (
    echo ❌ requirements.txt 不存在
)
echo.

echo 6. 尝试直接运行Python文件：
echo 正在测试运行web_app.py...
timeout /t 3 /nobreak >nul
python -c "import web_app; print('✅ web_app.py 可以正常导入')" 2>nul
if errorlevel 1 (
    echo ❌ web_app.py 导入失败
    echo 错误信息：
    python -c "import web_app" 2>&1
) else (
    echo ✅ web_app.py 可以正常导入
)
echo.

echo 诊断完成！
echo.
echo 如果所有检查都通过，请尝试以下方法启动：
echo 1. 双击 "启动网站.bat"
echo 2. 或在命令行中运行：python web_app.py
echo.

pause

