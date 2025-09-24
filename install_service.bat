@echo off
echo 正在安装阳昶产量记录管理系统为Windows服务...
echo.

REM 检查管理员权限
net session >nul 2>&1
if errorlevel 1 (
    echo 错误：需要管理员权限来安装服务
    echo 请右键点击此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

REM 获取当前目录
set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"

REM 创建服务安装脚本
echo 创建服务安装脚本...
(
echo import win32serviceutil
echo import win32service
echo import win32event
echo import servicemanager
echo import socket
echo import sys
echo import os
echo import subprocess
echo.
echo class ProductionService^(win32serviceutil.ServiceFramework^):
echo     _svc_name_ = "ProductionRecordSystem"
echo     _svc_display_name_ = "阳昶产量记录管理系统"
echo     _svc_description_ = "阳昶产量记录管理系统Web服务"
echo.
echo     def __init__^(self, args^):
echo         win32serviceutil.ServiceFramework.__init__^(self, args^)
echo         self.hWaitStop = win32event.CreateEvent^(None, 0, 0, None^)
echo         socket.setdefaulttimeout^(60^)
echo.
echo     def SvcStop^(self^):
echo         self.ReportServiceStatus^(win32service.SERVICE_STOP_PENDING^)
echo         win32event.SetEvent^(self.hWaitStop^)
echo.
echo     def SvcDoRun^(self^):
echo         servicemanager.LogMsg^(servicemanager.EVENTLOG_INFORMATION_TYPE,
echo                               servicemanager.PYS_SERVICE_STARTED,
echo                               ^(self._svc_name_, ''^)^)
echo         self.main^(^)
echo.
echo     def main^(self^):
echo         os.chdir^(r"%APP_DIR%"^)
echo         subprocess.run^(['python', 'web_app.py']^)
echo.
echo if __name__ == '__main__':
echo     win32serviceutil.HandleCommandLine^(ProductionService^)
) > service_installer.py

REM 安装pywin32
echo 安装Windows服务支持包...
pip install pywin32
if errorlevel 1 (
    echo 错误：pywin32安装失败
    pause
    exit /b 1
)

REM 安装服务
echo 安装服务...
python service_installer.py install
if errorlevel 1 (
    echo 错误：服务安装失败
    pause
    exit /b 1
)

REM 启动服务
echo 启动服务...
python service_installer.py start
if errorlevel 1 (
    echo 错误：服务启动失败
    pause
    exit /b 1
)

echo.
echo 服务安装成功！
echo 服务名称：阳昶产量记录管理系统
echo 访问地址：http://localhost:5000
echo.
echo 管理命令：
echo   启动服务：net start ProductionRecordSystem
echo   停止服务：net stop ProductionRecordSystem
echo   卸载服务：python service_installer.py remove
echo.

REM 清理临时文件
del service_installer.py

pause


