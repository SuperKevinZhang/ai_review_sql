"""加密服务"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional

from app.config import get_settings


class EncryptionService:
    """加密服务，用于加密存储敏感信息"""
    
    def __init__(self):
        self.settings = get_settings()
        self._fernet = None
    
    def _get_fernet(self) -> Fernet:
        """获取Fernet加密实例"""
        if self._fernet is None:
            # 使用配置中的密钥生成加密密钥
            password = self.settings.secret_key.encode()
            salt = b'salt_for_sql_review_tool'  # 在生产环境中应该使用随机盐
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            self._fernet = Fernet(key)
        
        return self._fernet
    
    def encrypt(self, data: str) -> str:
        """
        加密字符串
        
        Args:
            data: 要加密的字符串
            
        Returns:
            加密后的字符串（Base64编码）
        """
        if not data:
            return ""
        
        try:
            fernet = self._get_fernet()
            encrypted_data = fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            print(f"加密失败: {e}")
            return ""
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        解密字符串
        
        Args:
            encrypted_data: 加密的字符串（Base64编码）
            
        Returns:
            解密后的字符串
        """
        if not encrypted_data:
            return ""
        
        try:
            fernet = self._get_fernet()
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            print(f"解密失败: {e}")
            return ""
    
    def encrypt_password(self, password: str) -> str:
        """加密密码"""
        return self.encrypt(password)
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """解密密码"""
        return self.decrypt(encrypted_password)
    
    def encrypt_api_key(self, api_key: str) -> str:
        """加密API密钥"""
        return self.encrypt(api_key)
    
    def decrypt_api_key(self, encrypted_api_key: str) -> str:
        """解密API密钥"""
        return self.decrypt(encrypted_api_key) 