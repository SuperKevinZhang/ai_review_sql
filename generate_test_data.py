#!/usr/bin/env python3
"""
AI SQL Review Tool 测试数据生成脚本
用于生成演示和测试用的数据
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header():
    """打印标题"""
    print("=" * 60)
    print("🧪 AI SQL Review Tool 测试数据生成器")
    print("=" * 60)
    print()

def create_sample_database_connections():
    """创建示例数据库连接"""
    from app.models.database import SessionLocal
    from app.models.db_connection import DatabaseConnection, DatabaseType
    from app.core.encryption import EncryptionService
    
    encryption = EncryptionService()
    
    connections = [
        {
            "name": "本地SQLite测试库",
            "db_type": DatabaseType.SQLITE,
            "host": "",
            "port": None,
            "database_name": "test.db",
            "username": "",
            "password": "",
            "description": "用于测试的本地SQLite数据库"
        },
        {
            "name": "开发环境MySQL",
            "db_type": DatabaseType.MYSQL,
            "host": "localhost",
            "port": 3306,
            "database_name": "dev_database",
            "username": "dev_user",
            "password": encryption.encrypt("dev_password"),
            "description": "开发环境MySQL数据库"
        },
        {
            "name": "测试PostgreSQL",
            "db_type": DatabaseType.POSTGRESQL,
            "host": "localhost",
            "port": 5432,
            "database_name": "test_db",
            "username": "test_user",
            "password": encryption.encrypt("test_pass"),
            "description": "测试环境PostgreSQL数据库"
        }
    ]
    
    db = SessionLocal()
    try:
        created_count = 0
        for conn_data in connections:
            # 检查是否已存在
            existing = db.query(DatabaseConnection).filter(
                DatabaseConnection.name == conn_data["name"]
            ).first()
            
            if not existing:
                connection = DatabaseConnection(**conn_data)
                db.add(connection)
                created_count += 1
        
        db.commit()
        print(f"✅ 创建了 {created_count} 个数据库连接")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建数据库连接失败: {e}")
        return False
    finally:
        db.close()

def create_sample_llm_configs():
    """创建示例LLM配置"""
    from app.models.database import SessionLocal
    from app.models.llm_config import LLMConfig, LLMProvider
    from app.core.encryption import EncryptionService
    
    encryption = EncryptionService()
    
    configs = [
        {
            "name": "OpenAI GPT-3.5",
            "provider": LLMProvider.OPENAI,
            "model_name": "gpt-3.5-turbo",
            "api_key": encryption.encrypt("your-openai-api-key-here"),
            "base_url": "https://api.openai.com/v1",
            "temperature": 0.1,
            "max_tokens": 4000,
            "description": "OpenAI GPT-3.5 Turbo模型",
            "is_default": True
        },
        {
            "name": "DeepSeek Chat",
            "provider": LLMProvider.DEEPSEEK,
            "model_name": "deepseek-chat",
            "api_key": encryption.encrypt("your-deepseek-api-key-here"),
            "base_url": "https://api.deepseek.com/v1",
            "temperature": 0.1,
            "max_tokens": 4000,
            "description": "DeepSeek聊天模型",
            "is_default": False
        },
        {
            "name": "通义千问",
            "provider": LLMProvider.QWEN,
            "model_name": "qwen-turbo",
            "api_key": encryption.encrypt("your-qwen-api-key-here"),
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "temperature": 0.1,
            "max_tokens": 4000,
            "description": "阿里云通义千问模型",
            "is_default": False
        },
        {
            "name": "本地Ollama",
            "provider": LLMProvider.OLLAMA,
            "model_name": "llama2",
            "api_key": "",
            "base_url": "http://localhost:11434",
            "temperature": 0.1,
            "max_tokens": 4000,
            "description": "本地部署的Ollama模型",
            "is_default": False
        }
    ]
    
    db = SessionLocal()
    try:
        created_count = 0
        for config_data in configs:
            # 检查是否已存在
            existing = db.query(LLMConfig).filter(
                LLMConfig.name == config_data["name"]
            ).first()
            
            if not existing:
                config = LLMConfig(**config_data)
                db.add(config)
                created_count += 1
        
        db.commit()
        print(f"✅ 创建了 {created_count} 个LLM配置")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建LLM配置失败: {e}")
        return False
    finally:
        db.close()

def create_sample_sql_statements():
    """创建示例SQL语句"""
    from app.models.database import SessionLocal
    from app.models.sql_statement import SQLStatement
    from app.models.db_connection import DatabaseConnection
    
    sql_examples = [
        {
            "title": "用户基本信息查询",
            "sql_content": """SELECT 
    u.id,
    u.username,
    u.email,
    u.created_at,
    u.last_login_at
