"""SQL语句服务"""

import csv
import io
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import UploadFile

from app.models.sql_statement import SQLStatement, SQLStatementStatus
from app.models.db_connection import DatabaseConnection


class SQLStatementService:
    """SQL语句服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_sql_statement(self, statement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建SQL语句
        
        Args:
            statement_data: SQL语句数据
            
        Returns:
            创建结果
        """
        try:
            statement = SQLStatement(
                title=statement_data.get("title"),
                sql_content=statement_data.get("sql_content"),
                description=statement_data.get("description"),
                db_connection_id=statement_data.get("db_connection_id"),
                tags=statement_data.get("tags"),
                category=statement_data.get("category"),
                created_by=statement_data.get("created_by", "system")
            )
            
            self.db.add(statement)
            self.db.commit()
            self.db.refresh(statement)
            
            return {
                "success": True,
                "id": statement.id,
                "message": "SQL语句创建成功"
            }
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"创建SQL语句失败: {str(e)}"}
    
    def update_sql_statement(self, statement_id: int, statement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新SQL语句
        
        Args:
            statement_id: SQL语句ID
            statement_data: 更新数据
            
        Returns:
            更新结果
        """
        try:
            statement = self.db.query(SQLStatement).filter(
                SQLStatement.id == statement_id,
                SQLStatement.is_active == True
            ).first()
            
            if not statement:
                return {"success": False, "error": "SQL语句不存在"}
            
            # 如果SQL内容发生变化，创建新版本
            if "sql_content" in statement_data and statement_data["sql_content"] != statement.sql_content:
                self._create_new_version(statement, statement_data)
            else:
                # 只更新元数据
                for field, value in statement_data.items():
                    if hasattr(statement, field) and field != "sql_content":
                        setattr(statement, field, value)
            
            self.db.commit()
            
            return {"success": True, "message": "SQL语句更新成功"}
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"更新SQL语句失败: {str(e)}"}
    
    def get_sql_statement(self, statement_id: int) -> Optional[SQLStatement]:
        """获取SQL语句"""
        return self.db.query(SQLStatement).filter(
            SQLStatement.id == statement_id,
            SQLStatement.is_active == True
        ).first()
    
    def get_sql_statements(self, filters: Optional[Dict[str, Any]] = None) -> List[SQLStatement]:
        """
        获取SQL语句列表
        
        Args:
            filters: 过滤条件
            
        Returns:
            SQL语句列表
        """
        query = self.db.query(SQLStatement).filter(SQLStatement.is_active == True)
        
        if filters:
            if "db_connection_id" in filters:
                query = query.filter(SQLStatement.db_connection_id == filters["db_connection_id"])
            if "status" in filters:
                query = query.filter(SQLStatement.status == filters["status"])
            if "category" in filters:
                query = query.filter(SQLStatement.category == filters["category"])
            if "search" in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    SQLStatement.title.like(search_term) |
                    SQLStatement.description.like(search_term) |
                    SQLStatement.sql_content.like(search_term)
                )
        
        return query.order_by(desc(SQLStatement.created_at)).all()
    
    def delete_sql_statement(self, statement_id: int) -> Dict[str, Any]:
        """
        删除SQL语句（软删除）
        
        Args:
            statement_id: SQL语句ID
            
        Returns:
            删除结果
        """
        try:
            statement = self.db.query(SQLStatement).filter(
                SQLStatement.id == statement_id
            ).first()
            
            if not statement:
                return {"success": False, "error": "SQL语句不存在"}
            
            statement.is_active = False
            self.db.commit()
            
            return {"success": True, "message": "SQL语句删除成功"}
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"删除SQL语句失败: {str(e)}"}
    
    def get_sql_versions(self, statement_id: int) -> List[Dict[str, Any]]:
        """
        获取SQL语句的版本历史
        
        Args:
            statement_id: SQL语句ID
            
        Returns:
            版本历史列表
        """
        # 获取主版本
        main_statement = self.db.query(SQLStatement).filter(
            SQLStatement.id == statement_id
        ).first()
        
        if not main_statement:
            return []
        
        # 获取所有版本（包括主版本和子版本）
        versions = self.db.query(SQLStatement).filter(
            (SQLStatement.id == statement_id) |
            (SQLStatement.parent_id == statement_id)
        ).order_by(desc(SQLStatement.version)).all()
        
        return [
            {
                "id": version.id,
                "version": version.version,
                "title": version.title,
                "description": version.description,
                "sql_content": version.sql_content,
                "created_at": version.created_at,
                "is_current": version.id == statement_id
            }
            for version in versions
        ]
    
    def restore_version(self, statement_id: int, version_id: int) -> Dict[str, Any]:
        """
        恢复到指定版本
        
        Args:
            statement_id: 主SQL语句ID
            version_id: 要恢复的版本ID
            
        Returns:
            恢复结果
        """
        try:
            # 获取当前版本
            current_statement = self.db.query(SQLStatement).filter(
                SQLStatement.id == statement_id
            ).first()
            
            # 获取要恢复的版本
            target_version = self.db.query(SQLStatement).filter(
                SQLStatement.id == version_id
            ).first()
            
            if not current_statement or not target_version:
                return {"success": False, "error": "SQL语句或版本不存在"}
            
            # 创建新版本（基于目标版本）
            new_version_data = {
                "title": target_version.title,
                "sql_content": target_version.sql_content,
                "description": target_version.description
            }
            
            self._create_new_version(current_statement, new_version_data)
            self.db.commit()
            
            return {"success": True, "message": "版本恢复成功"}
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"版本恢复失败: {str(e)}"}
    
    def import_from_csv(self, file: UploadFile, default_db_connection_id: Optional[int] = None) -> Dict[str, Any]:
        """
        从CSV文件导入SQL语句
        
        Args:
            file: CSV文件
            default_db_connection_id: 默认数据库连接ID
            
        Returns:
            导入结果
        """
        try:
            # 读取CSV内容
            content = file.file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(content))
            
            imported_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    # 解析CSV行
                    title = row.get('title', row.get('标题', f'导入SQL-{row_num}'))
                    sql_content = row.get('sql_content', row.get('SQL语句', ''))
                    description = row.get('description', row.get('描述', ''))
                    
                    if not sql_content.strip():
                        errors.append(f"第{row_num}行: SQL内容为空")
                        continue
                    
                    # 创建SQL语句
                    statement = SQLStatement(
                        title=title,
                        sql_content=sql_content,
                        description=description,
                        db_connection_id=default_db_connection_id,
                        created_by="csv_import"
                    )
                    
                    self.db.add(statement)
                    imported_count += 1
                
                except Exception as e:
                    errors.append(f"第{row_num}行: {str(e)}")
            
            self.db.commit()
            
            result = {
                "success": True,
                "imported_count": imported_count,
                "message": f"成功导入 {imported_count} 条SQL语句"
            }
            
            if errors:
                result["errors"] = errors
            
            return result
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"导入失败: {str(e)}"}
    
    def export_to_csv(self, filters: Optional[Dict[str, Any]] = None) -> str:
        """
        导出SQL语句为CSV
        
        Args:
            filters: 过滤条件
            
        Returns:
            CSV内容
        """
        statements = self.get_sql_statements(filters)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        writer.writerow(['ID', '标题', 'SQL语句', '描述', '状态', '分类', '标签', '创建时间'])
        
        # 写入数据行
        for stmt in statements:
            writer.writerow([
                stmt.id,
                stmt.title or '',
                stmt.sql_content or '',
                stmt.description or '',
                stmt.status.value if stmt.status else '',
                stmt.category or '',
                stmt.tags or '',
                stmt.created_at.strftime('%Y-%m-%d %H:%M:%S') if stmt.created_at else ''
            ])
        
        return output.getvalue()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取SQL语句统计信息
        
        Returns:
            统计信息
        """
        total_count = self.db.query(SQLStatement).filter(SQLStatement.is_active == True).count()
        
        status_counts = {}
        for status in SQLStatementStatus:
            count = self.db.query(SQLStatement).filter(
                SQLStatement.is_active == True,
                SQLStatement.status == status
            ).count()
            status_counts[status.value] = count
        
        # 按数据库连接分组统计
        db_stats = self.db.query(
            DatabaseConnection.name,
            self.db.func.count(SQLStatement.id).label('count')
        ).join(
            SQLStatement, DatabaseConnection.id == SQLStatement.db_connection_id
        ).filter(
            SQLStatement.is_active == True
        ).group_by(DatabaseConnection.name).all()
        
        return {
            "total_count": total_count,
            "status_distribution": status_counts,
            "database_distribution": {name: count for name, count in db_stats}
        }
    
    def _create_new_version(self, current_statement: SQLStatement, new_data: Dict[str, Any]):
        """创建新版本"""
        # 更新当前版本
        current_statement.version += 1
        
        for field, value in new_data.items():
            if hasattr(current_statement, field):
                setattr(current_statement, field, value)
        
        # 重置状态为草稿（因为内容发生了变化）
        if "sql_content" in new_data:
            current_statement.status = SQLStatementStatus.DRAFT
            current_statement.last_reviewed_at = None 