# 阳昶产量记录管理系统 - 部署指南

## 🚀 快速部署方案

### 方案一：Railway 部署（推荐新手）

1. **注册Railway账号**
   - 访问 https://railway.app
   - 使用GitHub账号注册

2. **连接GitHub仓库**
   - 将代码推送到GitHub
   - 在Railway中连接GitHub仓库

3. **一键部署**
   - Railway会自动检测到Flask应用
   - 自动安装依赖并部署

4. **配置环境变量**
   ```
   FLASK_ENV=production
   SECRET_KEY=your-secret-key-here
   ```

### 方案二：Render 部署

1. **注册Render账号**
   - 访问 https://render.com
   - 连接GitHub账号

2. **创建Web Service**
   - 选择GitHub仓库
   - 选择Python环境
   - 设置构建命令：`pip install -r requirements.txt`
   - 设置启动命令：`gunicorn web_app:app`

3. **配置环境变量**
   ```
   FLASK_ENV=production
   SECRET_KEY=your-secret-key-here
   ```

### 方案三：云服务器部署

1. **购买云服务器**
   - 推荐配置：2核4G内存，40G硬盘
   - 系统：Ubuntu 20.04 LTS

2. **安装依赖**
   ```bash
   # 更新系统
   sudo apt update && sudo apt upgrade -y
   
   # 安装Python和pip
   sudo apt install python3 python3-pip python3-venv -y
   
   # 安装Nginx
   sudo apt install nginx -y
   
   # 安装MySQL（可选）
   sudo apt install mysql-server -y
   ```

3. **部署应用**
   ```bash
   # 创建应用目录
   mkdir -p /var/www/production-system
   cd /var/www/production-system
   
   # 上传代码文件
   # 创建虚拟环境
   python3 -m venv venv
   source venv/bin/activate
   
   # 安装依赖
   pip install -r requirements.txt
   
   # 运行应用
   gunicorn --bind 0.0.0.0:5000 web_app:app
   ```

4. **配置Nginx反向代理**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 🔧 部署前检查清单

- [ ] 代码已推送到Git仓库
- [ ] requirements.txt文件已创建
- [ ] 环境变量已配置
- [ ] 数据库已初始化
- [ ] 静态文件路径正确
- [ ] 日志配置已设置

## 📝 环境变量说明

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| FLASK_ENV | 运行环境 | production |
| SECRET_KEY | 密钥 | your-secret-key-here |
| DATABASE_URL | 数据库连接 | sqlite:///production.db |
| PORT | 端口号 | 5000 |

## 🛡️ 安全建议

1. **更改默认密钥**
   - 生成强密钥：`python -c "import secrets; print(secrets.token_hex(32))"`

2. **配置HTTPS**
   - 使用Let's Encrypt免费SSL证书
   - 或购买商业SSL证书

3. **数据库安全**
   - 使用强密码
   - 限制数据库访问权限

4. **定期备份**
   - 设置自动备份数据库
   - 备份重要配置文件

## 📞 技术支持

如遇到部署问题，请检查：
1. 日志文件中的错误信息
2. 环境变量是否正确设置
3. 依赖包是否完整安装
4. 端口是否被占用

## 🎯 推荐部署平台

| 平台 | 优点 | 缺点 | 适合场景 |
|------|------|------|----------|
| Railway | 简单易用，自动部署 | 免费额度有限 | 个人项目，快速上线 |
| Render | 免费额度大，稳定 | 冷启动较慢 | 中小型项目 |
| Heroku | 老牌稳定，生态完善 | 免费版已取消 | 企业级应用 |
| 云服务器 | 完全控制，成本可控 | 需要技术维护 | 大型项目，定制需求 |

