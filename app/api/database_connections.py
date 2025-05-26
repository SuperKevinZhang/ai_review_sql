"""数据库连接相关API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.models.database import get_db
from app.models.db_connection import DatabaseConnection, DatabaseType
from app.services.db_connection_service import DatabaseConnectionService

router = APIRouter()


class DatabaseConnectionCreate(BaseModel):
    name: str
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    description: Optional[str] = None


@router.get("/")
async def get_database_connections(db: Session = Depends(get_db)):
    """获取所有数据库连接"""
    connections = db.query(DatabaseConnection).filter(
        DatabaseConnection.is_active == True
    ).all()
    
    return [
        {
            "id": conn.id,
            "name": conn.name,
            "db_type": conn.db_type.value,
            "host": conn.host,
            "port": conn.port,
            "database_name": conn.database_name,
            "username": conn.username,
            "description": conn.description,
            "created_at": conn.created_at
        }
        for conn in connections
    ]


@router.post("/")
async def create_database_connection(
    connection_data: DatabaseConnectionCreate,
    db: Session = Depends(get_db)
):
    """创建数据库连接"""
    service = DatabaseConnectionService(db)
    
    connection_dict = {
        "name": connection_data.name,
        "db_type": connection_data.db_type,
        "host": connection_data.host,
        "port": connection_data.port,
        "database_name": connection_data.database_name,
        "username": connection_data.username,
        "password": connection_data.password,
        "description": connection_data.description
    }
    
    # 创建连接
    from app.core.encryption import EncryptionService
    encryption_service = EncryptionService()
    
    # 加密密码
    encrypted_password = encryption_service.encrypt_password(connection_data.password or "")
    
    connection = DatabaseConnection(
        name=connection_data.name,
        db_type=DatabaseType(connection_data.db_type),
        host=connection_data.host,
        port=connection_data.port,
        database_name=connection_data.database_name,
        username=connection_data.username,
        password=encrypted_password,
        description=connection_data.description
    )
    
    db.add(connection)
    db.commit()
    db.refresh(connection)
    
    return {"id": connection.id, "message": "数据库连接创建成功"}


@router.delete("/{connection_id}")
async def delete_database_connection(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """删除数据库连接"""
    connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == connection_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="数据库连接不存在")
    
    connection.is_active = False
    db.commit()
    
    return {"message": "数据库连接删除成功"}


@router.get("/{connection_id}")
async def get_database_connection(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """获取单个数据库连接"""
    connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == connection_id,
        DatabaseConnection.is_active == True
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="数据库连接不存在")
    
    return {
        "id": connection.id,
        "name": connection.name,
        "db_type": connection.db_type.value,
        "host": connection.host,
        "port": connection.port,
        "database_name": connection.database_name,
        "username": connection.username,
        "description": connection.description,
        "created_at": connection.created_at
    }


@router.put("/{connection_id}")
async def update_database_connection(
    connection_id: int,
    connection_data: DatabaseConnectionCreate,
    db: Session = Depends(get_db)
):
    """更新数据库连接"""
    connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == connection_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="数据库连接不存在")
    
    # 更新连接信息
    connection.name = connection_data.name
    connection.db_type = DatabaseType(connection_data.db_type)
    connection.host = connection_data.host
    connection.port = connection_data.port
    connection.database_name = connection_data.database_name
    connection.username = connection_data.username
    connection.description = connection_data.description
    
    # 如果提供了新密码，则加密并更新
    if connection_data.password:
        from app.core.encryption import EncryptionService
        encryption_service = EncryptionService()
        connection.password = encryption_service.encrypt_password(connection_data.password)
    
    db.commit()
    
    return {"message": "数据库连接更新成功"}


@router.post("/test")
async def test_connection_config(
    connection_data: DatabaseConnectionCreate,
    db: Session = Depends(get_db)
):
    """测试数据库连接配置（不保存）"""
    service = DatabaseConnectionService(db)
    
    # 创建临时连接对象用于测试
    temp_connection = DatabaseConnection(
        name=connection_data.name,
        db_type=DatabaseType(connection_data.db_type),
        host=connection_data.host,
        port=connection_data.port,
        database_name=connection_data.database_name,
        username=connection_data.username,
        password=connection_data.password or ""  # 不加密，直接测试
    )
    
    result = service.test_connection_object(temp_connection)
    return result


@router.post("/{connection_id}/test")
async def test_database_connection(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """测试数据库连接"""
    service = DatabaseConnectionService(db)
    result = service.test_connection(connection_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/{connection_id}/schema")
async def get_database_schema(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """获取数据库模式"""
    service = DatabaseConnectionService(db)
    result = service.get_database_schema(connection_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/{connection_id}/schema/{object_type}/{table_name}")
async def get_table_details(
    connection_id: int,
    object_type: str,
    table_name: str,
    db: Session = Depends(get_db)
):
    """获取表或视图详细信息"""
    service = DatabaseConnectionService(db)
    result = service.get_table_details(connection_id, table_name, object_type)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result 