"""审查相关API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database import get_db
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