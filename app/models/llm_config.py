"""LLM配置模型"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, Enum
from sqlalchemy.sql import func
import enum

from .database import Base


class LLMProvider(enum.Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    OLLAMA = "ollama"
    CLAUDE = "claude"


class LLMConfig(Base):
    """LLM配置模型"""
    
    __tablename__ = "llm_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="配置名称")
    provider = Column(Enum(LLMProvider), nullable=False, comment="LLM提供商")
    model_name = Column(String(100), nullable=False, comment="模型名称")
    
    # API配置
    api_key = Column(Text, comment="API密钥(加密存储)")
    base_url = Column(String(500), comment="API基础URL")
    
    # 模型参数
    temperature = Column(Float, default=0.1, comment="温度参数")
    max_tokens = Column(Integer, default=4000, comment="最大令牌数")
    top_p = Column(Float, default=1.0, comment="Top-p参数")
    frequency_penalty = Column(Float, default=0.0, comment="频率惩罚")
    presence_penalty = Column(Float, default=0.0, comment="存在惩罚")
    
    # 超时和重试配置
    timeout = Column(Integer, default=60, comment="超时时间(秒)")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    
    # 状态
    is_default = Column(Boolean, default=False, comment="是否为默认配置")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 描述和备注
    description = Column(Text, comment="配置描述")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    last_tested_at = Column(DateTime(timezone=True), comment="最后测试时间")
    
    def __repr__(self):
        return f"<LLMConfig(name='{self.name}', provider='{self.provider.value}', model='{self.model_name}')>" 