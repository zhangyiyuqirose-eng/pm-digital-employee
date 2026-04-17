"""
PM Digital Employee - Data Encryption
项目经理数字员工系统 - 数据加密模块

提供敏感数据的加密和解密功能，符合等保三级要求。
"""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataEncryptor:
    """
    数据加密器.

    使用Fernet（AES-128）对称加密，提供：
    - 敏感字段加密存储
    - 加密数据解密读取
    - 密钥管理

    符合等保三级要求：个人敏感信息加密存储。
    """

    def __init__(self, encryption_key: Optional[str] = None) -> None:
        """
        初始化加密器.

        Args:
            encryption_key: 加密密钥（Base64编码的32字节密钥）
                            如果不提供，从settings读取或生成临时密钥

        Raises:
            ValueError: 密钥格式无效
        """
        if encryption_key:
            try:
                self._fernet = Fernet(encryption_key.encode())
            except Exception as e:
                logger.error("Invalid encryption key", error=str(e))
                raise ValueError(f"加密密钥格式无效: {str(e)}")
        else:
            # 从settings获取密钥
            key = getattr(settings, 'encryption_key', None)
            if key:
                try:
                    self._fernet = Fernet(key.encode())
                except Exception as e:
                    logger.warning("Settings encryption key invalid, generating temporary key", error=str(e))
                    self._fernet = Fernet(Fernet.generate_key())
            else:
                # 生成临时密钥（生产环境必须配置）
                logger.warning("No encryption key configured, using temporary key (NOT suitable for production)")
                self._fernet = Fernet(Fernet.generate_key())

    def encrypt(self, plaintext: Optional[str]) -> Optional[str]:
        """
        加密数据.

        Args:
            plaintext: 明文数据

        Returns:
            Optional[str]: Base64编码的加密数据，或None（输入为空）

        Example:
            ```python
            encryptor = DataEncryptor()
            encrypted_phone = encryptor.encrypt("13812345678")
            ```
        """
        if plaintext is None or plaintext == "":
            return None

        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error("Encryption failed", error=str(e))
            raise RuntimeError(f"加密失败: {str(e)}")

    def decrypt(self, ciphertext: Optional[str]) -> Optional[str]:
        """
        解密数据.

        Args:
            ciphertext: Base64编码的加密数据

        Returns:
            Optional[str]: 明文数据，或None（输入为空）

        Example:
            ```python
            encryptor = DataEncryptor()
            decrypted_phone = encryptor.decrypt(encrypted_phone)
            ```
        """
        if ciphertext is None or ciphertext == "":
            return None

        try:
            encrypted_bytes = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error("Decryption failed", error=str(e))
            raise RuntimeError(f"解密失败: {str(e)}")

    def encrypt_phone(self, phone: Optional[str]) -> Optional[str]:
        """
        加密手机号.

        Args:
            phone: 手机号明文

        Returns:
            Optional[str]: 加密后的手机号
        """
        return self.encrypt(phone)

    def decrypt_phone(self, encrypted_phone: Optional[str]) -> Optional[str]:
        """
        解密手机号.

        Args:
            encrypted_phone: 加密的手机号

        Returns:
            Optional[str]: 手机号明文
        """
        return self.decrypt(encrypted_phone)

    def encrypt_email(self, email: Optional[str]) -> Optional[str]:
        """
        加密邮箱.

        Args:
            email: 邮箱明文

        Returns:
            Optional[str]: 加密后的邮箱
        """
        return self.encrypt(email)

    def decrypt_email(self, encrypted_email: Optional[str]) -> Optional[str]:
        """
        解密邮箱.

        Args:
            encrypted_email: 加密的邮箱

        Returns:
            Optional[str]: 邮箱明文
        """
        return self.decrypt(encrypted_email)


class MaskUtils:
    """
    数据脱敏工具.

    提供敏感数据的脱敏显示，用于日志和UI展示。
    """

    @staticmethod
    def mask_phone(phone: Optional[str]) -> Optional[str]:
        """
        手机号脱敏.

        保留前3位和后4位，中间用*替代。

        Args:
            phone: 手机号

        Returns:
            Optional[str]: 脱敏后的手机号

        Example:
            - 输入: "13812345678"
            - 输出: "138****5678"
        """
        if phone is None or len(phone) < 7:
            return phone

        return f"{phone[:3]}****{phone[-4:]}"

    @staticmethod
    def mask_email(email: Optional[str]) -> Optional[str]:
        """
        邮箱脱敏.

        保留前2位和@后的域名，中间用***替代。

        Args:
            email: 邮箱

        Returns:
            Optional[str]: 脱敏后的邮箱

        Example:
            - 输入: "test@example.com"
            - 输出: "te***@example.com"
        """
        if email is None or '@' not in email:
            return email

        parts = email.split('@')
        if len(parts[0]) < 2:
            return f"*@{parts[1]}"

        return f"{parts[0][:2]}***@{parts[1]}"

    @staticmethod
    def mask_id_card(id_card: Optional[str]) -> Optional[str]:
        """
        身份证号脱敏.

        保留前6位和后4位，中间用*替代。

        Args:
            id_card: 身份证号

        Returns:
            Optional[str]: 脱敏后的身份证号

        Example:
            - 输入: "123456789012345678"
            - 输出: "123456********5678"
        """
        if id_card is None or len(id_card) < 10:
            return id_card

        return f"{id_card[:6]}********{id_card[-4:]}"

    @staticmethod
    def mask_bank_card(card_number: Optional[str]) -> Optional[str]:
        """
        银行卡号脱敏.

        保留前4位和后4位，中间用*替代。

        Args:
            card_number: 银行卡号

        Returns:
            Optional[str]: 脱敏后的银行卡号

        Example:
            - 输入: "1234567890123456"
            - 输出: "1234********3456"
        """
        if card_number is None or len(card_number) < 8:
            return card_number

        return f"{card_number[:4]}****{card_number[-4:]}"

    @staticmethod
    def mask_name(name: Optional[str]) -> Optional[str]:
        """
        姓名脱敏.

        保留首字符，其余用*替代。

        Args:
            name: 姓名

        Returns:
            Optional[str]: 脱敏后的姓名

        Example:
            - 输入: "张三"
            - 输出: "张*"
        """
        if name is None or len(name) < 2:
            return name

        return f"{name[0]}{'*' * (len(name) - 1)}"


# 全局加密器实例
_encryptor: Optional[DataEncryptor] = None


def get_encryptor() -> DataEncryptor:
    """
    获取加密器实例.

    Returns:
        DataEncryptor: 加密器实例
    """
    global _encryptor
    if _encryptor is None:
        _encryptor = DataEncryptor()
    return _encryptor


def generate_encryption_key() -> str:
    """
    生成新的加密密钥.

    用于初始化加密配置。

    Returns:
        str: Base64编码的32字节密钥

    Example:
        ```python
        key = generate_encryption_key()
        # 将key配置到settings.encryption_key
        ```
    """
    return Fernet.generate_key().decode('utf-8')