"""数据库模式提取器"""

from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.models.db_connection import DatabaseType


class SchemaExtractor:
    """数据库模式提取器，用于获取表结构、索引等信息"""
    
    def __init__(self, engine: Engine, db_type: DatabaseType):
        self.engine = engine
        self.db_type = db_type
        self.metadata = MetaData()
    
    def get_table_schema(self, table_names: List[str]) -> Dict[str, Any]:
        """
        获取指定表的结构信息
        
        Args:
            table_names: 表名列表
            
        Returns:
            包含表结构信息的字典
        """
        schema_info = {
            "tables": [],
            "views": []
        }
        
        try:
            with self.engine.connect() as conn:
                for table_name in table_names:
                    # 检查是否为表或视图
                    if self._is_table(conn, table_name):
                        table_info = self._get_table_info(conn, table_name)
                        if table_info:
                            schema_info["tables"].append(table_info)
                    elif self._is_view(conn, table_name):
                        view_info = self._get_view_info(conn, table_name)
                        if view_info:
                            schema_info["views"].append(view_info)
        
        except SQLAlchemyError as e:
            print(f"获取表结构时出错: {e}")
        
        return schema_info
    
    def _is_table(self, conn, table_name: str) -> bool:
        """检查是否为表"""
        try:
            if self.db_type == DatabaseType.MYSQL:
                query = text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = :table_name 
                    AND table_type = 'BASE TABLE'
                """)
            elif self.db_type == DatabaseType.POSTGRESQL:
                query = text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name 
                    AND table_type = 'BASE TABLE'
                """)
            elif self.db_type == DatabaseType.SQLSERVER:
                query = text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_name = :table_name 
                    AND table_type = 'BASE TABLE'
                """)
            elif self.db_type == DatabaseType.SQLITE:
                query = text("""
                    SELECT COUNT(*) as count 
                    FROM sqlite_master 
                    WHERE type = 'table' 
                    AND name = :table_name
                """)
            else:
                return False
            
            result = conn.execute(query, {"table_name": table_name})
            return result.scalar() > 0
        
        except Exception:
            return False
    
    def _is_view(self, conn, view_name: str) -> bool:
        """检查是否为视图"""
        try:
            if self.db_type == DatabaseType.MYSQL:
                query = text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.views 
                    WHERE table_schema = DATABASE() 
                    AND table_name = :view_name
                """)
            elif self.db_type == DatabaseType.POSTGRESQL:
                query = text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.views 
                    WHERE table_schema = 'public' 
                    AND table_name = :view_name
                """)
            elif self.db_type == DatabaseType.SQLSERVER:
                query = text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.views 
                    WHERE table_name = :view_name
                """)
            elif self.db_type == DatabaseType.SQLITE:
                query = text("""
                    SELECT COUNT(*) as count 
                    FROM sqlite_master 
                    WHERE type = 'view' 
                    AND name = :view_name
                """)
            else:
                return False
            
            result = conn.execute(query, {"view_name": view_name})
            return result.scalar() > 0
        
        except Exception:
            return False
    
    def _get_table_info(self, conn, table_name: str) -> Optional[Dict[str, Any]]:
        """获取表的详细信息"""
        try:
            table_info = {
                "name": table_name,
                "type": "table",
                "columns": self._get_columns_info(conn, table_name),
                "indexes": self._get_indexes_info(conn, table_name),
                "primary_keys": self._get_primary_keys(conn, table_name),
                "foreign_keys": self._get_foreign_keys(conn, table_name)
            }
            return table_info
        
        except Exception as e:
            print(f"获取表 {table_name} 信息时出错: {e}")
            return None
    
    def _get_view_info(self, conn, view_name: str) -> Optional[Dict[str, Any]]:
        """获取视图的详细信息"""
        try:
            view_info = {
                "name": view_name,
                "type": "view",
                "columns": self._get_columns_info(conn, view_name),
                "definition": self._get_view_definition(conn, view_name)
            }
            return view_info
        
        except Exception as e:
            print(f"获取视图 {view_name} 信息时出错: {e}")
            return None
    
    def _get_columns_info(self, conn, table_name: str) -> List[Dict[str, Any]]:
        """获取列信息"""
        columns = []
        
        try:
            if self.db_type == DatabaseType.MYSQL:
                query = text("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        column_comment,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns 
                    WHERE table_schema = DATABASE() 
                    AND table_name = :table_name
                    ORDER BY ordinal_position
                """)
            elif self.db_type == DatabaseType.POSTGRESQL:
                query = text("""
                    SELECT 
                        c.column_name,
                        c.data_type,
                        c.is_nullable,
                        c.column_default,
                        COALESCE(pgd.description, '') as column_comment,
                        c.character_maximum_length,
                        c.numeric_precision,
                        c.numeric_scale
                    FROM information_schema.columns c
                    LEFT JOIN pg_catalog.pg_statio_all_tables st 
                        ON c.table_schema = st.schemaname 
                        AND c.table_name = st.relname
                    LEFT JOIN pg_catalog.pg_description pgd 
                        ON pgd.objoid = st.relid 
                        AND pgd.objsubid = c.ordinal_position
                    WHERE c.table_schema = 'public' 
                    AND c.table_name = :table_name
                    ORDER BY c.ordinal_position
                """)
            elif self.db_type == DatabaseType.SQLITE:
                # SQLite使用PRAGMA命令
                query = text(f"PRAGMA table_info({table_name})")
            else:
                return columns
            
            result = conn.execute(query, {"table_name": table_name})
            
            if self.db_type == DatabaseType.SQLITE:
                for row in result:
                    columns.append({
                        "name": row[1],
                        "type": row[2],
                        "is_nullable": not bool(row[3]),
                        "default_value": row[4],
                        "comment": "",
                        "max_length": None,
                        "precision": None,
                        "scale": None
                    })
            else:
                for row in result:
                    columns.append({
                        "name": row[0],
                        "type": row[1],
                        "is_nullable": row[2] == 'YES',
                        "default_value": row[3],
                        "comment": row[4] if len(row) > 4 else "",
                        "max_length": row[5] if len(row) > 5 else None,
                        "precision": row[6] if len(row) > 6 else None,
                        "scale": row[7] if len(row) > 7 else None
                    })
        
        except Exception as e:
            print(f"获取表 {table_name} 列信息时出错: {e}")
        
        return columns
    
    def _get_indexes_info(self, conn, table_name: str) -> List[Dict[str, Any]]:
        """获取索引信息"""
        indexes = []
        
        try:
            if self.db_type == DatabaseType.MYSQL:
                query = text("""
                    SELECT 
                        index_name,
                        column_name,
                        non_unique,
                        seq_in_index
                    FROM information_schema.statistics 
                    WHERE table_schema = DATABASE() 
                    AND table_name = :table_name
                    ORDER BY index_name, seq_in_index
                """)
                result = conn.execute(query, {"table_name": table_name})
                
                index_dict = {}
                for row in result:
                    index_name = row[0]
                    if index_name not in index_dict:
                        index_dict[index_name] = {
                            "name": index_name,
                            "columns": [],
                            "is_unique": row[2] == 0
                        }
                    index_dict[index_name]["columns"].append(row[1])
                
                indexes = list(index_dict.values())
            
            elif self.db_type == DatabaseType.SQLITE:
                # SQLite索引信息
                query = text(f"PRAGMA index_list({table_name})")
                result = conn.execute(query)
                
                for row in result:
                    index_name = row[1]
                    is_unique = bool(row[2])
                    
                    # 获取索引列
                    col_query = text(f"PRAGMA index_info({index_name})")
                    col_result = conn.execute(col_query)
                    columns = [col_row[2] for col_row in col_result]
                    
                    indexes.append({
                        "name": index_name,
                        "columns": columns,
                        "is_unique": is_unique
                    })
        
        except Exception as e:
            print(f"获取表 {table_name} 索引信息时出错: {e}")
        
        return indexes
    
    def _get_primary_keys(self, conn, table_name: str) -> List[str]:
        """获取主键信息"""
        primary_keys = []
        
        try:
            if self.db_type == DatabaseType.MYSQL:
                query = text("""
                    SELECT column_name 
                    FROM information_schema.key_column_usage 
                    WHERE table_schema = DATABASE() 
                    AND table_name = :table_name 
                    AND constraint_name = 'PRIMARY'
                    ORDER BY ordinal_position
                """)
                result = conn.execute(query, {"table_name": table_name})
                primary_keys = [row[0] for row in result]
            
            elif self.db_type == DatabaseType.SQLITE:
                query = text(f"PRAGMA table_info({table_name})")
                result = conn.execute(query)
                primary_keys = [row[1] for row in result if row[5]]  # pk字段为1表示主键
        
        except Exception as e:
            print(f"获取表 {table_name} 主键信息时出错: {e}")
        
        return primary_keys
    
    def _get_foreign_keys(self, conn, table_name: str) -> List[Dict[str, Any]]:
        """获取外键信息"""
        foreign_keys = []
        
        try:
            if self.db_type == DatabaseType.MYSQL:
                query = text("""
                    SELECT 
                        column_name,
                        referenced_table_name,
                        referenced_column_name,
                        constraint_name
                    FROM information_schema.key_column_usage 
                    WHERE table_schema = DATABASE() 
                    AND table_name = :table_name 
                    AND referenced_table_name IS NOT NULL
                """)
                result = conn.execute(query, {"table_name": table_name})
                
                for row in result:
                    foreign_keys.append({
                        "column": row[0],
                        "referenced_table": row[1],
                        "referenced_column": row[2],
                        "constraint_name": row[3]
                    })
            
            elif self.db_type == DatabaseType.SQLITE:
                query = text(f"PRAGMA foreign_key_list({table_name})")
                result = conn.execute(query)
                
                for row in result:
                    foreign_keys.append({
                        "column": row[3],
                        "referenced_table": row[2],
                        "referenced_column": row[4],
                        "constraint_name": f"fk_{table_name}_{row[0]}"
                    })
        
        except Exception as e:
            print(f"获取表 {table_name} 外键信息时出错: {e}")
        
        return foreign_keys
    
    def _get_view_definition(self, conn, view_name: str) -> str:
        """获取视图定义"""
        try:
            if self.db_type == DatabaseType.MYSQL:
                query = text("""
                    SELECT view_definition 
                    FROM information_schema.views 
                    WHERE table_schema = DATABASE() 
                    AND table_name = :view_name
                """)
                result = conn.execute(query, {"view_name": view_name})
                row = result.fetchone()
                return row[0] if row else ""
            
            elif self.db_type == DatabaseType.SQLITE:
                query = text("""
                    SELECT sql 
                    FROM sqlite_master 
                    WHERE type = 'view' 
                    AND name = :view_name
                """)
                result = conn.execute(query, {"view_name": view_name})
                row = result.fetchone()
                return row[0] if row else ""
        
        except Exception as e:
            print(f"获取视图 {view_name} 定义时出错: {e}")
        
        return "" 