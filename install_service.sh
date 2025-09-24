#!/bin/bash

echo "正在安装阳昶产量记录管理系统为Linux系统服务..."
echo

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo "错误：需要root权限来安装服务"
    echo "请使用：sudo $0"
    exit 1
fi

# 获取当前目录
APP_DIR=$(pwd)
APP_USER=$(whoami)

# 创建服务文件
echo "创建系统服务文件..."
cat > /etc/systemd/system/production-system.service << EOF
[Unit]
Description=阳昶产量记录管理系统
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/python3 $APP_DIR/web_app.py
Restart=always
RestartSec=10
Environment=FLASK_ENV=production

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
echo "重新加载系统服务配置..."
systemctl daemon-reload

# 启用服务
echo "启用服务..."
systemctl enable production-system.service

# 启动服务
echo "启动服务..."
systemctl start production-system.service

# 检查服务状态
echo "检查服务状态..."
systemctl status production-system.service --no-pager

echo
echo "服务安装成功！"
echo "服务名称：production-system"
echo "访问地址：http://localhost:5000"
echo
echo "管理命令："
echo "  启动服务：sudo systemctl start production-system"
echo "  停止服务：sudo systemctl stop production-system"
echo "  重启服务：sudo systemctl restart production-system"
echo "  查看状态：sudo systemctl status production-system"
echo "  查看日志：sudo journalctl -u production-system -f"
echo "  卸载服务：sudo systemctl disable production-system && sudo rm /etc/systemd/system/production-system.service"
echo


