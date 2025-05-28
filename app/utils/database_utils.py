"""数据库工具类 - 包含共通的数据库操作方法"""

from typing import Dict, Any
from app.models.db_connection import DatabaseConnection, DatabaseType
from app.core.encryption import EncryptionService


class DatabaseUtils:
    """数据库工具类"""
    
    def __init__(self):
        self.encryption_service = EncryptionService()
    
    def build_connection_string(self, db_connection: DatabaseConnection) -> str:
        """
        构建数据库连接字符串
        
        Args:
            db_connection: 数据库连接对象
            
        Returns:
            数据库连接字符串
        """
        # 解密密码
        password = self.encryption_service.decrypt_password(db_connection.password)
        
        db_type = db_connection.db_type.value
        username = db_connection.username
        host = db_connection.host
        port = db_connection.port
        database_name = db_connection.database_name
        
        if db_type == "mysql":
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_name}"
        
        elif db_type == "postgresql":
            return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database_name}"
        
        elif db_type == "sqlserver":
            return f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server"
        
        elif db_type == "oracle":
            # Oracle连接字符串使用service_name格式
            # 正确格式: oracle+cx_oracle://user:pass@host:port/?service_name=service_name
            return f"oracle+cx_oracle://{username}:{password}@{host}:{port}/?service_name={database_name}"
        
        elif db_type == "sqlite":
            # SQLite不需要host、port、username、password
            return f"sqlite:///{database_name}"
        
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    def get_database_specific_test_query(self, db_type: DatabaseType) -> str:
        """
        获取数据库特定的测试查询语句
        
        Args:
            db_type: 数据库类型
            
        Returns:
            测试查询语句
        """
        if db_type == DatabaseType.SQLITE:
            return "SELECT 1"
        elif db_type == DatabaseType.ORACLE:
            return "SELECT 1 FROM DUAL"
        else:
            # MySQL, PostgreSQL, SQL Server
            return "SELECT 1 as test"
    
    def get_database_port_default(self, db_type: DatabaseType) -> int:
        """
        获取数据库默认端口
        
        Args:
            db_type: 数据库类型
            
        Returns:
            默认端口号
        """
        port_mapping = {
            DatabaseType.MYSQL: 3306,
            DatabaseType.POSTGRESQL: 5432,
            DatabaseType.SQLSERVER: 1433,
            DatabaseType.ORACLE: 1521,
            DatabaseType.SQLITE: None  # SQLite不需要端口
        }
        return port_mapping.get(db_type)
    
    def get_required_driver_info(self, db_type: DatabaseType) -> Dict[str, Any]:
        """
        获取数据库驱动信息
        
        Args:
            db_type: 数据库类型
            
        Returns:
            驱动信息字典
        """
        driver_info = {
            DatabaseType.MYSQL: {
                "driver": "pymysql",
                "install_command": "pip install pymysql",
                "description": "MySQL数据库驱动"
            },
            DatabaseType.POSTGRESQL: {
                "driver": "psycopg2",
                "install_command": "pip install psycopg2-binary",
                "description": "PostgreSQL数据库驱动"
            },
            DatabaseType.SQLSERVER: {
                "driver": "pyodbc",
                "install_command": "pip install pyodbc",
                "description": "SQL Server数据库驱动，需要安装ODBC Driver 17 for SQL Server"
            },
            DatabaseType.ORACLE: {
                "driver": "cx_oracle",
                "install_command": "pip install cx_oracle",
                "description": "Oracle数据库驱动，需要安装Oracle Instant Client"
            },
            DatabaseType.SQLITE: {
                "driver": "sqlite3",
                "install_command": "内置驱动，无需安装",
                "description": "SQLite数据库驱动（Python内置）"
            }
        }
        return driver_info.get(db_type, {}) 