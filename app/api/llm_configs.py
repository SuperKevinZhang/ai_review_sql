"""LLM配置相关API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.models.database import get_db
from app.models.llm_config import LLMConfig, LLMProvider
from app.services.llm_config_service import LLMConfigService

router = APIRouter()


class LLMConfigCreate(BaseModel):
    name: str
    provider: str
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 4000
    description: Optional[str] = None


@router.get("/")
async def get_llm_configs(db: Session = Depends(get_db)):
    """获取所有LLM配置"""
    configs = db.query(LLMConfig).filter(
        LLMConfig.is_active == True
    ).all()
    
    return [
        {
            "id": config.id,
            "name": config.name,
            "provider": config.provider.value,
            "model_name": config.model_name,
            "base_url": config.base_url,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "is_default": config.is_default,
            "description": config.description,
            "created_at": config.created_at
        }
        for config in configs
    ]


@router.get("/{config_id}")
async def get_llm_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """获取单个LLM配置"""
    config = db.query(LLMConfig).filter(
        LLMConfig.id == config_id,
        LLMConfig.is_active == True
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="LLM配置不存在")
    
    return {
        "id": config.id,
        "name": config.name,
        "provider": config.provider.value,
        "model_name": config.model_name,
        "base_url": config.base_url,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "is_default": config.is_default,
        "description": config.description,
        "created_at": config.created_at
    }


@router.post("/")
async def create_llm_config(
    config_data: LLMConfigCreate,
    db: Session = Depends(get_db)
):
    """创建LLM配置"""
    service = LLMConfigService(db)
    
    config_dict = {
        "name": config_data.name,
        "provider": config_data.provider,
        "model_name": config_data.model_name,
        "api_key": config_data.api_key,
        "base_url": config_data.base_url,
        "temperature": config_data.temperature,
        "max_tokens": config_data.max_tokens,
        "description": config_data.description
    }
    
    result = service.create_llm_config(config_dict)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.put("/{config_id}")
async def update_llm_config(
    config_id: int,
    config_data: LLMConfigCreate,
    db: Session = Depends(get_db)
):
    """更新LLM配置"""
    service = LLMConfigService(db)
    
    config_dict = {
        "name": config_data.name,
        "provider": config_data.provider,
        "model_name": config_data.model_name,
        "api_key": config_data.api_key,
        "base_url": config_data.base_url,
        "temperature": config_data.temperature,
        "max_tokens": config_data.max_tokens,
        "description": config_data.description
    }
    
    result = service.update_llm_config(config_id, config_dict)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.put("/{config_id}/set-default")
async def set_default_llm_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """设置默认LLM配置"""
    service = LLMConfigService(db)
    result = service.set_default_llm_config(config_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.delete("/{config_id}")
async def delete_llm_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """删除LLM配置"""
    service = LLMConfigService(db)
    result = service.delete_llm_config(config_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/{config_id}/test")
async def test_llm_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """测试LLM配置"""
    service = LLMConfigService(db)
    result = service.test_llm_config(config_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result 