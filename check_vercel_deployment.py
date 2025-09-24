#!/usr/bin/env python3
"""
Vercel部署检查脚本
检查项目是否准备好部署到Vercel
"""

import os
import sys

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (缺失)")
        return False

def check_vercel_readiness():
    """检查Vercel部署准备情况"""
    print("🔍 检查Vercel部署准备情况...")
    print("=" * 50)
    
    required_files = [
        ("vercel.json", "Vercel配置文件"),
        ("api/index.py", "Vercel入口文件"),
        ("web_app.py", "Flask主应用"),
        ("requirements.txt", "Python依赖文件"),
        ("static/", "静态文件目录"),
        ("templates/", "模板文件目录")
    ]
    
    all_good = True
    
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_good = False
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("🎉 所有必需文件都存在！")
        print("✅ 项目已准备好部署到Vercel")
    else:
        print("⚠️  缺少必需文件，请先创建缺失的文件")
        print("❌ 项目尚未准备好部署到Vercel")
    
    print("\n📋 部署步骤：")
    print("1. 提交所有更改到GitHub")
    print("2. 在Vercel上连接GitHub仓库")
    print("3. 设置环境变量：FLASK_ENV=production")
    print("4. 部署项目")
    
    return all_good

if __name__ == "__main__":
    check_vercel_readiness()
