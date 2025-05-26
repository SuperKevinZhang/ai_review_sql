"""应用配置设置"""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    app_name: str = "AI SQL Review Tool"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 服务器配置
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    log_level: str = "info"
    
    # 数据库配置
    database_url: str = "sqlite:///./sql_review.db"
    
    # 安全配置
    secret_key: str = "your-secret-key-change-in-production"
    encryption_key: Optional[str] = None
    cors_origins: str = "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000"
    
    # AI模型配置
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_default_model: str = "gpt-3.5-turbo"
    
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_default_model: str = "deepseek-chat"
    
    qwen_api_key: Optional[str] = None
    qwen_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    qwen_default_model: str = "qwen-turbo"
    
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama2"
    
    # 默认LLM配置
    default_llm_provider: str = "openai"
    default_llm_model: str = "gpt-3.5-turbo"
    default_temperature: float = 0.1
    default_max_tokens: int = 4000
    
    # 文件上传配置
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: str = ".csv,.sql"
    max_upload_size: int = 10
    
    # 功能配置
    sql_parse_timeout: int = 30
    ai_review_timeout: int = 120
    cache_ttl: int = 3600
    
    # 日志配置
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "logs/app.log"
    log_max_size: int = 10485760
    log_backup_count: int = 5
    
    # 开发工具配置
    enable_docs: bool = True
    enable_debug_toolbar: bool = False
    enable_profiler: bool = False
    
    # 数据库连接池配置
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取应用配置实例（单例模式）"""
    return Settings() 