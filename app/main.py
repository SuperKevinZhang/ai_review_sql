"""FastAPI应用主文件"""

import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.config import get_settings
from app.models.database import create_tables
from app.api import router as api_router

# 设置Oracle环境变量
def setup_oracle_environment():
    """设置Oracle客户端环境变量"""
    oracle_home = "/opt/oracle/instantclient_19_8"
    if os.path.exists(oracle_home):
        os.environ["ORACLE_HOME"] = oracle_home
        
        # 设置库路径
        ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")
        if oracle_home not in ld_library_path:
            os.environ["LD_LIBRARY_PATH"] = f"{oracle_home}:{ld_library_path}"
        
        # macOS特定的动态库路径
        dyld_library_path = os.environ.get("DYLD_LIBRARY_PATH", "")
        if oracle_home not in dyld_library_path:
            os.environ["DYLD_LIBRARY_PATH"] = f"{oracle_home}:{dyld_library_path}"
        
        # 设置PATH
        path = os.environ.get("PATH", "")
        if oracle_home not in path:
            os.environ["PATH"] = f"{oracle_home}:{path}"
        
        print(f"Oracle环境变量已设置: ORACLE_HOME={oracle_home}")
    else:
        print(f"警告: Oracle Instant Client目录不存在: {oracle_home}")

# 在应用启动前设置Oracle环境
setup_oracle_environment()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据表
    create_tables()
    yield
    # 关闭时的清理工作（如果需要）


# 创建FastAPI应用实例
app = FastAPI(
    title="AI SQL Review Tool",
    description="一个基于AI的SQL语句审查工具",
    version="1.0.0",
    lifespan=lifespan
)

# 获取配置
settings = get_settings()

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 设置模板
templates = Jinja2Templates(directory="templates")

# 注册API路由
app.include_router(api_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/review-results", response_class=HTMLResponse)
async def review_results(request: Request):
    """SQL审查结果页面"""
    return templates.TemplateResponse("review_results.html", {"request": request})


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )