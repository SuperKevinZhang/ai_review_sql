# AI SQL Review Tool 架构文档

## 概述

AI SQL Review Tool 是一个基于AI的SQL语句审查工具，采用现代化的Web架构设计，支持多数据库、多AI模型的集成。本文档详细描述了系统的架构设计、技术选型和实现细节。

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser                              │
│                 (HTML + CSS + JS)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/HTTPS
┌─────────────────────▼───────────────────────────────────────┐
│                  FastAPI Server                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │   API       │ │  Templates  │ │      Static Files       ││
│  │  Routes     │ │   (Jinja2)  │ │   (CSS/JS/Images)      ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Service Layer                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ DB Service  │ │ SQL Service │ │     LLM Service         ││
│  │             │ │             │ │                         ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Core Layer                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ SQL Parser  │ │ AI Reviewer │ │   Schema Extractor      ││
│  │             │ │             │ │                         ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Data Layer                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │   SQLite    │ │   MySQL     │ │     PostgreSQL          ││
│  │             │ │             │ │                         ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                External AI Services                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │   OpenAI    │ │  DeepSeek   │ │       Ollama            ││
│  │             │ │             │ │                         ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 分层架构详解

### 1. 表现层 (Presentation Layer)

**技术栈**: HTML5 + CSS3 + JavaScript + Bootstrap 5

**职责**:
- 用户界面展示
- 用户交互处理
- 前端数据验证
- 响应式设计

**主要组件**:
- `templates/index.html`: 主页面模板
- `static/css/style.css`: 样式文件
- `static/js/main.js`: 主要JavaScript逻辑

### 2. API层 (API Layer)

**技术栈**: FastAPI + Pydantic

**职责**:
- HTTP请求路由
- 请求参数验证
- 响应格式化
- 错误处理

**主要模块**:
```python
app/api/
├── database_connections.py    # 数据库连接API
├── sql_statements.py         # SQL语句管理API
├── reviews.py               # 审查报告API
└── llm_configs.py          # LLM配置API
```

### 3. 服务层 (Service Layer)

**技术栈**: Python + SQLAlchemy

**职责**:
- 业务逻辑实现
- 数据处理协调
- 事务管理
- 缓存处理

**主要服务**:
```python
app/services/
├── db_connection_service.py   # 数据库连接服务
├── sql_statement_service.py   # SQL语句服务
├── review_service.py          # 审查服务
└── llm_config_service.py     # LLM配置服务
```

### 4. 核心层 (Core Layer)

**技术栈**: Python + sqlparse + requests

**职责**:
- 核心算法实现
- SQL解析处理
- AI模型集成
- 数据库模式提取

**核心组件**:
```python
app/core/
├── sql_parser.py         # SQL解析器
├── ai_reviewer.py        # AI审查器
├── schema_extractor.py   # 模式提取器
└── encryption.py         # 加密服务
```

### 5. 数据层 (Data Layer)

**技术栈**: SQLAlchemy + 多数据库驱动

**职责**:
- 数据持久化
- 数据库连接管理
- ORM映射
- 数据迁移

**数据模型**:
```python
app/models/
├── database.py           # 数据库配置
├── db_connection.py      # 数据库连接模型
├── sql_statement.py      # SQL语句模型
├── review_report.py      # 审查报告模型
└── llm_config.py        # LLM配置模型
```

## 核心功能设计

### 1. SQL解析器 (SQLParser)

**设计目标**: 准确提取SQL语句中的表名和视图名

**实现策略**:
- 主要使用 `sqlparse` 库进行语法分析
- 备用正则表达式解析方案
- 支持复杂SQL语句（JOIN、子查询等）

**关键算法**:
```python
def _extract_from_statement(self, statement):
    """从SQL语句中提取表名"""
    tokens = list(statement.flatten())
    
    for i, token in enumerate(tokens):
        if token.ttype is Keyword:
            token_upper = token.value.upper()
            if token_upper in ('FROM', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL'):
                # 查找下一个标识符
                for j in range(i + 1, len(tokens)):
                    next_token = tokens[j]
                    if next_token.ttype in (None, sqlparse.tokens.Name):
                        self._extract_table_name(next_token.value)
                        break
```

### 2. AI审查器 (AIReviewer)

**设计目标**: 集成多种AI模型，提供统一的SQL审查接口

**支持的AI提供商**:
- OpenAI (GPT-3.5, GPT-4)
- DeepSeek (deepseek-chat)
- 通义千问 (qwen-turbo)
- Ollama (本地模型)

**审查维度**:
1. **一致性分析**: 命名规范、编码风格
2. **规范性检查**: SQL标准、最佳实践
3. **性能优化**: 索引建议、查询优化
4. **安全性检查**: SQL注入、权限控制
5. **可读性评估**: 代码结构、注释
6. **可维护性分析**: 复杂度、模块化

**提示词工程**:
```python
def _build_prompt(self, sql_content, description, schema_info):
    """构建AI审查提示词"""
    prompt = f"""
    请对以下SQL语句进行全面的多维度审查分析：

    SQL语句：
    {sql_content}

    业务描述：
    {description}

    数据库模式信息：
    {self._format_schema_info(schema_info)}

    请从以下6个维度进行分析，并以JSON格式返回结果：
    1. 一致性分析 (consistency)
    2. 规范性检查 (conventions)
    3. 性能分析 (performance)
    4. 安全性检查 (security)
    5. 可读性评估 (readability)
    6. 可维护性分析 (maintainability)
    """
    return prompt
```

### 3. 数据库模式提取器 (SchemaExtractor)

**设计目标**: 获取数据库的表结构信息，为AI审查提供上下文

