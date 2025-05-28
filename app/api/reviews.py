"""审查相关API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_
from typing import Optional, List

from app.models.database import get_db
from app.models.review_report import ReviewReport
from app.models.sql_statement import SQLStatement
from app.models.db_connection import DatabaseConnection
from app.services.review_service import ReviewService

router = APIRouter()


@router.post("/sql/{sql_id}/review")
async def review_sql(
    sql_id: int,
    llm_config_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """审查SQL语句"""
    review_service = ReviewService(db)
    
    result = review_service.review_sql_statement(sql_id, llm_config_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/reports/{report_id}")
async def get_review_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """获取审查报告详情"""
    review_service = ReviewService(db)
    
    report = review_service.get_review_report(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="审查报告不存在")
    
    return {
        "id": report.id,
        "sql_statement_id": report.sql_statement_id,
        "overall_assessment": {
            "status": report.overall_status.value if report.overall_status else None,
            "score": report.overall_score,
            "summary": report.overall_summary
        },
        "consistency": {
            "status": report.consistency_status.value if report.consistency_status else None,
            "score": report.consistency_score,
            "details": report.consistency_details,
            "suggestions": report.consistency_suggestions
        },
        "conventions": {
            "status": report.conventions_status.value if report.conventions_status else None,
            "score": report.conventions_score,
            "details": report.conventions_details,
            "suggestions": report.conventions_suggestions
        },
        "performance": {
            "status": report.performance_status.value if report.performance_status else None,
            "score": report.performance_score,
            "details": report.performance_details,
            "suggestions": report.performance_suggestions
        },
        "security": {
            "status": report.security_status.value if report.security_status else None,
            "score": report.security_score,
            "details": report.security_details,
            "suggestions": report.security_suggestions
        },
        "readability": {
            "status": report.readability_status.value if report.readability_status else None,
            "score": report.readability_score,
            "details": report.readability_details,
            "suggestions": report.readability_suggestions
        },
        "maintainability": {
            "status": report.maintainability_status.value if report.maintainability_status else None,
            "score": report.maintainability_score,
            "details": report.maintainability_details,
            "suggestions": report.maintainability_suggestions
        },
        "llm_info": {
            "provider": report.llm_provider,
            "model": report.llm_model
        },
        "optimized_sql": report.optimized_sql,
        "created_at": report.created_at
    }


@router.get("/sql/{sql_id}/history")
async def get_sql_review_history(
    sql_id: int,
    db: Session = Depends(get_db)
):
    """获取SQL语句的审查历史"""
    review_service = ReviewService(db)
    
    reports = review_service.get_sql_review_history(sql_id)
    
    return [
        {
            "id": report.id,
            "overall_status": report.overall_status.value if report.overall_status else None,
            "overall_score": report.overall_score,
            "llm_provider": report.llm_provider,
            "llm_model": report.llm_model,
            "created_at": report.created_at
        }
        for report in reports
    ]


@router.get("/results")
async def get_review_results(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    database_name: Optional[str] = Query(None, description="数据库名称"),
    sql_title: Optional[str] = Query(None, description="SQL标题模糊查询"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="最低评分"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="最高评分"),
    order_by: str = Query("created_at", description="排序字段"),
    order_dir: str = Query("desc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """获取SQL审查结果列表（支持分页和筛选）"""
    
    # 构建查询，联接相关表
    query = db.query(ReviewReport).join(
        SQLStatement, ReviewReport.sql_statement_id == SQLStatement.id
    ).join(
        DatabaseConnection, SQLStatement.db_connection_id == DatabaseConnection.id
    ).filter(
        SQLStatement.is_active == True
    )
    
    # 应用筛选条件
    if database_name:
        query = query.filter(DatabaseConnection.name.ilike(f"%{database_name}%"))
    
    if sql_title:
        query = query.filter(SQLStatement.title.ilike(f"%{sql_title}%"))
    
    if min_score is not None:
        query = query.filter(ReviewReport.overall_score >= min_score)
    
    if max_score is not None:
        query = query.filter(ReviewReport.overall_score <= max_score)
    
    # 排序
    if hasattr(ReviewReport, order_by):
        order_column = getattr(ReviewReport, order_by)
    elif hasattr(SQLStatement, order_by):
        order_column = getattr(SQLStatement, order_by)
    else:
        order_column = ReviewReport.created_at
    
    if order_dir.lower() == "desc":
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(asc(order_column))
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    reports = query.offset(offset).limit(page_size).all()
    
    # 计算总页数
    pages = (total + page_size - 1) // page_size
    
    # 构建返回数据
    items = []
    for report in reports:
        sql_statement = report.sql_statement
        db_connection = sql_statement.db_connection
        
        items.append({
            "id": report.id,
            "sql_statement_id": sql_statement.id,
            "database_name": db_connection.name if db_connection else "未知",
            "sql_title": sql_statement.title,
            "sql_description": sql_statement.description,
            "sql_content": sql_statement.sql_content,
            "overall_score": report.overall_score,
            "overall_status": report.overall_status.value if report.overall_status else None,
            "overall_summary": report.overall_summary,
            "consistency_score": report.consistency_score,
            "consistency_status": report.consistency_status.value if report.consistency_status else None,
            "consistency_details": report.consistency_details,
            "consistency_suggestions": report.consistency_suggestions,
            "conventions_score": report.conventions_score,
            "conventions_status": report.conventions_status.value if report.conventions_status else None,
            "conventions_details": report.conventions_details,
            "conventions_suggestions": report.conventions_suggestions,
            "performance_score": report.performance_score,
            "performance_status": report.performance_status.value if report.performance_status else None,
            "performance_details": report.performance_details,
            "performance_suggestions": report.performance_suggestions,
            "security_score": report.security_score,
            "security_status": report.security_status.value if report.security_status else None,
            "security_details": report.security_details,
            "security_suggestions": report.security_suggestions,
            "readability_score": report.readability_score,
            "readability_status": report.readability_status.value if report.readability_status else None,
            "readability_details": report.readability_details,
            "readability_suggestions": report.readability_suggestions,
            "maintainability_score": report.maintainability_score,
            "maintainability_status": report.maintainability_status.value if report.maintainability_status else None,
            "maintainability_details": report.maintainability_details,
            "maintainability_suggestions": report.maintainability_suggestions,
            "optimized_sql": report.optimized_sql,
            "llm_provider": report.llm_provider,
            "llm_model": report.llm_model,
            "created_at": report.created_at.isoformat() if report.created_at else None
        })
    
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "total": total
    }


@router.get("/databases")
async def get_databases_for_filter(db: Session = Depends(get_db)):
    """获取数据库列表用于筛选下拉框"""
    databases = db.query(DatabaseConnection).filter(
        DatabaseConnection.is_active == True
    ).all()
    
    return [
        {
            "id": db_conn.id,
            "name": db_conn.name,
            "db_type": db_conn.db_type.value if db_conn.db_type else None
        }
        for db_conn in databases
    ] 