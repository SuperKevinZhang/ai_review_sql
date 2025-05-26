#!/usr/bin/env python3
"""
AI SQL Review Tool 启动脚本
"""

import uvicorn
import os
from app.config import get_settings

def main():
    """启动应用"""
    settings = get_settings()
    
    # 从环境变量获取配置，如果没有则使用默认值
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    
    print(f"🚀 启动 {settings.app_name} v{settings.app_version}")
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"🔧 调试模式: {settings.debug}")
    print(f"📊 数据库: {settings.database_url}")
    
    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )

if __name__ == "__main__":
    main() 