**支持的数据库**:
- MySQL
- PostgreSQL
- SQLite
- SQL Server

**提取信息**:
- 表结构（列名、数据类型、约束）
- 索引信息
- 外键关系
- 视图定义

### 4. 加密服务 (EncryptionService)

**设计目标**: 保护敏感信息（数据库密码、API密钥）

**加密算法**: Fernet (对称加密)

**实现特点**:
- 密钥派生使用PBKDF2
- 自动生成随机盐值
- 支持密钥轮换

## 数据库设计

### ER图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ DatabaseConnection│    │  SQLStatement   │    │  ReviewReport   │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │
│ name            │◄───┤ db_connection_id│    │ sql_statement_id│────┐
│ db_type         │    │ title           │◄───┤ llm_config_id   │    │
│ host            │    │ sql_content     │    │ overall_score   │    │
│ port            │    │ description     │    │ status          │    │
│ database_name   │    │ status          │    │ created_at      │    │
│ username        │    │ version         │    │ ...             │    │
│ password        │    │ created_at      │    └─────────────────┘    │
│ ...             │    │ ...             │                           │
└─────────────────┘    └─────────────────┘                           │
                                                                     │
┌─────────────────┐                                                  │
│   LLMConfig     │                                                  │
├─────────────────┤                                                  │
│ id (PK)         │◄─────────────────────────────────────────────────┘
│ name            │
│ provider        │
│ model_name      │
│ api_key         │
│ base_url        │
│ temperature     │
│ ...             │
└─────────────────┘
```

### 表结构设计

#### 1. database_connections (数据库连接)
```sql
CREATE TABLE database_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    db_type VARCHAR(20) NOT NULL,
    host VARCHAR(255),
    port INTEGER,
    database_name VARCHAR(100),
    username VARCHAR(100),
    password TEXT,  -- 加密存储
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_tested_at TIMESTAMP
);
```

#### 2. sql_statements (SQL语句)
```sql
CREATE TABLE sql_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    sql_content TEXT NOT NULL,
    description TEXT,
    db_connection_id INTEGER,
    status VARCHAR(20) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    parent_id INTEGER,  -- 版本控制
    tags VARCHAR(500),
    category VARCHAR(50),
    created_by VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reviewed_at TIMESTAMP,
    FOREIGN KEY (db_connection_id) REFERENCES database_connections(id),
    FOREIGN KEY (parent_id) REFERENCES sql_statements(id)
);
```

#### 3. review_reports (审查报告)
```sql
CREATE TABLE review_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sql_statement_id INTEGER NOT NULL,
    llm_config_id INTEGER,
    overall_score INTEGER,
    overall_status VARCHAR(20),
    overall_summary TEXT,
    consistency_score INTEGER,
    consistency_status VARCHAR(20),
    consistency_details TEXT,
    consistency_suggestions TEXT,
    -- ... 其他维度字段
    review_result JSON,  -- 完整的审查结果
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sql_statement_id) REFERENCES sql_statements(id),
    FOREIGN KEY (llm_config_id) REFERENCES llm_configs(id)
);
```

## 安全设计

### 1. 数据加密
- 敏感信息（密码、API密钥）使用Fernet对称加密
- 加密密钥通过环境变量配置
- 支持密钥轮换机制

### 2. 输入验证
- 使用Pydantic进行请求参数验证
- SQL注入防护
- XSS攻击防护

### 3. 访问控制
- API接口权限控制
- 数据库连接权限隔离
- 文件上传类型限制

### 4. 错误处理
- 统一异常处理机制
- 敏感信息脱敏
- 详细的日志记录

## 性能优化

### 1. 数据库优化
- 合理的索引设计
- 连接池管理
- 查询优化

### 2. 缓存策略
- 数据库模式信息缓存
- AI审查结果缓存
- 静态资源缓存

### 3. 异步处理
- AI审查异步执行
- 批量操作优化
- 长时间任务后台处理

## 扩展性设计

### 1. 插件化架构
- AI提供商插件化
- 数据库驱动插件化
- 审查维度可扩展

### 2. 微服务化
- 服务拆分策略
- API网关设计
- 服务发现机制

### 3. 水平扩展
- 负载均衡
- 数据库分片
- 缓存集群

## 部署架构

### 1. 开发环境
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
      - DATABASE_URL=sqlite:///./dev.db
    volumes:
      - .:/app
```

### 2. 生产环境
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    image: ai-sql-review:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/prod
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ai_sql_review
  
  redis:
    image: redis:7-alpine
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
```

### 3. 监控和日志
- 应用性能监控 (APM)
- 日志聚合和分析
- 健康检查和告警
- 指标收集和可视化

## 技术选型理由

### 1. FastAPI vs Django/Flask
**选择FastAPI的原因**:
- 自动API文档生成
- 高性能异步支持
- 现代Python类型提示
- 内置数据验证

### 2. SQLAlchemy vs Django ORM
**选择SQLAlchemy的原因**:
- 更灵活的查询构建
- 更好的性能控制
- 支持多种数据库
- 成熟的生态系统

### 3. 前端技术选择
**选择传统Web技术的原因**:
- 简单直接，易于维护
- 服务端渲染，SEO友好
- 减少前后端分离复杂性
- 快速原型开发

## 未来规划

### 1. 功能增强
- 支持更多数据库类型
- 增加更多AI模型
- 实时协作功能
- 移动端适配

### 2. 性能提升
- 查询结果缓存
- 增量更新机制
- 并发处理优化
- 资源使用监控

### 3. 企业级特性
- 用户权限管理
- 审计日志
- 数据备份恢复
- 高可用部署

---

本架构文档将随着项目的发展持续更新和完善。 