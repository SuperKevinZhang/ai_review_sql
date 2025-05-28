"""数据库连接服务"""

from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.db_connection import DatabaseConnection
from app.core.encryption import EncryptionService
from app.core.schema_extractor import SchemaExtractor
from app.utils.database_utils import DatabaseUtils


class DatabaseConnectionService:
    """数据库连接服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.encryption_service = EncryptionService()
        self.database_utils = DatabaseUtils()
    
    def test_connection_object(self, db_connection: DatabaseConnection) -> Dict[str, Any]:
        """
        测试数据库连接对象（不保存到数据库）
        
        Args:
            db_connection: 数据库连接对象
            
        Returns:
            测试结果
        """
        try:
            # 构建连接字符串
            connection_string = self._build_connection_string_for_object(db_connection)
            
            # 创建引擎并测试连接
            engine = create_engine(connection_string, pool_timeout=10)
            
            # 获取数据库特定的测试查询
            test_query = self.database_utils.get_database_specific_test_query(db_connection.db_type)
            
            with engine.connect() as conn:
                # 执行简单查询测试连接
                result = conn.execute(text(test_query))
                
                row = result.fetchone()
                if row:
                    return {
                        "success": True,
                        "message": "数据库连接测试成功",
                        "database_info": self._get_database_info(conn, db_connection)
                    }
                else:
                    return {"success": False, "message": "连接测试失败"}
        
        except SQLAlchemyError as e:
            return {"success": False, "message": f"数据库连接错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"连接测试失败: {str(e)}"}

    def test_connection(self, connection_id: int) -> Dict[str, Any]:
        """
        测试数据库连接
        
        Args:
            connection_id: 数据库连接ID
            
        Returns:
            测试结果
        """
        try:
            # 获取连接配置
            db_connection = self.db.query(DatabaseConnection).filter(
                DatabaseConnection.id == connection_id
            ).first()
            
            if not db_connection:
                return {"success": False, "error": "数据库连接不存在"}
            
            # 使用共通工具类构建连接字符串
            connection_string = self.database_utils.build_connection_string(db_connection)
            
            # 创建引擎并测试连接
            engine = create_engine(connection_string, pool_timeout=10)
            
            # 获取数据库特定的测试查询
            test_query = self.database_utils.get_database_specific_test_query(db_connection.db_type)
            
            with engine.connect() as conn:
                # 执行简单查询测试连接
                result = conn.execute(text(test_query))
                
                row = result.fetchone()
                if row:
                    # 更新最后测试时间
                    from sqlalchemy.sql import func
                    db_connection.last_tested_at = func.now()
                    self.db.commit()
                    
                    return {
                        "success": True,
                        "message": "数据库连接测试成功",
                        "database_info": self._get_database_info(conn, db_connection)
                    }
                else:
                    return {"success": False, "error": "连接测试失败"}
        
        except SQLAlchemyError as e:
            return {"success": False, "error": f"数据库连接错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"连接测试失败: {str(e)}"}
    
    def get_database_schema(self, connection_id: int) -> Dict[str, Any]:
        """
        获取数据库模式信息
        
        Args:
            connection_id: 数据库连接ID
            
        Returns:
            数据库模式信息
        """
        try:
            # 获取连接配置
            db_connection = self.db.query(DatabaseConnection).filter(
                DatabaseConnection.id == connection_id
            ).first()
            
            if not db_connection:
                return {"error": "数据库连接不存在"}
            
            # 使用共通工具类构建连接字符串
            connection_string = self.database_utils.build_connection_string(db_connection)
            
            # 创建引擎
            engine = create_engine(connection_string)
            
            # 获取所有表和视图
            with engine.connect() as conn:
                tables = self._get_all_tables(conn, db_connection)
                views = self._get_all_views(conn, db_connection)
            
            return {
                "tables": tables,
                "views": views,
                "connection_info": {
                    "name": db_connection.name,
                    "db_type": db_connection.db_type.value,
                    "database_name": db_connection.database_name
                }
            }
        
        except Exception as e:
            return {"error": f"获取数据库模式失败: {str(e)}"}
    
    def get_table_details(self, connection_id: int, table_name: str, object_type: str = "table") -> Dict[str, Any]:
        """
        获取表或视图的详细信息
        
        Args:
            connection_id: 数据库连接ID
            table_name: 表名或视图名
            object_type: 对象类型 (table/view)
            
        Returns:
            表或视图的详细信息
        """
        try:
            # 获取连接配置
            db_connection = self.db.query(DatabaseConnection).filter(
                DatabaseConnection.id == connection_id
            ).first()
            
            if not db_connection:
                return {"error": "数据库连接不存在"}
            
            # 使用共通工具类构建连接字符串
            connection_string = self.database_utils.build_connection_string(db_connection)
            
            # 创建引擎和模式提取器
            engine = create_engine(connection_string)
            schema_extractor = SchemaExtractor(engine, db_connection.db_type)
            
            # 获取表结构信息
            schema_info = schema_extractor.get_table_schema([table_name])
            
            if object_type == "table" and schema_info["tables"]:
                return schema_info["tables"][0]
            elif object_type == "view" and schema_info["views"]:
                return schema_info["views"][0]
            else:
                return {"error": f"{object_type} '{table_name}' 不存在"}
        
        except Exception as e:
            return {"error": f"获取{object_type}详细信息失败: {str(e)}"}
    
    def _build_connection_string_for_object(self, db_connection: DatabaseConnection) -> str:
        """构建数据库连接字符串（用于测试对象，密码未加密）"""
        password = db_connection.password or ""
        username = db_connection.username
        host = db_connection.host
        port = db_connection.port
        database_name = db_connection.database_name
        
        db_type = db_connection.db_type.value
        
        if db_type == "mysql":
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_name}"
        elif db_type == "postgresql":
            return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database_name}"
        elif db_type == "sqlserver":
            return f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server"
        elif db_type == "oracle":
            return f"oracle+cx_oracle://{username}:{password}@{host}:{port}/?service_name={database_name}"
        elif db_type == "sqlite":
            return f"sqlite:///{database_name}"
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    def _get_database_info(self, conn, db_connection: DatabaseConnection) -> Dict[str, Any]:
        """获取数据库基本信息"""
        try:
            info = {
                "database_type": db_connection.db_type.value,
                "database_name": db_connection.database_name
            }
            
            db_type = db_connection.db_type.value
            
            if db_type == "mysql":
                result = conn.execute(text("SELECT VERSION() as version"))
                row = result.fetchone()
                if row:
                    info["version"] = row[0]
            elif db_type == "postgresql":
                result = conn.execute(text("SELECT version()"))
                row = result.fetchone()
                if row:
                    info["version"] = row[0]
            elif db_type == "oracle":
                result = conn.execute(text("SELECT * FROM v$version WHERE banner LIKE 'Oracle%'"))
                row = result.fetchone()
                if row:
                    info["version"] = row[0]
            elif db_type == "sqlserver":
                result = conn.execute(text("SELECT @@VERSION"))
                row = result.fetchone()
                if row:
                    info["version"] = row[0]
            elif db_type == "sqlite":
                result = conn.execute(text("SELECT sqlite_version()"))
                row = result.fetchone()
                if row:
                    info["version"] = f"SQLite {row[0]}"
            
            return info
        except Exception:
            return {"database_type": db_connection.db_type.value}
    
    def _get_all_tables(self, conn, db_connection: DatabaseConnection) -> List[Dict[str, Any]]:
        """获取所有表"""
        tables = []
        
        try:
            db_type = db_connection.db_type.value
            
            if db_type == "mysql":
                query = text("""
                    SELECT table_name, table_comment 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
            elif db_type == "postgresql":
                query = text("""
                    SELECT table_name, '' as table_comment
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
            elif db_type == "oracle":
                query = text("""
                    SELECT table_name, comments as table_comment
                    FROM user_tab_comments 
                    WHERE table_type = 'TABLE'
                    ORDER BY table_name
                """)
            elif db_type == "sqlserver":
                query = text("""
                    SELECT t.name as table_name, 
                           ISNULL(ep.value, '') as table_comment
                    FROM sys.tables t
                    LEFT JOIN sys.extended_properties ep 
                        ON ep.major_id = t.object_id 
                        AND ep.minor_id = 0 
                        AND ep.name = 'MS_Description'
                    ORDER BY t.name
                """)
            elif db_type == "sqlite":
                query = text("""
                    SELECT name as table_name, '' as table_comment
                    FROM sqlite_master 
                    WHERE type = 'table' 
                    AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
            else:
                return tables
            
            result = conn.execute(query)
            for row in result:
                tables.append({
                    "name": row[0],
                    "comment": row[1] if len(row) > 1 else "",
                    "type": "table"
                })
        
        except Exception as e:
            print(f"获取表列表失败: {e}")
        
        return tables
    
    def _get_all_views(self, conn, db_connection: DatabaseConnection) -> List[Dict[str, Any]]:
        """获取所有视图"""
        views = []
        
        try:
            db_type = db_connection.db_type.value
            
            if db_type == "mysql":
                query = text("""
                    SELECT table_name 
                    FROM information_schema.views 
                    WHERE table_schema = DATABASE()
                    ORDER BY table_name
                """)
            elif db_type == "postgresql":
                query = text("""
                    SELECT table_name 
                    FROM information_schema.views 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
            elif db_type == "oracle":
                query = text("""
                    SELECT view_name as table_name
                    FROM user_views
                    ORDER BY view_name
                """)
            elif db_type == "sqlserver":
                query = text("""
                    SELECT name as table_name
                    FROM sys.views
                    ORDER BY name
                """)
            elif db_type == "sqlite":
                query = text("""
                    SELECT name as table_name
                    FROM sqlite_master 
                    WHERE type = 'view'
                    ORDER BY name
                """)
            else:
                return views
            
            result = conn.execute(query)
            for row in result:
                views.append({
                    "name": row[0],
                    "type": "view"
                })
        
        except Exception as e:
            print(f"获取视图列表失败: {e}")
        
        return views 