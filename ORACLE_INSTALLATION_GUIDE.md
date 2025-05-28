# Oracle Instant Client 安装指南

## 错误说明

您遇到的错误：
```
DPI-1047: Cannot locate a 64-bit Oracle Client library: "dlopen(libclntsh.dylib, 0x0001): tried: 'libclntsh.dylib' (no such file)
```

这表明系统中缺少Oracle Instant Client库文件。这是连接Oracle数据库的必要组件。

## macOS 安装指南

### 方法一：使用Homebrew安装（推荐）

```bash
# 1. 安装Homebrew（如果还没有安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 添加Oracle的tap
brew tap InstantClientTap/instantclient

# 3. 安装Oracle Instant Client
brew install instantclient-basic
brew install instantclient-sqlplus  # 可选，包含SQL*Plus工具
```

### 方法二：手动下载安装

#### 步骤1：下载Oracle Instant Client

1. 访问Oracle官网：https://www.oracle.com/database/technologies/instant-client/macos-intel-x86-downloads.html
2. 下载以下文件（需要Oracle账号，免费注册）：
   - **Basic Package** (instantclient-basic-macos.x64-21.x.x.x.x.zip)
   - **SQL*Plus Package** (可选)

#### 步骤2：安装

```bash
# 1. 创建安装目录
sudo mkdir -p /opt/oracle

# 2. 解压下载的文件到安装目录
cd /opt/oracle
sudo unzip ~/Downloads/instantclient-basic-macos.x64-21.x.x.x.x.zip

# 3. 创建符号链接（重要）
cd /opt/oracle/instantclient_21_x
sudo ln -s libclntsh.dylib.21.1 libclntsh.dylib

# 4. 设置环境变量
echo 'export ORACLE_HOME=/opt/oracle/instantclient_21_x' >> ~/.zshrc
echo 'export LD_LIBRARY_PATH=$ORACLE_HOME:$LD_LIBRARY_PATH' >> ~/.zshrc
echo 'export DYLD_LIBRARY_PATH=$ORACLE_HOME:$DYLD_LIBRARY_PATH' >> ~/.zshrc
echo 'export PATH=$ORACLE_HOME:$PATH' >> ~/.zshrc

# 5. 重新加载环境变量
source ~/.zshrc
```

### 方法三：使用conda安装

```bash
# 如果您使用conda环境
conda install -c conda-forge oracle-instantclient
```

## 验证安装

安装完成后，验证是否成功：

```bash
# 1. 检查库文件是否存在
ls -la /opt/oracle/instantclient_*/libclntsh.dylib

# 2. 检查环境变量
echo $ORACLE_HOME
echo $LD_LIBRARY_PATH

# 3. 测试Python连接
python3 -c "import cx_Oracle; print('cx_Oracle version:', cx_Oracle.version)"
```

## 常见问题解决

### 问题1：权限问题
```bash
# 如果遇到权限问题，确保文件有执行权限
sudo chmod +x /opt/oracle/instantclient_*/*
```

### 问题2：M1 Mac（Apple Silicon）
如果您使用M1 Mac，需要下载ARM64版本：
```bash
# 下载ARM64版本的Instant Client
# 或者使用Rosetta运行x86版本
arch -x86_64 python3 your_script.py
```

### 问题3：环境变量未生效
```bash
# 手动设置环境变量（临时）
export ORACLE_HOME=/opt/oracle/instantclient_21_x
export LD_LIBRARY_PATH=$ORACLE_HOME:$LD_LIBRARY_PATH
export DYLD_LIBRARY_PATH=$ORACLE_HOME:$DYLD_LIBRARY_PATH
```

## 测试Oracle连接

安装完成后，可以使用以下代码测试连接：

```python
import cx_Oracle

# 测试连接
try:
    # 替换为您的Oracle数据库信息
    dsn = cx_Oracle.makedsn("localhost", 1521, service_name="ORCL")
    connection = cx_Oracle.connect("username", "password", dsn)
    print("Oracle连接成功！")
    
    cursor = connection.cursor()
    cursor.execute("SELECT 1 FROM DUAL")
    result = cursor.fetchone()
    print(f"测试查询结果: {result}")
    
    cursor.close()
    connection.close()
    
except cx_Oracle.Error as e:
    print(f"Oracle连接失败: {e}")
```

## 在AI Review SQL系统中测试

安装完成后，您可以在系统中测试Oracle连接：

```python
# 在项目根目录运行
python3 -c "
from app.utils.database_utils import DatabaseUtils
from app.models.db_connection import DatabaseConnection, DatabaseType

# 创建测试连接
db_utils = DatabaseUtils()
oracle_conn = DatabaseConnection()
oracle_conn.db_type = DatabaseType.ORACLE
oracle_conn.username = 'your_username'
oracle_conn.host = 'your_host'
oracle_conn.port = 1521
oracle_conn.database_name = 'your_service_name'

# 测试查询
query = db_utils.get_database_specific_test_query(DatabaseType.ORACLE)
print(f'Oracle测试查询: {query}')
"
```

## 注意事项

1. **版本兼容性**：确保cx_Oracle版本与Instant Client版本兼容
2. **网络连接**：确保能够访问Oracle数据库服务器
3. **防火墙**：检查1521端口是否开放
4. **服务名vs SID**：确认使用正确的连接方式

## 如果仍有问题

如果按照上述步骤安装后仍有问题，请：

1. 重启终端或IDE
2. 检查系统架构：`uname -m`
3. 检查Python架构：`python3 -c "import platform; print(platform.machine())"`
4. 确保Python和Instant Client架构匹配（都是x86_64或都是arm64）

## 替代方案

如果Oracle Instant Client安装困难，可以考虑：

1. **使用Docker**：在Docker容器中运行Oracle数据库和应用
2. **云服务**：使用Oracle Cloud或其他云服务的Oracle数据库
3. **虚拟机**：在Linux虚拟机中安装和使用 