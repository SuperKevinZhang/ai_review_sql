# AI SQL Review Tool

一个基于AI的SQL语句审查工具，帮助开发者和数据库管理员提高SQL代码质量。

## 🌟 功能特性

### 核心功能
- **多维度SQL审查**: 一致性、规范性、性能、安全性、可读性、可维护性
- **多数据库支持**: MySQL、PostgreSQL、SQLite、SQL Server
- **多AI模型支持**: OpenAI、DeepSeek、通义千问、Ollama
- **版本控制**: SQL语句版本管理和历史追踪
- **批量处理**: CSV文件导入导出功能

### 数据库管理
- **连接管理**: 安全的数据库连接配置和测试
- **模式浏览**: 数据库表和视图结构查看
- **对象详情**: 表结构、索引、约束信息展示

### AI配置
- **多提供商支持**: 灵活配置不同的AI服务提供商
- **参数调优**: 温度、最大令牌数等参数自定义
- **连接测试**: AI服务可用性验证

## 🚀 快速开始

### 环境要求
- Python 3.11+
- 支持的数据库（可选）
- AI服务API密钥

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ai_review_sql
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**
```bash
cp env.example .env
# 编辑 .env 文件，配置数据库和AI服务
```

4. **启动应用**
```bash
python run.py
```

5. **访问应用**
打开浏览器访问: http://localhost:8000

## 🔧 配置说明

### 环境变量配置

主要配置项：

```bash
# 数据库配置
DATABASE_URL="sqlite:///./sql_review.db"

# AI服务配置
OPENAI_API_KEY="your_openai_api_key"
DEEPSEEK_API_KEY="your_deepseek_api_key"

# 应用配置
SECRET_KEY="your-secret-key"
DEBUG=false
```

### 支持的AI提供商

| 提供商 | 模型示例 | 配置要求 |
|--------|----------|----------|
| OpenAI | gpt-3.5-turbo, gpt-4 | API Key |
| DeepSeek | deepseek-chat | API Key |
| 通义千问 | qwen-turbo | API Key |
| Ollama | llama2, codellama | 本地部署 |

## 📖 使用指南

### 1. 配置数据库连接
- 点击"添加数据库连接"
- 填写数据库信息
- 测试连接是否成功

### 2. 配置AI模型
- 进入"LLM配置"页面
- 添加AI服务提供商配置
- 设置为默认配置

### 3. 创建SQL语句
- 点击"新建SQL"
- 输入SQL语句和描述
- 选择关联的数据库连接

### 4. 执行AI审查
- 选择要审查的SQL语句
- 点击"开始审查"
- 查看详细的审查报告

### 5. 版本管理
- 修改SQL语句会自动创建新版本
- 查看版本历史
- 恢复到指定版本

## 🏗️ 项目架构

```
ai_review_sql/
├── app/                    # 应用主目录
│   ├── main.py            # FastAPI应用入口
│   ├── config/            # 配置模块
│   ├── models/            # 数据模型层
│   ├── core/              # 核心功能层
│   ├── services/          # 业务逻辑层
│   └── api/               # API路由层
├── static/                # 静态资源
├── templates/             # HTML模板
├── tests/                 # 测试文件
├── requirements.txt       # 依赖包
├── run.py                # 启动脚本
└── README.md             # 项目文档
```

### 技术栈
- **后端**: FastAPI + SQLAlchemy + Pydantic
- **前端**: HTML + CSS + JavaScript + Bootstrap
- **数据库**: SQLite（默认）/ MySQL / PostgreSQL
- **AI集成**: OpenAI API / 其他兼容接口
- **部署**: Docker + Docker Compose

## 🐳 Docker部署

### 使用Docker Compose

1. **构建和启动**
```bash
docker-compose up -d
```

2. **查看日志**
```bash
docker-compose logs -f app
```

3. **停止服务**
```bash
docker-compose down
```

### 生产环境部署

生产环境建议：
- 使用PostgreSQL作为数据库
- 配置Nginx反向代理
- 启用HTTPS
- 设置环境变量保护敏感信息

## 🧪 测试

运行测试套件：

```bash
# 运行所有测试
python -m pytest

# 运行特定测试
python -m pytest tests/test_sql_parser.py -v

# 生成覆盖率报告
python -m pytest --cov=app tests/
```

## 📊 审查维度说明

### 一致性分析
- 命名规范一致性
- 数据类型使用一致性
- 编码风格一致性

### 规范性检查
- SQL标准符合性
- 最佳实践遵循
- 代码风格规范

### 性能优化
- 索引使用建议
- 查询优化建议
- 资源使用分析

### 安全性检查
- SQL注入风险
- 权限控制建议
- 敏感数据处理

### 可读性评估
- 代码结构清晰度
- 注释完整性
- 变量命名合理性

### 可维护性分析
- 代码复杂度
- 模块化程度
- 扩展性评估

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果遇到问题或有建议，请：

1. 查看 [FAQ](docs/FAQ.md)
2. 搜索 [Issues](../../issues)
3. 创建新的 Issue

## 🔄 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 支持多数据库连接
- AI多维度SQL审查
- Web界面
- Docker部署支持

---

**Made with ❤️ by AI SQL Review Team**
