@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM AI SQL Review Tool 快速启动脚本
REM 适用于 Windows 系统

echo.
echo ==================================================
echo 🚀 AI SQL Review Tool 启动脚本
echo ==================================================
echo.

REM 检查Python版本
echo ℹ️  检查Python版本...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装Python 3.11+
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python版本: %PYTHON_VERSION%

REM 检查并创建虚拟环境
echo ℹ️  设置虚拟环境...
if not exist "venv" (
    echo ℹ️  创建虚拟环境...
    python -m venv venv
    echo ✅ 虚拟环境创建成功
) else (
    echo ✅ 虚拟环境已存在
)

REM 激活虚拟环境
call venv\Scripts\activate.bat
echo ✅ 虚拟环境已激活

REM 升级pip
echo ℹ️  升级pip...
python -m pip install --upgrade pip

REM 安装依赖
echo ℹ️  安装项目依赖...
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo ✅ 依赖安装完成
) else (
    echo ❌ requirements.txt 文件不存在
    pause
    exit /b 1
)

REM 检查环境配置
echo ℹ️  检查环境配置...
if not exist ".env" (
    if exist "env.example" (
        echo ⚠️  .env 文件不存在，从 env.example 复制...
        copy env.example .env >nul
        echo ⚠️  请编辑 .env 文件配置必要的参数（如API密钥）
        echo ℹ️  配置文件位置: %CD%\.env
    ) else (
        echo ❌ env.example 文件不存在，无法创建配置文件
        pause
        exit /b 1
    )
) else (
    echo ✅ 环境配置文件已存在
)

REM 初始化数据库
echo ℹ️  初始化数据库...
python -c "from app.models.database import engine, Base; Base.metadata.create_all(bind=engine); print('✅ 数据库表创建成功')" 2>nul
if errorlevel 1 (
    echo ❌ 数据库初始化失败
    pause
    exit /b 1
)

REM 检查端口占用
set PORT=8000
netstat -an | find ":%PORT%" >nul
if not errorlevel 1 (
    echo ⚠️  端口 %PORT% 已被占用，尝试使用其他端口...
    set /a PORT=%PORT%+1
)

REM 启动应用
echo ℹ️  启动应用...
echo ✅ 准备在端口 %PORT% 启动应用
echo ℹ️  访问地址: http://localhost:%PORT%
echo ℹ️  API文档: http://localhost:%PORT%/docs
echo ℹ️  按 Ctrl+C 停止服务
echo.

REM 设置环境变量并启动
set PORT=%PORT%
python run.py

pause 