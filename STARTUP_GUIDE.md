# AI SQL Review Tool 启动指南

## 🚀 快速启动

### 前置要求
- Python 3.11+ 
- pip 包管理器
- Git (可选)

### 1. 环境准备

#### 检查Python版本
```bash
python --version
# 应该显示 Python 3.11.x 或更高版本
```

#### 创建虚拟环境（推荐）
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. 安装依赖

```bash
# 安装项目依赖
pip install -r requirements.txt

# 验证安装
pip list | grep fastapi
pip list | grep sqlalchemy
```

### 3. 环境配置

#### 复制环境配置文件
```bash
cp env.example .env
```

#### 编辑 .env 文件
```bash
# 使用你喜欢的编辑器编辑 .env 文件
nano .env
# 或者
vim .env
# 或者
code .env
```

#### 基础配置示例
```env
# 应用基础配置
APP_NAME="AI SQL Review Tool"
DEBUG=true
SECRET_KEY="your-development-secret-key-change-me"

# 数据库配置（开发环境使用SQLite）
DATABASE_URL="sqlite:///./sql_review.db"

# AI服务配置（至少配置一个）
OPENAI_API_KEY="sk-your-openai-api-key-here"
# DEEPSEEK_API_KEY="your-deepseek-api-key"
# QWEN_API_KEY="your-qwen-api-key"

# 服务器配置
HOST="127.0.0.1"
PORT=8000
RELOAD=true
LOG_LEVEL="info"
```

### 4. 数据库初始化

```bash
# 启动应用会自动创建数据库表
# 如果需要手动初始化，可以运行：
python -c "
from app.models.database import engine, Base
Base.metadata.create_all(bind=engine)
print('数据库表创建成功！')
"
```

### 5. 启动应用

#### 方式一：使用启动脚本（推荐）
```bash
python run.py
```

#### 方式二：直接使用uvicorn
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 6. 验证启动

#### 检查服务状态
```bash
# 健康检查
curl http://localhost:8000/health

# 应该返回：
# {"status":"healthy","app_name":"AI SQL Review Tool","version":"1.0.0"}
```

#### 访问Web界面
打开浏览器访问：http://localhost:8000

#### 查看API文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 功能测试

### 1. 配置LLM服务

1. 访问 http://localhost:8000
2. 点击"LLM配置"
3. 添加新的LLM配置：
   - 名称：OpenAI GPT-3.5
   - 提供商：openai
   - 模型：gpt-3.5-turbo
   - API密钥：你的OpenAI API密钥
   - 基础URL：https://api.openai.com/v1
4. 点击"测试连接"验证配置
5. 设置为默认配置

### 2. 配置数据库连接

1. 点击"数据库连接"
2. 添加新连接：
   - 名称：测试SQLite
   - 数据库类型：sqlite
   - 数据库名：test.db
   - 描述：测试用SQLite数据库
3. 点击"测试连接"

### 3. 创建测试SQL

1. 点击"SQL语句"
2. 添加新SQL：
   - 标题：用户查询测试
   - SQL内容：
     ```sql
     SELECT u.id, u.name, u.email 
     FROM users u 
     WHERE u.status = 'active' 
     ORDER BY u.created_at DESC 
     LIMIT 10
     ```
   - 描述：查询活跃用户列表
   - 关联数据库：选择刚创建的数据库连接

### 4. 执行AI审查

1. 选择刚创建的SQL语句
2. 点击"开始审查"
3. 等待AI分析完成
4. 查看多维度审查报告

## 🐛 常见问题排查

### 问题1：Python版本不兼容
```bash
# 错误：Python版本过低
# 解决：升级Python或使用pyenv管理多版本
pyenv install 3.11.0
pyenv local 3.11.0
```

### 问题2：依赖安装失败
```bash
# 错误：某些包安装失败
# 解决：升级pip并清理缓存
pip install --upgrade pip
pip cache purge
pip install -r requirements.txt
```

### 问题3：端口被占用
```bash
# 错误：Address already in use
# 解决：更换端口或杀死占用进程
lsof -ti:8000 | xargs kill -9
# 或者修改 .env 文件中的 PORT=8001
```

### 问题4：数据库连接失败
```bash
# 错误：数据库文件权限问题
# 解决：检查文件权限
ls -la sql_review.db
chmod 664 sql_review.db
```

### 问题5：AI服务连接失败
- 检查API密钥是否正确
- 检查网络连接
- 验证API配额是否充足
- 检查防火墙设置

## 📊 性能监控

### 查看应用日志
```bash
# 启动时会显示详细日志
python run.py

# 输出示例：
# 🚀 启动 AI SQL Review Tool v1.0.0
# 📍 服务地址: http://127.0.0.1:8000
# 🔧 调试模式: True
# 📊 数据库: sqlite:///./sql_review.db
```

### 监控系统资源
```bash
# 查看进程状态
ps aux | grep python

# 查看端口占用
netstat -tulpn | grep :8000

# 查看内存使用
top -p $(pgrep -f "python run.py")
```

## 🔧 开发模式配置

### 启用调试模式
```env
# .env 文件
DEBUG=true
RELOAD=true
LOG_LEVEL="debug"
```

### 运行测试
```bash
# 运行所有测试
python -m pytest -v

# 运行特定测试
python -m pytest tests/test_sql_parser.py -v

# 生成覆盖率报告
python -m pytest --cov=app tests/
```

### 代码格式化
```bash
# 安装开发工具
pip install black isort flake8

# 格式化代码
black app/
isort app/

# 检查代码质量
flake8 app/
```

## 🚀 生产环境部署

### Docker部署
```bash
# 构建镜像
docker build -t ai-sql-review .

# 运行容器
docker run -d \
  --name ai-sql-review \
  -p 8000:8000 \
  -e DATABASE_URL="sqlite:///./sql_review.db" \
  -e OPENAI_API_KEY="your-api-key" \
  ai-sql-review
```

### Docker Compose部署
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down
```

## 📝 下一步

1. **配置生产数据库**：将SQLite替换为PostgreSQL或MySQL
2. **设置反向代理**：使用Nginx进行负载均衡
3. **启用HTTPS**：配置SSL证书
4. **监控告警**：集成监控系统
5. **备份策略**：设置数据备份计划

## 🆘 获取帮助

- 查看项目文档：README.md
- 架构设计：ARCHITECTURE.md
- 提交Issue：GitHub Issues
- 联系开发团队：support@example.com

---

**祝您使用愉快！** 🎉 