FROM users u 
WHERE u.status = 'active' 
    AND u.created_at >= '2024-01-01'
ORDER BY u.created_at DESC 
LIMIT 100;""",
            "description": "查询活跃用户的基本信息，按创建时间倒序排列",
            "category": "查询",
            "tags": "用户,基础查询,分页"
        },
        {
            "title": "订单统计分析",
            "sql_content": """SELECT 
    DATE(o.created_at) as order_date,
    COUNT(*) as order_count,
    SUM(o.total_amount) as total_revenue,
    AVG(o.total_amount) as avg_order_value
FROM orders o
INNER JOIN users u ON o.user_id = u.id
WHERE o.status IN ('completed', 'shipped')
    AND o.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(o.created_at)
ORDER BY order_date DESC;""",
            "description": "最近30天的订单统计分析，包含订单数量、总收入和平均订单价值",
            "category": "分析",
            "tags": "订单,统计,聚合,日期"
        },
        {
            "title": "用户权限更新",
            "sql_content": """UPDATE users 
SET role = 'premium',
    updated_at = NOW()
WHERE id IN (
    SELECT DISTINCT u.id 
    FROM users u
    INNER JOIN orders o ON u.id = o.user_id
    WHERE o.total_amount > 1000
        AND o.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)
);""",
            "description": "将最近90天内消费超过1000元的用户升级为高级用户",
            "category": "更新",
            "tags": "用户,权限,批量更新"
        },
        {
            "title": "产品库存预警",
            "sql_content": """SELECT 
    p.id,
    p.name,
    p.sku,
    i.current_stock,
    i.min_stock_level,
    CASE 
        WHEN i.current_stock = 0 THEN '缺货'
        WHEN i.current_stock <= i.min_stock_level THEN '库存不足'
        ELSE '正常'
    END as stock_status
