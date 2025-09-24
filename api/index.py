import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_app import app

# Vercel需要这个变量来识别Flask应用
application = app

# 如果直接运行此文件
if __name__ == '__main__':
    app.run()
