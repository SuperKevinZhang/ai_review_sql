# Oracle数据库支持和代码重构说明

## 概述

本次更新完成了两个主要任务：
1. **代码重构**：抽取冗余方法到共通工具类
2. **Oracle支持**：添加完整的Oracle数据库支持

## 1. 代码重构 - 抽取冗余方法

### 问题
`review_service.py` 和 `db_connection_service.py` 中存在重复的 `_build_connection_string` 方法。

### 解决方案
创建了新的共通工具类 `app/utils/database_utils.py`，包含：

#### DatabaseUtils 类功能：
- `build_connection_string()` - 构建数据库连接字符串
- `get_database_specific_test_query()` - 获取数据库特定的测试查询
- `get_database_port_default()` - 获取数据库默认端口
- `get_required_driver_info()` - 获取数据库驱动信息

#### 更新的文件：
- ✅ `app/services/review_service.py` - 使用共通工具类
- ✅ `app/services/db_connection_service.py` - 使用共通工具类，删除冗余方法

## 2. Oracle数据库支持

### 新增功能

#### 连接字符串支持
```python
# Oracle连接字符串格式
oracle+cx_oracle://username:password@host:port/service_name
# 示例
oracle+cx_oracle://hr:password@localhost:1521/ORCL
```

#### 数据库特定查询
- **测试查询**: `SELECT 1 FROM DUAL`
- **版本查询**: `SELECT * FROM v$version WHERE banner LIKE 'Oracle%'`
- **表查询**: `SELECT table_name, comments FROM user_tab_comments WHERE table_type = 'TABLE'`
- **视图查询**: `SELECT view_name FROM user_views`

#### DDL生成支持
Oracle特定的CREATE TABLE DDL生成，包括：
- 列定义（VARCHAR2, NUMBER, DATE等Oracle数据类型）
- 主键约束
- 表注释和列注释
- 完整的Oracle语法支持

### 更新的文件

#### 1. `app/utils/database_utils.py` (新文件)
- 添加Oracle连接字符串构建
- Oracle默认端口：1521
- Oracle测试查询：`SELECT 1 FROM DUAL`
- Oracle驱动信息：cx_oracle

#### 2. `app/core/schema_extractor.py`
- 添加Oracle方言支持
- 新增 `_generate_oracle_ddl()` 方法
- 新增 `_generate_oracle_comments_ddl()` 方法
- Oracle特定的表结构查询

#### 3. `app/services/db_connection_service.py`
- 更新 `_build_connection_string_for_object()` 支持Oracle
- 更新 `_get_database_info()` 支持Oracle版本查询
- 更新 `_get_all_tables()` 和 `_get_all_views()` 支持Oracle

## 3. 支持的数据库类型

现在系统完整支持以下数据库：

| 数据库 | 驱动 | 默认端口 | 测试查询 |
|--------|------|----------|----------|
| MySQL | pymysql | 3306 | SELECT 1 as test |
| PostgreSQL | psycopg2 | 5432 | SELECT 1 as test |
| SQL Server | pyodbc | 1433 | SELECT 1 as test |
| **Oracle** | **cx_oracle** | **1521** | **SELECT 1 FROM DUAL** |
| SQLite | sqlite3 | N/A | SELECT 1 |

## 4. 安装要求

### Oracle数据库连接要求：
1. **Python驱动**: `cx_oracle` (已包含在requirements.txt中)
2. **Oracle Instant Client**: 需要单独安装
   - 下载地址：https://www.oracle.com/database/technologies/instant-client.html
   - 支持Windows、Linux、macOS

### 安装步骤：
```bash
# 1. 安装Python依赖（已包含在requirements.txt中）
pip install cx_oracle

# 2. 下载并安装Oracle Instant Client
# 根据操作系统选择对应版本

# 3. 配置环境变量（如需要）
export LD_LIBRARY_PATH=/path/to/instantclient:$LD_LIBRARY_PATH
```

## 5. 使用示例

### Oracle数据库连接配置
```python
from app.models.db_connection import DatabaseConnection, DatabaseType

# 创建Oracle连接配置
oracle_conn = DatabaseConnection()
oracle_conn.name = "生产Oracle数据库"
oracle_conn.db_type = DatabaseType.ORACLE
oracle_conn.host = "oracle-server.company.com"
oracle_conn.port = 1521
oracle_conn.database_name = "PROD"  # 服务名或SID
oracle_conn.username = "app_user"
oracle_conn.password = "encrypted_password"  # 加密存储
```

### Oracle DDL生成示例
```sql
-- 生成的Oracle CREATE TABLE DDL示例
CREATE TABLE EMPLOYEES (
  EMPLOYEE_ID NUMBER(6) NOT NULL,
  FIRST_NAME VARCHAR2(20),
  LAST_NAME VARCHAR2(25) NOT NULL,
  EMAIL VARCHAR2(25) NOT NULL,
  HIRE_DATE DATE DEFAULT SYSDATE NOT NULL,
  SALARY NUMBER(8,2),
  PRIMARY KEY (EMPLOYEE_ID)
);

-- 表注释
COMMENT ON TABLE EMPLOYEES IS '员工信息表';

-- 列注释
COMMENT ON COLUMN EMPLOYEES.EMPLOYEE_ID IS '员工ID';
COMMENT ON COLUMN EMPLOYEES.FIRST_NAME IS '名字';
COMMENT ON COLUMN EMPLOYEES.LAST_NAME IS '姓氏';
```

## 6. 测试验证

所有功能已通过测试验证：
- ✅ Oracle连接字符串构建
- ✅ Oracle特定查询语句
- ✅ Oracle DDL生成
- ✅ 共通工具类功能
- ✅ 代码重构后的兼容性

## 7. 注意事项

1. **Oracle Instant Client**: 使用Oracle数据库前必须安装Oracle Instant Client
2. **服务名 vs SID**: Oracle连接支持服务名和SID两种方式
3. **大小写敏感**: Oracle对象名默认为大写，DDL生成时会自动转换
4. **权限要求**: 需要访问`user_*`系统视图的权限来获取表结构信息

## 8. 后续扩展

可以进一步扩展的功能：
- Oracle分区表支持
- Oracle序列(SEQUENCE)支持
- Oracle包(PACKAGE)和存储过程支持
- Oracle同义词(SYNONYM)支持
- Oracle数据库链接(DATABASE LINK)支持 