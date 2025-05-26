"""API模块"""

from fastapi import APIRouter
from .database_connections import router as db_connections_router
from .sql_statements import router as sql_statements_router
from .reviews import router as reviews_router
from .llm_configs import router as llm_configs_router

# 创建主路由
router = APIRouter()

# 注册子路由
router.include_router(db_connections_router, prefix="/db-connections", tags=["数据库连接"])
router.include_router(sql_statements_router, prefix="/sql-statements", tags=["SQL语句"])
router.include_router(reviews_router, prefix="/reviews", tags=["审查报告"])
router.include_router(llm_configs_router, prefix="/llm-configs", tags=["LLM配置"]) 