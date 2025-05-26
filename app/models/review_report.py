"""审查报告模型"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base


class ReviewStatus(enum.Enum):
    """审查状态枚举"""
    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"  # 良好
    NEEDS_IMPROVEMENT = "needs_improvement"  # 需要改进
    HAS_ISSUES = "has_issues"  # 存在问题


class ReviewReport(Base):
    """审查报告模型"""
    
    __tablename__ = "review_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联的SQL语句
    sql_statement_id = Column(Integer, ForeignKey("sql_statements.id"), nullable=False, comment="关联的SQL语句ID")
    sql_statement = relationship("SQLStatement", backref="review_reports")
    
    # 总体评估
    overall_status = Column(Enum(ReviewStatus), comment="总体评估状态")
    overall_score = Column(Float, comment="总体评分(0-100)")
    overall_summary = Column(Text, comment="总体评估摘要")
    
    # 各维度评估
    consistency_status = Column(Enum(ReviewStatus), comment="一致性状态")
    consistency_score = Column(Float, comment="一致性评分")
    consistency_details = Column(Text, comment="一致性详细分析")
    consistency_suggestions = Column(Text, comment="一致性改进建议")
    
    conventions_status = Column(Enum(ReviewStatus), comment="规范性状态")
    conventions_score = Column(Float, comment="规范性评分")
    conventions_details = Column(Text, comment="规范性详细分析")
    conventions_suggestions = Column(Text, comment="规范性改进建议")
    
    performance_status = Column(Enum(ReviewStatus), comment="性能状态")
    performance_score = Column(Float, comment="性能评分")
    performance_details = Column(Text, comment="性能详细分析")
    performance_suggestions = Column(Text, comment="性能改进建议")
    
    security_status = Column(Enum(ReviewStatus), comment="安全性状态")
    security_score = Column(Float, comment="安全性评分")
    security_details = Column(Text, comment="安全性详细分析")
    security_suggestions = Column(Text, comment="安全性改进建议")
    
    readability_status = Column(Enum(ReviewStatus), comment="可读性状态")
    readability_score = Column(Float, comment="可读性评分")
    readability_details = Column(Text, comment="可读性详细分析")
    readability_suggestions = Column(Text, comment="可读性改进建议")
    
    maintainability_status = Column(Enum(ReviewStatus), comment="可维护性状态")
    maintainability_score = Column(Float, comment="可维护性评分")
    maintainability_details = Column(Text, comment="可维护性详细分析")
    maintainability_suggestions = Column(Text, comment="可维护性改进建议")
    
    # AI模型信息
    llm_provider = Column(String(50), comment="使用的LLM提供商")
    llm_model = Column(String(100), comment="使用的LLM模型")
    
    # 优化建议
    optimized_sql = Column(Text, comment="优化后的SQL建议")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<ReviewReport(id={self.id}, sql_id={self.sql_statement_id}, status='{self.overall_status.value if self.overall_status else None}')>" 