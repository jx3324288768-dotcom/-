# Vercel部署指南

## 🚀 部署步骤

### 1. 准备工作
- 确保代码已推送到GitHub
- 在Vercel上连接GitHub账号

### 2. 在Vercel上部署
1. 访问 https://vercel.com
2. 点击 "New Project"
3. 选择您的GitHub仓库
4. 配置项目：
   - **Framework Preset**: Other
   - **Root Directory**: `./`
   - **Build Command**: 留空
   - **Output Directory**: 留空
   - **Install Command**: `pip install -r requirements.txt`

### 3. 环境变量设置
在Vercel项目设置中添加：
```
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
```

### 4. 部署配置
- Vercel会自动检测到 `vercel.json` 配置文件
- 使用 `api/index.py` 作为入口点
- 自动处理Python依赖

## 📁 项目结构

```
├── api/
│   └── index.py          # Vercel入口文件
├── static/               # 静态文件
├── templates/            # HTML模板
├── web_app.py           # 主应用文件
├── config.py            # 配置文件
├── requirements.txt     # Python依赖
├── vercel.json         # Vercel配置
└── .gitignore          # Git忽略文件
```

## ⚠️ 注意事项

1. **数据库**: Vercel使用临时文件系统，数据不会持久化
2. **文件上传**: 不支持文件上传功能
3. **长时间运行**: 适合API和Web应用
4. **免费限制**: 有使用量限制

## 🔧 故障排除

### 常见问题：
1. **构建失败**: 检查requirements.txt中的依赖
2. **导入错误**: 确保所有Python文件路径正确
3. **静态文件404**: 检查static文件夹结构
4. **数据库错误**: 使用内存数据库或外部数据库服务

### 调试方法：
1. 查看Vercel构建日志
2. 检查环境变量设置
3. 测试本地运行是否正常
