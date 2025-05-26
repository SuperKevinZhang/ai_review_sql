"""SQL语句模型"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base


class SQLStatementStatus(enum.Enum):
    """SQL语句状态枚举"""
    DRAFT = "draft"  # 草稿
    REVIEWED = "reviewed"  # 已审查
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝


class SQLStatement(Base):
    """SQL语句模型"""
    
    __tablename__ = "sql_statements"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="SQL标题")
    sql_content = Column(Text, nullable=False, comment="SQL内容")
    description = Column(Text, comment="业务描述")
    status = Column(Enum(SQLStatementStatus), default=SQLStatementStatus.DRAFT, comment="状态")
    
    # 关联的数据库连接
    db_connection_id = Column(Integer, ForeignKey("database_connections.id"), comment="关联的数据库连接ID")
    db_connection = relationship("DatabaseConnection", backref="sql_statements")
    
    # 版本控制
    version = Column(Integer, default=1, comment="版本号")
    parent_id = Column(Integer, ForeignKey("sql_statements.id"), comment="父版本ID")
    
    # 标签和分类
    tags = Column(String(500), comment="标签(逗号分隔)")
    category = Column(String(100), comment="分类")
    
    # 元数据
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_by = Column(String(100), comment="创建者")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    last_reviewed_at = Column(DateTime(timezone=True), comment="最后审查时间")
    
    def __repr__(self):
        return f"<SQLStatement(id={self.id}, title='{self.title}', status='{self.status.value}')>" 