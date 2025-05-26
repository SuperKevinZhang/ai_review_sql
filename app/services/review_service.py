"""审查服务"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.sql import text

from app.core.sql_parser import SQLParser
from app.core.schema_extractor import SchemaExtractor
from app.core.ai_reviewer import AIReviewer
from app.core.encryption import EncryptionService
from app.models.sql_statement import SQLStatement
from app.models.review_report import ReviewReport, ReviewStatus
from app.models.db_connection import DatabaseConnection
from app.models.llm_config import LLMConfig


class ReviewService:
    """审查服务，协调SQL解析、模式提取和AI审查"""
    
    def __init__(self, db: Session):
        self.db = db
        self.sql_parser = SQLParser()
        self.encryption_service = EncryptionService()
    
    def review_sql_statement(self, sql_statement_id: int, llm_config_id: Optional[int] = None) -> Dict[str, Any]:
        """
        审查SQL语句
        
        Args:
            sql_statement_id: SQL语句ID
            llm_config_id: LLM配置ID，如果为None则使用默认配置
            
        Returns:
            审查结果
        """
        try:
            # 获取SQL语句
            sql_statement = self.db.query(SQLStatement).filter(
                SQLStatement.id == sql_statement_id
            ).first()
            
            if not sql_statement:
                return {"error": "SQL语句不存在"}
            
            # 获取数据库连接
            if not sql_statement.db_connection:
                return {"error": "SQL语句未关联数据库连接"}
            
            # 步骤1: 检测数据库连接是否可用
            db_connection_test = self._test_database_connection(sql_statement.db_connection)
            if not db_connection_test["success"]:
                return {"error": f"数据库连接失败: {db_connection_test['message']}"}
            
            # 获取LLM配置
            llm_config = self._get_llm_config(llm_config_id)
            if not llm_config:
                return {"error": "LLM配置不存在或未配置"}
            
            # 步骤2: 检测大模型是否能够连通
            llm_connection_test = self._test_llm_connection(llm_config)
            if not llm_connection_test["success"]:
                return {"error": f"AI模型连接失败: {llm_connection_test['message']}"}
            
            # 步骤3: 解析SQL，提取表名
            parse_result = self.sql_parser.parse(sql_statement.sql_content)
            table_names = parse_result["tables"] + parse_result["views"]
            
            if not table_names:
                return {"error": "无法从SQL中提取表名"}
            
            # 步骤4: 获取数据库模式信息
            schema_info = self._get_schema_info(sql_statement.db_connection, table_names)
            
            # 步骤5: 调用AI进行审查
            ai_reviewer = AIReviewer(llm_config)
            review_result = ai_reviewer.review_sql(
                sql_statement.sql_content,
                sql_statement.description or "",
                schema_info
            )
            
            # 步骤6: 保存审查报告
            report = self._save_review_report(sql_statement, review_result, llm_config)
            
            # 更新SQL语句状态
            sql_statement.status = self._determine_sql_status(review_result)
            sql_statement.last_reviewed_at = report.created_at
            self.db.commit()
            
            return {
                "success": True,
                "report_id": report.id,
                "review_result": review_result
            }
        
        except Exception as e:
            self.db.rollback()
            return {"error": f"审查失败: {str(e)}"}
    
    def _get_llm_config(self, llm_config_id: Optional[int]) -> Optional[Dict[str, Any]]:
        """获取LLM配置"""
        if llm_config_id:
            llm_config = self.db.query(LLMConfig).filter(
                LLMConfig.id == llm_config_id,
                LLMConfig.is_active == True
            ).first()
        else:
            # 使用默认配置
            llm_config = self.db.query(LLMConfig).filter(
                LLMConfig.is_default == True,
                LLMConfig.is_active == True
            ).first()
        
        if not llm_config:
            return None
        
        return {
            "provider": llm_config.provider.value,
            "model_name": llm_config.model_name,
            "api_key": llm_config.api_key,
            "base_url": llm_config.base_url,
            "temperature": llm_config.temperature,
            "max_tokens": llm_config.max_tokens,
            "top_p": llm_config.top_p,
            "frequency_penalty": llm_config.frequency_penalty,
            "presence_penalty": llm_config.presence_penalty,
            "timeout": llm_config.timeout
        }
    
    def _get_schema_info(self, db_connection: DatabaseConnection, table_names: list) -> Dict[str, Any]:
        """获取数据库模式信息"""
        try:
            # 构建数据库连接字符串
            connection_string = self._build_connection_string(db_connection)
            
            # 创建数据库引擎
            engine = create_engine(connection_string)
            
            # 创建模式提取器
            schema_extractor = SchemaExtractor(engine, db_connection.db_type)
            
            # 获取表结构信息
            schema_info = schema_extractor.get_table_schema(table_names)
            
            return schema_info
        
        except Exception as e:
            print(f"获取数据库模式信息失败: {e}")
            return {"tables": [], "views": []}
    
    def _build_connection_string(self, db_connection: DatabaseConnection) -> str:
        """构建数据库连接字符串"""
        # 解密密码
        password = self.encryption_service.decrypt_password(db_connection.password)
        
        if db_connection.db_type.value == "mysql":
            return f"mysql+pymysql://{db_connection.username}:{password}@{db_connection.host}:{db_connection.port}/{db_connection.database_name}"
        elif db_connection.db_type.value == "postgresql":
            return f"postgresql+psycopg2://{db_connection.username}:{password}@{db_connection.host}:{db_connection.port}/{db_connection.database_name}"
        elif db_connection.db_type.value == "sqlserver":
            return f"mssql+pyodbc://{db_connection.username}:{password}@{db_connection.host}:{db_connection.port}/{db_connection.database_name}?driver=ODBC+Driver+17+for+SQL+Server"
        elif db_connection.db_type.value == "sqlite":
            return f"sqlite:///{db_connection.database_name}"
        else:
            raise ValueError(f"不支持的数据库类型: {db_connection.db_type.value}")
    
    def _test_database_connection(self, db_connection: DatabaseConnection) -> Dict[str, Any]:
        """测试数据库连接"""
        try:
            # 构建连接字符串
            connection_string = self._build_connection_string(db_connection)
            
            # 创建临时引擎进行连接测试
            test_engine = create_engine(connection_string, pool_pre_ping=True)
            
            # 尝试连接并执行简单查询
            with test_engine.connect() as conn:
                if db_connection.db_type.value == "sqlite":
                    conn.execute(text("SELECT 1"))
                else:
                    conn.execute(text("SELECT 1 as test"))
            
            test_engine.dispose()
            return {"success": True, "message": "数据库连接成功"}
            
        except Exception as e:
            return {"success": False, "message": f"数据库连接失败: {str(e)}"}
    
    def _test_llm_connection(self, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """测试大模型连接"""
        try:
            # 创建AI审查器实例
            ai_reviewer = AIReviewer(llm_config)
            
            # 发送简单的测试请求
            test_prompt = "请回复'连接测试成功'"
            response = ai_reviewer._call_llm(test_prompt)
            
            if response and len(response.strip()) > 0:
                return {"success": True, "message": "AI模型连接成功"}
            else:
                return {"success": False, "message": "AI模型响应为空"}
                
        except Exception as e:
            return {"success": False, "message": f"AI模型连接失败: {str(e)}"}
    
    def _save_review_report(self, sql_statement: SQLStatement, review_result: Dict[str, Any], llm_config: Dict[str, Any]) -> ReviewReport:
        """保存审查报告"""
        
        # 解析审查结果
        overall = review_result.get("overall_assessment", {})
        consistency = review_result.get("consistency", {})
        conventions = review_result.get("conventions", {})
        performance = review_result.get("performance", {})
        security = review_result.get("security", {})
        readability = review_result.get("readability", {})
        maintainability = review_result.get("maintainability", {})
        
        # 创建审查报告
        report = ReviewReport(
            sql_statement_id=sql_statement.id,
            
            # 总体评估
            overall_status=self._parse_status(overall.get("status")),
            overall_score=overall.get("score", 0),
            overall_summary=overall.get("summary", ""),
            
            # 一致性
            consistency_status=self._parse_status(consistency.get("status")),
            consistency_score=consistency.get("score", 0),
            consistency_details=consistency.get("details", ""),
            consistency_suggestions=consistency.get("suggestions", ""),
            
            # 规范性
            conventions_status=self._parse_status(conventions.get("status")),
            conventions_score=conventions.get("score", 0),
            conventions_details=conventions.get("details", ""),
            conventions_suggestions=conventions.get("suggestions", ""),
            
            # 性能
            performance_status=self._parse_status(performance.get("status")),
            performance_score=performance.get("score", 0),
            performance_details=performance.get("details", ""),
            performance_suggestions=performance.get("suggestions", ""),
            
            # 安全性
            security_status=self._parse_status(security.get("status")),
            security_score=security.get("score", 0),
            security_details=security.get("details", ""),
            security_suggestions=security.get("suggestions", ""),
            
            # 可读性
            readability_status=self._parse_status(readability.get("status")),
            readability_score=readability.get("score", 0),
            readability_details=readability.get("details", ""),
            readability_suggestions=readability.get("suggestions", ""),
            
            # 可维护性
            maintainability_status=self._parse_status(maintainability.get("status")),
            maintainability_score=maintainability.get("score", 0),
            maintainability_details=maintainability.get("details", ""),
            maintainability_suggestions=maintainability.get("suggestions", ""),
            
            # LLM信息
            llm_provider=llm_config["provider"],
            llm_model=llm_config["model_name"],
            
            # 优化建议
            optimized_sql=review_result.get("optimized_sql", "")
        )
        
        self.db.add(report)
        self.db.flush()  # 获取ID但不提交
        
        return report
    
    def _parse_status(self, status_str: str) -> ReviewStatus:
        """解析状态字符串为枚举"""
        if not status_str:
            return ReviewStatus.HAS_ISSUES
        
        status_map = {
            "excellent": ReviewStatus.EXCELLENT,
            "good": ReviewStatus.GOOD,
            "needs_improvement": ReviewStatus.NEEDS_IMPROVEMENT,
            "has_issues": ReviewStatus.HAS_ISSUES
        }
        
        return status_map.get(status_str.lower(), ReviewStatus.HAS_ISSUES)
    
    def _determine_sql_status(self, review_result: Dict[str, Any]):
        """根据审查结果确定SQL状态"""
        from app.models.sql_statement import SQLStatementStatus
        
        overall = review_result.get("overall_assessment", {})
        status = overall.get("status", "has_issues")
        
        if status == "excellent":
            return SQLStatementStatus.APPROVED
        elif status == "good":
            return SQLStatementStatus.REVIEWED
        else:
            return SQLStatementStatus.DRAFT
    
    def get_review_report(self, report_id: int) -> Optional[ReviewReport]:
        """获取审查报告"""
        return self.db.query(ReviewReport).filter(ReviewReport.id == report_id).first()
    
    def get_sql_review_history(self, sql_statement_id: int) -> list:
        """获取SQL语句的审查历史"""
        return self.db.query(ReviewReport).filter(
            ReviewReport.sql_statement_id == sql_statement_id
        ).order_by(ReviewReport.created_at.desc()).all() 