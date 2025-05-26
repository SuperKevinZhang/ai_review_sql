"""数据库连接服务"""

from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.db_connection import DatabaseConnection
from app.core.encryption import EncryptionService
from app.core.schema_extractor import SchemaExtractor


class DatabaseConnectionService:
    """数据库连接服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.encryption_service = EncryptionService()
    
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
            
            with engine.connect() as conn:
                # 执行简单查询测试连接
                if db_connection.db_type.value == "sqlite":
                    result = conn.execute(text("SELECT 1"))
                else:
                    result = conn.execute(text("SELECT 1 as test"))
                
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
            
            # 构建连接字符串
            connection_string = self._build_connection_string(db_connection)
            
            # 创建引擎并测试连接
            engine = create_engine(connection_string, pool_timeout=10)
            
            with engine.connect() as conn:
                # 执行简单查询测试连接
                if db_connection.db_type.value == "sqlite":
                    result = conn.execute(text("SELECT 1"))
                else:
                    result = conn.execute(text("SELECT 1 as test"))
                
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
            
            # 构建连接字符串
            connection_string = self._build_connection_string(db_connection)
            
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
            
            # 构建连接字符串
            connection_string = self._build_connection_string(db_connection)
            
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

    def _build_connection_string_for_object(self, db_connection: DatabaseConnection) -> str:
        """构建数据库连接字符串（用于测试对象，密码未加密）"""
        password = db_connection.password or ""
        
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
    
    def _get_database_info(self, conn, db_connection: DatabaseConnection) -> Dict[str, Any]:
        """获取数据库基本信息"""
        try:
            info = {
                "database_type": db_connection.db_type.value,
                "database_name": db_connection.database_name
            }
            
            if db_connection.db_type.value == "mysql":
                result = conn.execute(text("SELECT VERSION() as version"))
                row = result.fetchone()
                if row:
                    info["version"] = row[0]
            elif db_connection.db_type.value == "postgresql":
                result = conn.execute(text("SELECT version()"))
                row = result.fetchone()
                if row:
                    info["version"] = row[0]
            elif db_connection.db_type.value == "sqlite":
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
            if db_connection.db_type.value == "mysql":
                query = text("""
                    SELECT table_name, table_comment 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
            elif db_connection.db_type.value == "postgresql":
                query = text("""
                    SELECT table_name, '' as table_comment
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
            elif db_connection.db_type.value == "sqlite":
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
            if db_connection.db_type.value == "mysql":
                query = text("""
                    SELECT table_name 
                    FROM information_schema.views 
                    WHERE table_schema = DATABASE()
                    ORDER BY table_name
                """)
            elif db_connection.db_type.value == "postgresql":
                query = text("""
                    SELECT table_name 
                    FROM information_schema.views 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
            elif db_connection.db_type.value == "sqlite":
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