#!/usr/bin/env python3
"""
AI SQL Review Tool 健康检查脚本
用于验证应用的各个组件是否正常工作
"""

import sys
import os
import requests
import time
import json
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header():
    """打印标题"""
    print("=" * 60)
    print("🏥 AI SQL Review Tool 健康检查")
    print("=" * 60)
    print()

def print_result(check_name: str, success: bool, message: str = ""):
    """打印检查结果"""
    status = "✅ 通过" if success else "❌ 失败"
    print(f"{check_name:<30} {status}")
    if message:
        print(f"{'':30} {message}")
    print()

def check_python_version() -> Tuple[bool, str]:
    """检查Python版本"""
    try:
        version = sys.version_info
        if version.major == 3 and version.minor >= 11:
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        else:
            return False, f"Python版本过低: {version.major}.{version.minor}.{version.micro}，需要3.11+"
    except Exception as e:
        return False, f"检查失败: {e}"

def check_dependencies() -> Tuple[bool, str]:
    """检查依赖包"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'sqlparse',
        'pydantic',
        'requests',
        'cryptography'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        return False, f"缺少依赖包: {', '.join(missing_packages)}"
    else:
        return True, f"所有依赖包已安装 ({len(required_packages)}个)"

def check_environment_config() -> Tuple[bool, str]:
    """检查环境配置"""
    try:
        from app.config import get_settings
        settings = get_settings()
        
        issues = []
        
        # 检查必要配置
        if not settings.secret_key or settings.secret_key == "your-development-secret-key-change-me":
            issues.append("SECRET_KEY未设置或使用默认值")
        
        if not settings.database_url:
            issues.append("DATABASE_URL未设置")
        
        if issues:
            return False, f"配置问题: {'; '.join(issues)}"
        else:
            return True, "环境配置正常"
            
    except Exception as e:
        return False, f"配置检查失败: {e}"

def check_database_connection() -> Tuple[bool, str]:
    """检查数据库连接"""
    try:
        from app.models.database import engine, Base
        
        # 尝试连接数据库
        with engine.connect() as conn:
            # 检查表是否存在
            Base.metadata.create_all(bind=engine)
            return True, "数据库连接正常，表结构已创建"
            
    except Exception as e:
        return False, f"数据库连接失败: {e}"

def check_sql_parser() -> Tuple[bool, str]:
    """检查SQL解析器"""
    try:
        from app.core.sql_parser import SQLParser
        
        parser = SQLParser()
        test_sql = "SELECT u.id, u.name FROM users u WHERE u.status = 'active'"
        result = parser.parse(test_sql)
        
        if 'tables' in result and 'users' in result['tables']:
            return True, "SQL解析器工作正常"
        else:
            return False, f"SQL解析结果异常: {result}"
            
    except Exception as e:
        return False, f"SQL解析器检查失败: {e}"

def check_encryption_service() -> Tuple[bool, str]:
    """检查加密服务"""
    try:
        from app.core.encryption import EncryptionService
        
        encryption = EncryptionService()
        test_data = "test_password_123"
        
        # 测试加密和解密
        encrypted = encryption.encrypt(test_data)
        decrypted = encryption.decrypt(encrypted)
        
        if decrypted == test_data:
            return True, "加密服务工作正常"
        else:
            return False, "加密解密结果不匹配"
            
    except Exception as e:
        return False, f"加密服务检查失败: {e}"

def check_web_server(host: str = "127.0.0.1", port: int = 8000, timeout: int = 5) -> Tuple[bool, str]:
    """检查Web服务器"""
    try:
        url = f"http://{host}:{port}/health"
        response = requests.get(url, timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                return True, f"Web服务器运行正常 (端口 {port})"
            else:
                return False, f"健康检查返回异常状态: {data}"
        else:
            return False, f"HTTP状态码: {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return False, f"无法连接到服务器 {host}:{port}"
    except requests.exceptions.Timeout:
        return False, f"连接超时 ({timeout}秒)"
    except Exception as e:
        return False, f"检查失败: {e}"

def check_api_endpoints(host: str = "127.0.0.1", port: int = 8000) -> Tuple[bool, str]:
    """检查API端点"""
    try:
        base_url = f"http://{host}:{port}"
        endpoints = [
            "/",
            "/docs",
            "/api/database-connections",
            "/api/sql-statements",
            "/api/llm-configs"
        ]
        
        failed_endpoints = []
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=3)
                if response.status_code >= 500:
                    failed_endpoints.append(f"{endpoint} ({response.status_code})")
            except Exception:
                failed_endpoints.append(f"{endpoint} (连接失败)")
        
        if failed_endpoints:
            return False, f"失败的端点: {', '.join(failed_endpoints)}"
        else:
            return True, f"所有API端点正常 ({len(endpoints)}个)"
            
    except Exception as e:
        return False, f"API检查失败: {e}"

def run_all_checks(check_server: bool = False) -> Dict[str, Tuple[bool, str]]:
    """运行所有检查"""
    checks = {
        "Python版本": check_python_version,
        "依赖包": check_dependencies,
        "环境配置": check_environment_config,
        "数据库连接": check_database_connection,
        "SQL解析器": check_sql_parser,
        "加密服务": check_encryption_service,
    }
    
    if check_server:
        checks["Web服务器"] = check_web_server
        checks["API端点"] = check_api_endpoints
    
    results = {}
    
    for check_name, check_func in checks.items():
        try:
            success, message = check_func()
            results[check_name] = (success, message)
        except Exception as e:
            results[check_name] = (False, f"检查过程中出错: {e}")
    
    return results

def main():
    """主函数"""
    print_header()
    
    # 检查命令行参数
    check_server = "--server" in sys.argv or "-s" in sys.argv
    
    if check_server:
        print("🌐 包含服务器检查（确保应用正在运行）")
        print()
    
    # 运行检查
    results = run_all_checks(check_server)
    
    # 显示结果
    passed = 0
    total = len(results)
    
    for check_name, (success, message) in results.items():
        print_result(check_name, success, message)
        if success:
            passed += 1
    
    # 总结
    print("=" * 60)
    print(f"📊 检查完成: {passed}/{total} 项通过")
    
    if passed == total:
        print("🎉 所有检查都通过了！系统状态良好。")
        sys.exit(0)
    else:
        print("⚠️  有些检查未通过，请查看上述详细信息。")
        sys.exit(1)

if __name__ == "__main__":
    main() 