#!/usr/bin/env python3
"""
测试Vercel应用是否正常工作
"""

import sys
import os

# 添加api目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

def test_imports():
    """测试导入是否正常"""
    print("🔍 测试导入...")
    
    try:
        from api.vercel_app import app, db, ProductionRecord
        print("✅ 成功导入vercel_app")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_app_creation():
    """测试应用创建"""
    print("🔍 测试应用创建...")
    
    try:
        from api.vercel_app import app
        print(f"✅ 应用创建成功: {app}")
        return True
    except Exception as e:
        print(f"❌ 应用创建失败: {e}")
        return False

def test_database():
    """测试数据库"""
    print("🔍 测试数据库...")
    
    try:
        from api.vercel_app import app, db, ProductionRecord
        
        with app.app_context():
            # 测试数据库连接
            count = ProductionRecord.query.count()
            print(f"✅ 数据库连接成功，记录数: {count}")
            return True
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_routes():
    """测试路由"""
    print("🔍 测试路由...")
    
    try:
        from api.vercel_app import app
        
        with app.test_client() as client:
            # 测试主页
            response = client.get('/')
            if response.status_code == 200:
                print("✅ 主页路由正常")
            else:
                print(f"❌ 主页路由失败: {response.status_code}")
                return False
            
            # 测试API路由
            response = client.get('/api/records')
            if response.status_code == 200:
                print("✅ API路由正常")
            else:
                print(f"❌ API路由失败: {response.status_code}")
                return False
            
            return True
    except Exception as e:
        print(f"❌ 路由测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试Vercel应用...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_app_creation,
        test_database,
        test_routes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！应用已准备好部署到Vercel")
    else:
        print("⚠️  部分测试失败，请检查错误信息")
    
    return passed == total

if __name__ == "__main__":
    main()
