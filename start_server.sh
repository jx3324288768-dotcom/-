#!/bin/bash

echo "正在启动阳昶产量记录管理系统..."
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3，请先安装Python 3.7+"
    exit 1
fi

# 检查依赖是否安装
echo "检查依赖包..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "正在安装依赖包..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "错误：依赖包安装失败"
        exit 1
    fi
fi

# 启动服务器
echo "启动Web服务器..."
echo "服务器地址：http://localhost:5000"
echo "按 Ctrl+C 停止服务器"
echo

python3 web_app.py


