"""SQL解析器"""

import re
import sqlparse
from typing import List, Set, Dict, Any
from sqlparse.sql import IdentifierList, Identifier, Function
from sqlparse.tokens import Keyword, DML

try:
    from sql_metadata import get_query_tables, get_query_columns
    SQL_METADATA_AVAILABLE = True
except ImportError:
    SQL_METADATA_AVAILABLE = False


class SQLParser:
    """SQL解析器，用于提取SQL中的表名和视图名"""
    
    def __init__(self):
        self.table_names: Set[str] = set()
        self.view_names: Set[str] = set()
    
    def parse(self, sql: str) -> Dict[str, List[str]]:
        """
        解析SQL语句，提取表名和视图名
        
        Args:
            sql: SQL语句
            
        Returns:
            包含表名和视图名的字典
        """
        self.table_names.clear()
        self.view_names.clear()
        
        try:
            # 优先使用sql-metadata库
            if SQL_METADATA_AVAILABLE:
                return self._extract_with_sql_metadata(sql)
            else:
                # 回退到原有方法
                return self._extract_with_sqlparse(sql)
        except Exception as e:
            print(f"SQL解析失败，使用备选方案: {e}")
            # 如果解析失败，使用正则表达式作为备选方案
            return self._fallback_parse(sql)
    
    def _extract_with_sql_metadata(self, sql: str) -> Dict[str, List[str]]:
        """使用sql-metadata库提取表名"""
        try:
            # 获取所有表名
            tables = get_query_tables(sql)
            
            # 清理表名（移除schema前缀等）
            cleaned_tables = []
            for table in tables:
                # 处理schema.table格式
                if '.' in table:
                    table = table.split('.')[-1]
                # 移除引号
                table = table.strip('"').strip("'").strip('`')
                if table and self._is_valid_identifier(table):
                    cleaned_tables.append(table)
            
            print(f"sql-metadata提取到的表名: {cleaned_tables}")
            
            return {
                "tables": cleaned_tables,
                "views": []  # sql-metadata无法区分表和视图，统一当作表处理
            }
        except Exception as e:
            print(f"sql-metadata解析失败: {e}")
            # 回退到sqlparse方法
            return self._extract_with_sqlparse(sql)
    
    def _extract_with_sqlparse(self, sql: str) -> Dict[str, List[str]]:
        """使用sqlparse库提取表名（原有方法的改进版）"""
        try:
            # 解析SQL语句
            parsed = sqlparse.parse(sql)
            
            for statement in parsed:
                self._extract_from_statement_improved(statement)
            
            return {
                "tables": list(self.table_names),
                "views": list(self.view_names)
            }
        except Exception as e:
            print(f"sqlparse解析失败: {e}")
            return self._fallback_parse(sql)
    
    def _extract_from_statement_improved(self, statement):
        """改进的表名提取方法"""
        # 将SQL转换为字符串进行处理
        sql_str = str(statement)
        
        # 使用正则表达式提取FROM和JOIN后的表名
        patterns = [
            r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)\s*(?:[a-zA-Z_][a-zA-Z0-9_]*)?',
            r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)\s*(?:[a-zA-Z_][a-zA-Z0-9_]*)?',
            r'\bINNER\s+JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)\s*(?:[a-zA-Z_][a-zA-Z0-9_]*)?',
            r'\bLEFT\s+JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)\s*(?:[a-zA-Z_][a-zA-Z0-9_]*)?',
            r'\bRIGHT\s+JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)\s*(?:[a-zA-Z_][a-zA-Z0-9_]*)?',
            r'\bFULL\s+JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)\s*(?:[a-zA-Z_][a-zA-Z0-9_]*)?',
            r'\bINTO\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, sql_str, re.IGNORECASE)
            for match in matches:
                table_name = match.group(1)
                self._extract_table_name(table_name)
    
    def _extract_from_statement(self, statement):
        """从SQL语句中提取表名（原有方法，保留作为备用）"""
        # 使用更简单的方法，直接查找FROM和JOIN后的标识符
        tokens = list(statement.flatten())
        
        for i, token in enumerate(tokens):
            if token.ttype is Keyword:
                token_upper = token.value.upper()
                if token_upper in ('FROM', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL'):
                    # 查找下一个非空白、非关键字的token
                    for j in range(i + 1, len(tokens)):
                        next_token = tokens[j]
                        if next_token.ttype in (None, sqlparse.tokens.Name):
                            # 找到可能的表名
                            self._extract_table_name(next_token.value)
                            break
                        elif next_token.ttype is Keyword:
                            # 遇到下一个关键字，停止查找
                            break
    
    def _is_subselect(self, token):
        """检查是否为子查询"""
        if not hasattr(token, 'tokens'):
            return False
        
        for sub_token in token.tokens:
            if sub_token.ttype is DML and sub_token.value.upper() == 'SELECT':
                return True
        return False
    
    def _extract_table_name(self, token_value: str):
        """提取表名"""
        # 移除引号和空格
        table_name = token_value.strip().strip('"').strip("'").strip('`')
        
        # 处理别名 (table_name alias 或 table_name AS alias)
        parts = table_name.split()
        if len(parts) >= 2 and parts[1].upper() != 'AS':
            table_name = parts[0]
        elif len(parts) >= 3 and parts[1].upper() == 'AS':
            table_name = parts[0]
        
        # 处理schema.table格式
        if '.' in table_name:
            table_name = table_name.split('.')[-1]
        
        # 过滤掉关键字和特殊字符
        if table_name and not self._is_keyword(table_name) and self._is_valid_identifier(table_name):
            self.table_names.add(table_name)
    
    def _is_keyword(self, word: str) -> bool:
        """检查是否为SQL关键字"""
        keywords = {
            'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER',
            'ON', 'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'IS', 'NULL',
            'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'UNION', 'ALL', 'DISTINCT',
            'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'INDEX', 'TABLE',
            'VIEW', 'DATABASE', 'SCHEMA', 'AS', 'ASC', 'DESC', 'COUNT', 'SUM', 'AVG',
            'MIN', 'MAX', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'IF', 'IFNULL', 'COALESCE'
        }
        return word.upper() in keywords
    
    def _is_valid_identifier(self, identifier: str) -> bool:
        """检查是否为有效的标识符"""
        if not identifier:
            return False
        
        # 基本的标识符验证
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, identifier))
    
    def _fallback_parse(self, sql: str) -> Dict[str, List[str]]:
        """备选解析方法，使用正则表达式"""
        tables = set()
        
        # 更全面的正则表达式模式
        patterns = [
            r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'\bINNER\s+JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'\bLEFT\s+JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'\bRIGHT\s+JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'\bFULL\s+JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'\bINTO\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, sql, re.IGNORECASE)
            for match in matches:
                table_name = match.group(1)
                if '.' in table_name:
                    table_name = table_name.split('.')[-1]
                # 移除引号
                table_name = table_name.strip('"').strip("'").strip('`')
                if table_name and self._is_valid_identifier(table_name):
                    tables.add(table_name)
        
        print(f"备选方案提取到的表名: {list(tables)}")
        
        return {
            "tables": list(tables),
            "views": []  # 正则表达式方法无法区分表和视图
        }
    
    def get_sql_type(self, sql: str) -> str:
        """获取SQL语句类型"""
        sql_upper = sql.strip().upper()
        
        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'
        elif sql_upper.startswith('CREATE'):
            return 'CREATE'
        elif sql_upper.startswith('DROP'):
            return 'DROP'
        elif sql_upper.startswith('ALTER'):
            return 'ALTER'
        else:
            return 'UNKNOWN' 