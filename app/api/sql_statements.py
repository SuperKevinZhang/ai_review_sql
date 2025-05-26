"""SQL语句相关API"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.models.database import get_db
from app.models.sql_statement import SQLStatement
from app.services.sql_statement_service import SQLStatementService

router = APIRouter()


class SQLStatementCreate(BaseModel):
    title: str
    sql_content: str
    description: Optional[str] = None
    db_connection_id: Optional[int] = None
    tags: Optional[str] = None
    category: Optional[str] = None


class SQLStatementUpdate(BaseModel):
    title: Optional[str] = None
    sql_content: Optional[str] = None
    description: Optional[str] = None
    db_connection_id: Optional[int] = None
    tags: Optional[str] = None
    category: Optional[str] = None


@router.get("/")
async def get_sql_statements(
    page: int = 1,
    page_size: int = 10,
    order_by: str = "created_at",
    order_dir: str = "desc",
    db: Session = Depends(get_db)
):
    """获取SQL语句列表（支持分页）"""
    from sqlalchemy import desc, asc
    
    # 构建查询
    query = db.query(SQLStatement).filter(SQLStatement.is_active == True)
    
    # 排序
    if hasattr(SQLStatement, order_by):
        order_column = getattr(SQLStatement, order_by)
        if order_dir.lower() == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
    else:
        query = query.order_by(desc(SQLStatement.created_at))
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    statements = query.offset(offset).limit(page_size).all()
    
    # 计算总页数
    pages = (total + page_size - 1) // page_size
    
    return {
        "items": [
            {
                "id": stmt.id,
                "title": stmt.title,
                "sql_content": stmt.sql_content,
                "description": stmt.description,
                "status": stmt.status.value,
                "db_connection_id": stmt.db_connection_id,
                "version": stmt.version,
                "tags": stmt.tags,
                "category": stmt.category,
                "created_at": stmt.created_at,
                "updated_at": stmt.updated_at,
                "last_reviewed_at": stmt.last_reviewed_at
            }
            for stmt in statements
        ],
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "total": total
    }


@router.get("/{statement_id}")
async def get_sql_statement(
    statement_id: int,
    db: Session = Depends(get_db)
):
    """获取单个SQL语句"""
    statement = db.query(SQLStatement).filter(
        SQLStatement.id == statement_id,
        SQLStatement.is_active == True
    ).first()
    
    if not statement:
        raise HTTPException(status_code=404, detail="SQL语句不存在")
    
    return {
        "id": statement.id,
        "title": statement.title,
        "sql_content": statement.sql_content,
        "description": statement.description,
        "status": statement.status.value,
        "db_connection_id": statement.db_connection_id,
        "version": statement.version,
        "tags": statement.tags,
        "category": statement.category,
        "created_at": statement.created_at,
        "updated_at": statement.updated_at,
        "last_reviewed_at": statement.last_reviewed_at
    }


@router.post("/")
async def create_sql_statement(
    statement_data: SQLStatementCreate,
    db: Session = Depends(get_db)
):
    """创建SQL语句"""
    statement = SQLStatement(
        title=statement_data.title,
        sql_content=statement_data.sql_content,
        description=statement_data.description,
        db_connection_id=statement_data.db_connection_id,
        tags=statement_data.tags,
        category=statement_data.category
    )
    
    db.add(statement)
    db.commit()
    db.refresh(statement)
    
    return {"id": statement.id, "message": "SQL语句创建成功"}


@router.put("/{statement_id}")
async def update_sql_statement(
    statement_id: int,
    statement_data: SQLStatementUpdate,
    db: Session = Depends(get_db)
):
    """更新SQL语句"""
    statement = db.query(SQLStatement).filter(
        SQLStatement.id == statement_id,
        SQLStatement.is_active == True
    ).first()
    
    if not statement:
        raise HTTPException(status_code=404, detail="SQL语句不存在")
    
    # 更新字段
    for field, value in statement_data.dict(exclude_unset=True).items():
        setattr(statement, field, value)
    
    db.commit()
    
    return {"message": "SQL语句更新成功"}


@router.delete("/{statement_id}")
async def delete_sql_statement(
    statement_id: int,
    db: Session = Depends(get_db)
):
    """删除SQL语句"""
    statement = db.query(SQLStatement).filter(
        SQLStatement.id == statement_id
    ).first()
    
    if not statement:
        raise HTTPException(status_code=404, detail="SQL语句不存在")
    
    statement.is_active = False
    db.commit()
    
    return {"message": "SQL语句删除成功"}


@router.get("/{statement_id}/versions")
async def get_sql_versions(
    statement_id: int,
    db: Session = Depends(get_db)
):
    """获取SQL语句版本历史"""
    service = SQLStatementService(db)
    versions = service.get_sql_versions(statement_id)
    
    if not versions:
        raise HTTPException(status_code=404, detail="SQL语句不存在")
    
    return versions


@router.post("/{statement_id}/restore/{version_id}")
async def restore_sql_version(
    statement_id: int,
    version_id: int,
    db: Session = Depends(get_db)
):
    """恢复SQL语句版本"""
    service = SQLStatementService(db)
    result = service.restore_version(statement_id, version_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/import-csv")
async def import_sql_from_csv(
    file: UploadFile = File(...),
    db_connection_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """从CSV文件导入SQL语句"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持CSV文件")
    
    service = SQLStatementService(db)
    result = service.import_from_csv(file, db_connection_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/export-csv")
async def export_sql_to_csv(
    db: Session = Depends(get_db),
    db_connection_id: Optional[int] = None,
    status: Optional[str] = None,
    category: Optional[str] = None
):
    """导出SQL语句为CSV"""
    filters = {}
    if db_connection_id:
        filters["db_connection_id"] = db_connection_id
    if status:
        filters["status"] = status
    if category:
        filters["category"] = category
    
    service = SQLStatementService(db)
    csv_content = service.export_to_csv(filters)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sql_statements.csv"}
    )


@router.get("/statistics")
async def get_sql_statistics(db: Session = Depends(get_db)):
    """获取SQL语句统计信息"""
    service = SQLStatementService(db)
    return service.get_statistics() 