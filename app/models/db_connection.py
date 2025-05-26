"""数据库连接模型"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import enum

from .database import Base


class DatabaseType(enum.Enum):
    """数据库类型枚举"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    SQLITE = "sqlite"


class DatabaseConnection(Base):
    """数据库连接模型"""
    
    __tablename__ = "database_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="连接名称")
    db_type = Column(Enum(DatabaseType), nullable=False, comment="数据库类型")
    host = Column(String(255), comment="主机地址")
    port = Column(Integer, comment="端口号")
    database_name = Column(String(100), comment="数据库名")
    username = Column(String(100), comment="用户名")
    password = Column(Text, comment="密码(加密存储)")
    ssl_enabled = Column(Boolean, default=False, comment="是否启用SSL")
    connection_params = Column(Text, comment="额外连接参数(JSON格式)")
    description = Column(Text, comment="连接描述")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    last_tested_at = Column(DateTime(timezone=True), comment="最后测试时间")
    
    def __repr__(self):
        return f"<DatabaseConnection(name='{self.name}', db_type='{self.db_type.value}')>" 