FROM products p
INNER JOIN inventory i ON p.id = i.product_id
WHERE i.current_stock <= i.min_stock_level
ORDER BY i.current_stock ASC;""",
            "description": "查询库存不足或缺货的产品，用于库存预警",
            "category": "查询",
            "tags": "库存,预警,产品,条件查询"
        },
        {
            "title": "复杂关联查询",
            "sql_content": """SELECT 
    u.username,
    u.email,
    COUNT(DISTINCT o.id) as order_count,
    SUM(o.total_amount) as total_spent,
    MAX(o.created_at) as last_order_date,
    GROUP_CONCAT(DISTINCT c.name) as categories
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN products p ON oi.product_id = p.id
LEFT JOIN categories c ON p.category_id = c.id
WHERE u.created_at >= '2024-01-01'
GROUP BY u.id, u.username, u.email
HAVING order_count > 0
ORDER BY total_spent DESC
LIMIT 50;""",
            "description": "复杂的多表关联查询，分析用户购买行为和偏好",
            "category": "分析",
            "tags": "多表关联,聚合,分组,用户行为"
        }
    ]
    
    db = SessionLocal()
    try:
        # 获取第一个数据库连接
        db_connection = db.query(DatabaseConnection).first()
        if not db_connection:
            print("❌ 没有找到数据库连接，请先创建数据库连接")
            return False
        
        created_count = 0
        for sql_data in sql_examples:
            # 检查是否已存在
            existing = db.query(SQLStatement).filter(
                SQLStatement.title == sql_data["title"]
            ).first()
            
            if not existing:
                sql_statement = SQLStatement(
                    db_connection_id=db_connection.id,
                    **sql_data
                )
                db.add(sql_statement)
                created_count += 1
        
        db.commit()
        print(f"✅ 创建了 {created_count} 个SQL语句")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建SQL语句失败: {e}")
        return False
    finally:
        db.close()

def create_sample_review_reports():
    """创建示例审查报告"""
    from app.models.database import SessionLocal
    from app.models.review_report import ReviewReport
    from app.models.sql_statement import SQLStatement
    from app.models.llm_config import LLMConfig
    import json
    
    db = SessionLocal()
    try:
        # 获取SQL语句和LLM配置
        sql_statements = db.query(SQLStatement).limit(3).all()
        llm_config = db.query(LLMConfig).filter(LLMConfig.is_default == True).first()
        
        if not sql_statements or not llm_config:
            print("❌ 没有找到SQL语句或LLM配置，请先创建相关数据")
            return False
        
        created_count = 0
        for i, sql_statement in enumerate(sql_statements):
            # 检查是否已存在
            existing = db.query(ReviewReport).filter(
                ReviewReport.sql_statement_id == sql_statement.id
            ).first()
            
            if not existing:
                # 生成模拟的审查结果
                review_result = {
                    "consistency": {
                        "score": 85 + i * 2,
                        "status": "good",
                        "details": "命名规范基本一致，建议统一使用下划线命名",
                        "suggestions": ["统一字段命名规范", "添加表别名"]
                    },
                    "conventions": {
                        "score": 90 + i,
                        "status": "excellent",
                        "details": "遵循SQL编写规范，代码结构清晰",
                        "suggestions": ["添加适当的注释"]
                    },
                    "performance": {
                        "score": 75 + i * 3,
                        "status": "good",
                        "details": "查询性能良好，建议添加索引优化",
                        "suggestions": ["在WHERE条件字段上添加索引", "考虑使用LIMIT限制结果集"]
                    },
                    "security": {
                        "score": 95,
                        "status": "excellent",
                        "details": "没有发现安全风险",
                        "suggestions": []
                    },
                    "readability": {
                        "score": 88 + i,
                        "status": "good",
                        "details": "代码可读性良好，格式规范",
                        "suggestions": ["添加业务逻辑注释"]
                    },
                    "maintainability": {
                        "score": 82 + i * 2,
                        "status": "good",
                        "details": "代码结构合理，易于维护",
                        "suggestions": ["考虑将复杂查询拆分为多个步骤"]
                    }
                }
                
                overall_score = sum(dim["score"] for dim in review_result.values()) // 6
                
                from app.models.review_report import ReviewStatus
                
                report = ReviewReport(
                    sql_statement_id=sql_statement.id,
                    llm_provider=llm_config.provider.value,
                    llm_model=llm_config.model_name,
                    overall_score=overall_score,
                    overall_status=ReviewStatus.GOOD if overall_score >= 80 else ReviewStatus.NEEDS_IMPROVEMENT,
                    overall_summary=f"SQL语句整体质量{overall_score}分，建议关注性能优化和代码注释。",
                    consistency_score=review_result["consistency"]["score"],
                    consistency_status=ReviewStatus.GOOD,
                    consistency_details=review_result["consistency"]["details"],
                    consistency_suggestions=json.dumps(review_result["consistency"]["suggestions"], ensure_ascii=False),
                    conventions_score=review_result["conventions"]["score"],
                    conventions_status=ReviewStatus.EXCELLENT,
                    conventions_details=review_result["conventions"]["details"],
                    conventions_suggestions=json.dumps(review_result["conventions"]["suggestions"], ensure_ascii=False),
                    performance_score=review_result["performance"]["score"],
                    performance_status=ReviewStatus.GOOD,
                    performance_details=review_result["performance"]["details"],
                    performance_suggestions=json.dumps(review_result["performance"]["suggestions"], ensure_ascii=False),
                    security_score=review_result["security"]["score"],
                    security_status=ReviewStatus.EXCELLENT,
                    security_details=review_result["security"]["details"],
                    security_suggestions=json.dumps(review_result["security"]["suggestions"], ensure_ascii=False),
                    readability_score=review_result["readability"]["score"],
                    readability_status=ReviewStatus.GOOD,
                    readability_details=review_result["readability"]["details"],
                    readability_suggestions=json.dumps(review_result["readability"]["suggestions"], ensure_ascii=False),
                    maintainability_score=review_result["maintainability"]["score"],
                    maintainability_status=ReviewStatus.GOOD,
                    maintainability_details=review_result["maintainability"]["details"],
                    maintainability_suggestions=json.dumps(review_result["maintainability"]["suggestions"], ensure_ascii=False)
                )
                
                db.add(report)
                created_count += 1
        
        db.commit()
        print(f"✅ 创建了 {created_count} 个审查报告")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建审查报告失败: {e}")
        return False
    finally:
        db.close()

def main():
    """主函数"""
    print_header()
    
    # 检查数据库是否已初始化
    try:
        from app.models.database import engine, Base
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表结构检查完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return
    
    print("开始生成测试数据...")
    print()
    
    # 生成各种测试数据
    success_count = 0
    total_count = 3
    
    if create_sample_database_connections():
        success_count += 1
    
    if create_sample_llm_configs():
        success_count += 1
    
    if create_sample_sql_statements():
        success_count += 1
    
    if create_sample_review_reports():
        success_count += 1
    
    print()
    print("=" * 60)
    print(f"📊 测试数据生成完成: {success_count}/{total_count} 项成功")
    
    if success_count == total_count:
        print("🎉 所有测试数据都生成成功！")
        print()
        print("现在您可以：")
        print("1. 启动应用: python run.py")
        print("2. 访问 http://localhost:8000")
        print("3. 查看生成的示例数据")
        print("4. 测试AI审查功能")
    else:
        print("⚠️  部分数据生成失败，请查看上述错误信息")

if __name__ == "__main__":
    main() 