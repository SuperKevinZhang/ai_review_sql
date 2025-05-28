"""数据库模式提取器 - 生成完整的CREATE TABLE DDL语句"""

from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text, MetaData, Table, Column, inspect
from sqlalchemy.engine import Engine, Inspector
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import mysql, postgresql, sqlite, mssql, oracle
import logging

from app.models.db_connection import DatabaseType

logger = logging.getLogger(__name__)


class SchemaExtractor:
    """数据库模式提取器，用于生成完整的CREATE TABLE DDL语句"""
    
    def __init__(self, engine: Engine, db_type: DatabaseType):
        self.engine = engine
        self.db_type = db_type
        self.inspector = inspect(engine)
        self.metadata = MetaData()
    
    def get_table_schema(self, table_names: List[str]) -> Dict[str, Any]:
        """
        获取指定表的完整CREATE TABLE DDL语句
        
        Args:
            table_names: 表名列表
            
        Returns:
            包含表结构DDL的字典
        """
        schema_info = {
            "tables": {},
            "total_tables": 0,
            "found_tables": 0,
            "missing_tables": []
        }
        
        try:
            # 获取数据库中所有表名
            available_tables = self.inspector.get_table_names()
            logger.info(f"数据库中可用的表: {available_tables}")
            
            for table_name in table_names:
                if table_name in available_tables:
                    try:
                        ddl = self._generate_create_table_ddl(table_name)
                        if ddl:
                            schema_info["tables"][table_name] = {
                                "ddl": ddl,
                                "type": "table"
                            }
                            schema_info["found_tables"] += 1
                            logger.info(f"成功生成表 {table_name} 的DDL")
                        else:
                            logger.warning(f"无法生成表 {table_name} 的DDL")
                            schema_info["missing_tables"].append(table_name)
                    except Exception as e:
                        logger.error(f"生成表 {table_name} DDL时出错: {e}")
                        schema_info["missing_tables"].append(table_name)
                else:
                    logger.warning(f"表 {table_name} 在数据库中不存在")
                    schema_info["missing_tables"].append(table_name)
            
            schema_info["total_tables"] = len(table_names)
            
        except SQLAlchemyError as e:
            logger.error(f"获取表结构时出错: {e}")
        
        return schema_info
    
    def _generate_create_table_ddl(self, table_name: str) -> Optional[str]:
        """
        使用SQLAlchemy Inspector生成CREATE TABLE DDL语句
        
        Args:
            table_name: 表名
            
        Returns:
            CREATE TABLE DDL语句
        """
        try:
            # 使用Inspector反射表结构
            table = Table(table_name, self.metadata, autoload_with=self.engine)
            
            # 根据数据库类型选择方言
            dialect = self._get_dialect()
            
            # 生成CREATE TABLE语句
            create_table_stmt = CreateTable(table)
            ddl = str(create_table_stmt.compile(dialect=dialect, compile_kwargs={"literal_binds": True}))
            
            # 添加索引信息
            indexes_ddl = self._generate_indexes_ddl(table_name, dialect)
            if indexes_ddl:
                ddl += "\n\n" + indexes_ddl
            
            return ddl
            
        except Exception as e:
            logger.error(f"生成表 {table_name} DDL时出错: {e}")
            # 尝试备用方法
            return self._generate_ddl_fallback(table_name)
    
    def _get_dialect(self):
        """根据数据库类型获取SQLAlchemy方言"""
        if self.db_type == DatabaseType.MYSQL:
            return mysql.dialect()
        elif self.db_type == DatabaseType.POSTGRESQL:
            return postgresql.dialect()
        elif self.db_type == DatabaseType.SQLITE:
            return sqlite.dialect()
        elif self.db_type == DatabaseType.SQLSERVER:
            return mssql.dialect()
        elif self.db_type == DatabaseType.ORACLE:
            return oracle.dialect()
        else:
            # 默认使用通用方言
            return None
    
    def _generate_indexes_ddl(self, table_name: str, dialect) -> str:
        """生成索引的DDL语句"""
        try:
            indexes = self.inspector.get_indexes(table_name)
            index_ddls = []
            
            for index in indexes:
                index_name = index['name']
                columns = index['column_names']
                unique = index.get('unique', False)
                
                if unique:
                    ddl = f"CREATE UNIQUE INDEX {index_name} ON {table_name} ({', '.join(columns)});"
                else:
                    ddl = f"CREATE INDEX {index_name} ON {table_name} ({', '.join(columns)});"
                
                index_ddls.append(ddl)
            
            return '\n'.join(index_ddls)
            
        except Exception as e:
            logger.warning(f"生成表 {table_name} 索引DDL时出错: {e}")
            return ""
    
    def _generate_ddl_fallback(self, table_name: str) -> Optional[str]:
        """
        备用方法：使用原始SQL查询生成DDL
        """
        try:
            with self.engine.connect() as conn:
                if self.db_type == DatabaseType.MYSQL:
                    result = conn.execute(text(f"SHOW CREATE TABLE {table_name}"))
                    row = result.fetchone()
                    if row:
                        return row[1]  # CREATE TABLE语句在第二列
                
                elif self.db_type == DatabaseType.SQLITE:
                    result = conn.execute(text(
                        "SELECT sql FROM sqlite_master WHERE type='table' AND name=:table_name"
                    ), {"table_name": table_name})
                    row = result.fetchone()
                    if row:
                        return row[0]
                
                elif self.db_type == DatabaseType.POSTGRESQL:
                    # PostgreSQL需要更复杂的查询来重建CREATE TABLE
                    return self._generate_postgresql_ddl(conn, table_name)
                
                elif self.db_type == DatabaseType.SQLSERVER:
                    # SQL Server需要更复杂的查询来重建CREATE TABLE
                    return self._generate_sqlserver_ddl(conn, table_name)
                
                elif self.db_type == DatabaseType.ORACLE:
                    # Oracle需要更复杂的查询来重建CREATE TABLE
                    return self._generate_oracle_ddl(conn, table_name)
                    
        except Exception as e:
            logger.error(f"备用方法生成表 {table_name} DDL时出错: {e}")
        
        return None
    
    def _generate_postgresql_ddl(self, conn, table_name: str) -> str:
        """为PostgreSQL生成CREATE TABLE DDL"""
        try:
            # 获取列信息
            columns_query = text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """)
            
            columns_result = conn.execute(columns_query, {"table_name": table_name})
            columns = []
            
            for row in columns_result:
                col_def = f"  {row.column_name} {row.data_type}"
                
                # 添加长度/精度
                if row.character_maximum_length:
                    col_def += f"({row.character_maximum_length})"
                elif row.numeric_precision and row.numeric_scale:
                    col_def += f"({row.numeric_precision},{row.numeric_scale})"
                elif row.numeric_precision:
                    col_def += f"({row.numeric_precision})"
                
                # 添加NOT NULL
                if row.is_nullable == 'NO':
                    col_def += " NOT NULL"
                
                # 添加默认值
                if row.column_default:
                    col_def += f" DEFAULT {row.column_default}"
                
                columns.append(col_def)
            
            # 获取主键信息
            pk_query = text("""
                SELECT column_name
                FROM information_schema.key_column_usage
                WHERE table_name = :table_name
                AND constraint_name IN (
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE table_name = :table_name
                    AND constraint_type = 'PRIMARY KEY'
                )
                ORDER BY ordinal_position
            """)
            
            pk_result = conn.execute(pk_query, {"table_name": table_name})
            pk_columns = [row.column_name for row in pk_result]
            
            if pk_columns:
                columns.append(f"  PRIMARY KEY ({', '.join(pk_columns)})")
            
            ddl = f"CREATE TABLE {table_name} (\n" + ",\n".join(columns) + "\n);"
            return ddl
            
        except Exception as e:
            logger.error(f"生成PostgreSQL DDL时出错: {e}")
            return f"-- 无法生成表 {table_name} 的DDL: {e}"
    
    def _generate_sqlserver_ddl(self, conn, table_name: str) -> str:
        """为SQL Server生成CREATE TABLE DDL"""
        try:
            # 获取列信息
            columns_query = text("""
                SELECT 
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    c.character_maximum_length,
                    c.numeric_precision,
                    c.numeric_scale
                FROM information_schema.columns c
                WHERE c.table_name = :table_name
                ORDER BY c.ordinal_position
            """)
            
            columns_result = conn.execute(columns_query, {"table_name": table_name})
            columns = []
            
            for row in columns_result:
                col_def = f"  [{row.column_name}] {row.data_type}"
                
                # 添加长度/精度
                if row.character_maximum_length and row.character_maximum_length != -1:
                    col_def += f"({row.character_maximum_length})"
                elif row.numeric_precision and row.numeric_scale:
                    col_def += f"({row.numeric_precision},{row.numeric_scale})"
                elif row.numeric_precision:
                    col_def += f"({row.numeric_precision})"
                
                # 添加NOT NULL
                if row.is_nullable == 'NO':
                    col_def += " NOT NULL"
                
                # 添加默认值
                if row.column_default:
                    col_def += f" DEFAULT {row.column_default}"
                
                columns.append(col_def)
            
            ddl = f"CREATE TABLE [{table_name}] (\n" + ",\n".join(columns) + "\n);"
            return ddl
            
        except Exception as e:
            logger.error(f"生成SQL Server DDL时出错: {e}")
            return f"-- 无法生成表 {table_name} 的DDL: {e}"
    
    def _generate_oracle_ddl(self, conn, table_name: str) -> str:
        """为Oracle生成CREATE TABLE DDL"""
        try:
            # 获取列信息
            columns_query = text("""
                SELECT 
                    column_name,
                    data_type,
                    nullable,
                    data_default,
                    data_length,
                    data_precision,
                    data_scale,
                    char_length
                FROM user_tab_columns 
                WHERE table_name = UPPER(:table_name)
                ORDER BY column_id
            """)
            
            columns_result = conn.execute(columns_query, {"table_name": table_name})
            columns = []
            
            for row in columns_result:
                col_def = f"  {row.column_name} {row.data_type}"
                
                # 添加长度/精度
                if row.data_type in ('VARCHAR2', 'CHAR', 'NVARCHAR2', 'NCHAR'):
                    if row.char_length:
                        col_def += f"({row.char_length})"
                    elif row.data_length:
                        col_def += f"({row.data_length})"
                elif row.data_type == 'NUMBER':
                    if row.data_precision and row.data_scale:
                        col_def += f"({row.data_precision},{row.data_scale})"
                    elif row.data_precision:
                        col_def += f"({row.data_precision})"
                elif row.data_type in ('RAW', 'VARCHAR'):
                    if row.data_length:
                        col_def += f"({row.data_length})"
                
                # 添加NOT NULL
                if row.nullable == 'N':
                    col_def += " NOT NULL"
                
                # 添加默认值
                if row.data_default:
                    default_value = row.data_default.strip()
                    col_def += f" DEFAULT {default_value}"
                
                columns.append(col_def)
            
            # 获取主键信息
            pk_query = text("""
                SELECT column_name
                FROM user_cons_columns
                WHERE constraint_name = (
                    SELECT constraint_name
                    FROM user_constraints
                    WHERE table_name = UPPER(:table_name)
                    AND constraint_type = 'P'
                )
                ORDER BY position
            """)
            
            pk_result = conn.execute(pk_query, {"table_name": table_name})
            pk_columns = [row.column_name for row in pk_result]
            
            if pk_columns:
                columns.append(f"  PRIMARY KEY ({', '.join(pk_columns)})")
            
            ddl = f"CREATE TABLE {table_name.upper()} (\n" + ",\n".join(columns) + "\n);"
            
            # 添加注释信息
            comments_ddl = self._generate_oracle_comments_ddl(conn, table_name)
            if comments_ddl:
                ddl += "\n\n" + comments_ddl
            
            return ddl
            
        except Exception as e:
            logger.error(f"生成Oracle DDL时出错: {e}")
            return f"-- 无法生成表 {table_name} 的DDL: {e}"
    
    def _generate_oracle_comments_ddl(self, conn, table_name: str) -> str:
        """为Oracle生成注释DDL"""
        try:
            comments_ddl = []
            
            # 表注释
            table_comment_query = text("""
                SELECT comments
                FROM user_tab_comments
                WHERE table_name = UPPER(:table_name)
                AND comments IS NOT NULL
            """)
            
            table_comment_result = conn.execute(table_comment_query, {"table_name": table_name})
            table_comment_row = table_comment_result.fetchone()
            
            if table_comment_row and table_comment_row.comments:
                comments_ddl.append(f"COMMENT ON TABLE {table_name.upper()} IS '{table_comment_row.comments}';")
            
            # 列注释
            column_comments_query = text("""
                SELECT column_name, comments
                FROM user_col_comments
                WHERE table_name = UPPER(:table_name)
                AND comments IS NOT NULL
            """)
            
            column_comments_result = conn.execute(column_comments_query, {"table_name": table_name})
            
            for row in column_comments_result:
                comments_ddl.append(f"COMMENT ON COLUMN {table_name.upper()}.{row.column_name} IS '{row.comments}';")
            
            return '\n'.join(comments_ddl)
            
        except Exception as e:
            logger.warning(f"生成Oracle注释DDL时出错: {e}")
            return "" 