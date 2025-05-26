"""LLM配置服务"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import openai
import requests

from app.models.llm_config import LLMConfig, LLMProvider
from app.core.encryption import EncryptionService


class LLMConfigService:
    """LLM配置服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.encryption_service = EncryptionService()
    
    def create_llm_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建LLM配置
        
        Args:
            config_data: LLM配置数据
            
        Returns:
            创建结果
        """
        try:
            # 加密API密钥
            encrypted_api_key = self.encryption_service.encrypt_api_key(
                config_data.get("api_key", "")
            )
            
            config = LLMConfig(
                name=config_data.get("name"),
                provider=LLMProvider(config_data.get("provider")),
                model_name=config_data.get("model_name"),
                api_key=encrypted_api_key,
                base_url=config_data.get("base_url"),
                temperature=config_data.get("temperature", 0.1),
                max_tokens=config_data.get("max_tokens", 4000),
                top_p=config_data.get("top_p", 1.0),
                frequency_penalty=config_data.get("frequency_penalty", 0.0),
                presence_penalty=config_data.get("presence_penalty", 0.0),
                timeout=config_data.get("timeout", 60),
                max_retries=config_data.get("max_retries", 3),
                description=config_data.get("description")
            )
            
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            
            return {
                "success": True,
                "id": config.id,
                "message": "LLM配置创建成功"
            }
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"创建LLM配置失败: {str(e)}"}
    
    def update_llm_config(self, config_id: int, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新LLM配置
        
        Args:
            config_id: LLM配置ID
            config_data: 更新数据
            
        Returns:
            更新结果
        """
        try:
            config = self.db.query(LLMConfig).filter(
                LLMConfig.id == config_id,
                LLMConfig.is_active == True
            ).first()
            
            if not config:
                return {"success": False, "error": "LLM配置不存在"}
            
            # 更新字段
            for field, value in config_data.items():
                if field == "api_key" and value:
                    # 重新加密API密钥
                    encrypted_api_key = self.encryption_service.encrypt_api_key(value)
                    setattr(config, field, encrypted_api_key)
                elif field == "provider" and value:
                    setattr(config, field, LLMProvider(value))
                elif hasattr(config, field):
                    setattr(config, field, value)
            
            self.db.commit()
            
            return {"success": True, "message": "LLM配置更新成功"}
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"更新LLM配置失败: {str(e)}"}
    
    def get_llm_config(self, config_id: int) -> Optional[LLMConfig]:
        """获取LLM配置"""
        return self.db.query(LLMConfig).filter(
            LLMConfig.id == config_id,
            LLMConfig.is_active == True
        ).first()
    
    def get_llm_configs(self) -> List[LLMConfig]:
        """获取所有LLM配置"""
        return self.db.query(LLMConfig).filter(
            LLMConfig.is_active == True
        ).order_by(LLMConfig.is_default.desc(), LLMConfig.created_at.desc()).all()
    
    def get_default_llm_config(self) -> Optional[LLMConfig]:
        """获取默认LLM配置"""
        return self.db.query(LLMConfig).filter(
            LLMConfig.is_default == True,
            LLMConfig.is_active == True
        ).first()
    
    def set_default_llm_config(self, config_id: int) -> Dict[str, Any]:
        """
        设置默认LLM配置
        
        Args:
            config_id: LLM配置ID
            
        Returns:
            设置结果
        """
        try:
            # 取消所有默认配置
            self.db.query(LLMConfig).update({"is_default": False})
            
            # 设置新的默认配置
            config = self.db.query(LLMConfig).filter(
                LLMConfig.id == config_id,
                LLMConfig.is_active == True
            ).first()
            
            if not config:
                return {"success": False, "error": "LLM配置不存在"}
            
            config.is_default = True
            self.db.commit()
            
            return {"success": True, "message": "默认LLM配置设置成功"}
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"设置默认LLM配置失败: {str(e)}"}
    
    def delete_llm_config(self, config_id: int) -> Dict[str, Any]:
        """
        删除LLM配置（软删除）
        
        Args:
            config_id: LLM配置ID
            
        Returns:
            删除结果
        """
        try:
            config = self.db.query(LLMConfig).filter(
                LLMConfig.id == config_id
            ).first()
            
            if not config:
                return {"success": False, "error": "LLM配置不存在"}
            
            # 如果是默认配置，不允许删除
            if config.is_default:
                return {"success": False, "error": "不能删除默认LLM配置"}
            
            config.is_active = False
            self.db.commit()
            
            return {"success": True, "message": "LLM配置删除成功"}
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": f"删除LLM配置失败: {str(e)}"}
    
    def test_llm_config(self, config_id: int) -> Dict[str, Any]:
        """
        测试LLM配置
        
        Args:
            config_id: LLM配置ID
            
        Returns:
            测试结果
        """
        try:
            config = self.get_llm_config(config_id)
            if not config:
                return {"success": False, "error": "LLM配置不存在"}
            
            # 解密API密钥
            api_key = self.encryption_service.decrypt_api_key(config.api_key)
            
            # 根据提供商进行测试
            if config.provider == LLMProvider.OPENAI:
                return self._test_openai_config(config, api_key)
            elif config.provider == LLMProvider.DEEPSEEK:
                return self._test_deepseek_config(config, api_key)
            elif config.provider == LLMProvider.OLLAMA:
                return self._test_ollama_config(config)
            else:
                return {"success": False, "error": f"不支持的LLM提供商: {config.provider.value}"}
        
        except Exception as e:
            return {"success": False, "error": f"测试LLM配置失败: {str(e)}"}
    
    def _test_openai_config(self, config: LLMConfig, api_key: str) -> Dict[str, Any]:
        """测试OpenAI配置"""
        try:
            # 设置OpenAI配置
            openai.api_key = api_key
            openai.api_base = config.base_url or "https://api.openai.com/v1"
            
            # 发送测试请求
            response = openai.ChatCompletion.create(
                model=config.model_name,
                messages=[
                    {"role": "user", "content": "Hello, this is a test message."}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            # 更新最后测试时间
            from sqlalchemy.sql import func
            config.last_tested_at = func.now()
            self.db.commit()
            
            return {
                "success": True,
                "message": "OpenAI配置测试成功",
                "response": response.choices[0].message.content
            }
        
        except Exception as e:
            return {"success": False, "error": f"OpenAI配置测试失败: {str(e)}"}
    
    def _test_deepseek_config(self, config: LLMConfig, api_key: str) -> Dict[str, Any]:
        """测试DeepSeek配置"""
        try:
            # DeepSeek使用OpenAI兼容的API
            openai.api_key = api_key
            openai.api_base = config.base_url or "https://api.deepseek.com/v1"
            
            # 发送测试请求
            response = openai.ChatCompletion.create(
                model=config.model_name,
                messages=[
                    {"role": "user", "content": "Hello, this is a test message."}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            # 更新最后测试时间
            from sqlalchemy.sql import func
            config.last_tested_at = func.now()
            self.db.commit()
            
            return {
                "success": True,
                "message": "DeepSeek配置测试成功",
                "response": response.choices[0].message.content
            }
        
        except Exception as e:
            return {"success": False, "error": f"DeepSeek配置测试失败: {str(e)}"}
    
    def _test_ollama_config(self, config: LLMConfig) -> Dict[str, Any]:
        """测试Ollama配置"""
        try:
            url = f"{config.base_url}/api/generate"
            
            data = {
                "model": config.model_name,
                "prompt": "Hello, this is a test message.",
                "stream": False,
                "options": {
                    "num_predict": 10
                }
            }
            
            response = requests.post(
                url,
                json=data,
                timeout=config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 更新最后测试时间
            from sqlalchemy.sql import func
            config.last_tested_at = func.now()
            self.db.commit()
            
            return {
                "success": True,
                "message": "Ollama配置测试成功",
                "response": result.get("response", "")
            }
        
        except Exception as e:
            return {"success": False, "error": f"Ollama配置测试失败: {str(e)}"}
    
    def get_llm_config_dict(self, config_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        获取LLM配置字典（用于AI审查器）
        
        Args:
            config_id: LLM配置ID，如果为None则使用默认配置
            
        Returns:
            LLM配置字典
        """
        if config_id:
            config = self.get_llm_config(config_id)
        else:
            config = self.get_default_llm_config()
        
        if not config:
            return None
        
        return {
            "provider": config.provider.value,
            "model_name": config.model_name,
            "api_key": config.api_key,  # 已加密
            "base_url": config.base_url,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
            "timeout": config.timeout
        } 