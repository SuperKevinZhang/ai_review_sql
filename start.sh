#!/bin/bash

# AI SQL Review Tool 快速启动脚本
# 适用于 Linux/macOS 系统

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "🚀 AI SQL Review Tool 启动脚本"
    echo "=================================================="
    echo -e "${NC}"
}

# 检查Python版本
check_python() {
    print_info "检查Python版本..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装，请先安装Python 3.11+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.11"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        print_success "Python版本检查通过: $PYTHON_VERSION"
    else
        print_error "Python版本过低: $PYTHON_VERSION，需要 $REQUIRED_VERSION+"
        exit 1
    fi
}

# 检查并创建虚拟环境
setup_venv() {
    print_info "设置虚拟环境..."
    
    if [ ! -d "venv" ]; then
        print_info "创建虚拟环境..."
        python3 -m venv venv
        print_success "虚拟环境创建成功"
    else
        print_success "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    print_success "虚拟环境已激活"
}

# 安装依赖
install_dependencies() {
    print_info "安装项目依赖..."
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "依赖安装完成"
    else
        print_error "requirements.txt 文件不存在"
        exit 1
    fi
}

# 检查环境配置
check_env() {
    print_info "检查环境配置..."
    
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            print_warning ".env 文件不存在，从 env.example 复制..."
            cp env.example .env
            print_warning "请编辑 .env 文件配置必要的参数（如API密钥）"
            print_info "配置文件位置: $(pwd)/.env"
        else
            print_error "env.example 文件不存在，无法创建配置文件"
            exit 1
        fi
    else
        print_success "环境配置文件已存在"
    fi
}

# 初始化数据库
init_database() {
    print_info "初始化数据库..."
    
    python3 -c "
from app.models.database import engine, Base
try:
    Base.metadata.create_all(bind=engine)
    print('✅ 数据库表创建成功')
except Exception as e:
    print(f'❌ 数据库初始化失败: {e}')
    exit(1)
" || {
        print_error "数据库初始化失败"
        exit 1
    }
}

# 运行测试
run_tests() {
    if [ "$1" = "--test" ]; then
        print_info "运行测试套件..."
        
        if command -v pytest &> /dev/null; then
            python3 -m pytest tests/ -v
            print_success "测试完成"
        else
            print_warning "pytest 未安装，跳过测试"
        fi
    fi
}

# 启动应用
start_app() {
    print_info "启动应用..."
    
    # 检查端口是否被占用
    PORT=${PORT:-8000}
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
        print_warning "端口 $PORT 已被占用，尝试使用其他端口..."
        PORT=$((PORT + 1))
        export PORT
    fi
    
    print_success "准备在端口 $PORT 启动应用"
    print_info "访问地址: http://localhost:$PORT"
    print_info "API文档: http://localhost:$PORT/docs"
    print_info "按 Ctrl+C 停止服务"
    echo ""
    
    # 启动应用
    python3 run.py
}

# 清理函数
cleanup() {
    print_info "正在停止服务..."
    # 这里可以添加清理逻辑
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help, -h     显示此帮助信息"
    echo "  --test         运行测试后启动"
    echo "  --dev          开发模式（启用调试和自动重载）"
    echo "  --prod         生产模式"
    echo "  --clean        清理并重新安装依赖"
    echo ""
    echo "示例:"
    echo "  $0              # 正常启动"
    echo "  $0 --test       # 运行测试后启动"
    echo "  $0 --dev        # 开发模式启动"
    echo "  $0 --clean      # 清理重装后启动"
}

# 清理安装
clean_install() {
    print_info "清理现有环境..."
    
    if [ -d "venv" ]; then
        rm -rf venv
        print_success "虚拟环境已删除"
    fi
    
    if [ -f ".env" ]; then
        print_warning "保留现有 .env 配置文件"
    fi
    
    # 清理Python缓存
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    print_success "清理完成"
}

# 主函数
main() {
    print_header
    
    # 解析命令行参数
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --clean)
            clean_install
            ;;
        --dev)
            export DEBUG=true
            export RELOAD=true
            export LOG_LEVEL=debug
            print_info "开发模式已启用"
            ;;
        --prod)
            export DEBUG=false
            export RELOAD=false
            export LOG_LEVEL=info
            print_info "生产模式已启用"
            ;;
    esac
    
    # 执行启动流程
    check_python
    setup_venv
    install_dependencies
    check_env
    init_database
    run_tests "$1"
    start_app
}

# 运行主函数
main "$@" 