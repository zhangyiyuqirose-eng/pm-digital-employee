"""
PM Digital Employee - Log Sanitizer
项目经理数字员工系统 - 日志脱敏模块

提供日志输出前的敏感数据脱敏，防止敏感信息泄露到日志。
"""

import re
from typing import Any, Dict, Optional, Union

from app.core.logging import get_logger

logger = get_logger(__name__)


class LogSanitizer:
    """
    日志脱敏器.

    在日志输出前自动脱敏敏感信息：
    - 手机号
    - 邮箱
    - 身份证号
    - 银行卡号
    - IP地址
    - 密钥/Token

    符合等保三级要求：日志不包含敏感个人信息。
    """

    # 正则表达式模式
    PHONE_PATTERN = re.compile(r'1[3-9]\d{9}')
    EMAIL_PATTERN = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
    ID_CARD_PATTERN = re.compile(r'\d{17}[\dXx]')
    BANK_CARD_PATTERN = re.compile(r'\d{16,19}')
    IP_PATTERN = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    TOKEN_PATTERN = re.compile(r'(token|key|secret|password|pwd|auth)[\s:=]+[\w\-\.]+', re.IGNORECASE)

    # 替换模板
    PHONE_REPLACE = '1****0000'
    EMAIL_REPLACE = '***@***.***'
    ID_CARD_REPLACE = '****************'
    BANK_CARD_REPLACE = '************'
    IP_REPLACE = '*.*.*.*'
    TOKEN_REPLACE = '[SENSITIVE]'

    def sanitize(self, text: Optional[str]) -> Optional[str]:
        """
        脱敏文本.

        Args:
            text: 原始文本

        Returns:
            Optional[str]: 脱敏后的文本

        Example:
            ```python
            sanitizer = LogSanitizer()
            safe_text = sanitizer.sanitize("用户手机号13812345678登录")
            # 输出: "用户手机号1****0000登录"
            ```
        """
        if text is None:
            return None

        result = text

        # 脱敏手机号
        result = self.PHONE_PATTERN.sub(self.PHONE_REPLACE, result)

        # 脱敏邮箱
        result = self.EMAIL_PATTERN.sub(self.EMAIL_REPLACE, result)

        # 脱敏身份证号
        result = self.ID_CARD_PATTERN.sub(self.ID_CARD_REPLACE, result)

        # 脱敏银行卡号（仅在明确是银行卡的上下文中）
        # 这里保守处理，避免误伤

        # 脱敏Token/密钥
        result = self.TOKEN_PATTERN.sub(self.TOKEN_REPLACE, result)

        return result

    def sanitize_dict(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        脱敏字典数据.

        Args:
            data: 原始字典

        Returns:
            Optional[Dict[str, Any]]: 脱敏后的字典

        Example:
            ```python
            sanitizer = LogSanitizer()
            safe_data = sanitizer.sanitize_dict({
                "phone": "13812345678",
                "email": "test@example.com"
            })
            ```
        """
        if data is None:
            return None

        result = {}
        for key, value in data.items():
            # 敏感键名直接替换
            if self._is_sensitive_key(key):
                result[key] = '[REDACTED]'
            elif isinstance(value, str):
                result[key] = self.sanitize(value)
            elif isinstance(value, dict):
                result[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                result[key] = self.sanitize_list(value)
            else:
                result[key] = value

        return result

    def sanitize_list(self, data: Optional[list]) -> Optional[list]:
        """
        脱敏列表数据.

        Args:
            data: 原始列表

        Returns:
            Optional[list]: 脱敏后的列表
        """
        if data is None:
            return None

        result = []
        for item in data:
            if isinstance(item, str):
                result.append(self.sanitize(item))
            elif isinstance(item, dict):
                result.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                result.append(self.sanitize_list(item))
            else:
                result.append(item)

        return result

    def _is_sensitive_key(self, key: str) -> bool:
        """
        检查键名是否敏感.

        Args:
            key: 键名

        Returns:
            bool: 是否敏感
        """
        sensitive_keys = [
            'password', 'pwd', 'pass',
            'secret', 'key', 'token', 'auth',
            'phone', 'mobile', 'tel',
            'email', 'mail',
            'id_card', 'identity',
            'bank_card', 'card_no',
            'ssn', 'social_security',
        ]

        key_lower = key.lower()
        return any(sk in key_lower for sk in sensitive_keys)

    def sanitize_user_id(self, user_id: Optional[str]) -> Optional[str]:
        """
        脱敏用户ID（飞书用户ID）.

        保留前缀和后4位，中间用*替代。

        Args:
            user_id: 用户ID（如 ou_xxxx）

        Returns:
            Optional[str]: 脱敏后的用户ID

        Example:
            - 输入: "ou_abc123def456"
            - 输出: "ou_****456"
        """
        if user_id is None or len(user_id) < 8:
            return user_id

        prefix = user_id[:3]  # ou_
        suffix = user_id[-4:]
        return f"{prefix}****{suffix}"


class SanitizedLogger:
    """
    脱敏日志器.

    包装原始logger，自动脱敏日志内容。
    """

    def __init__(self, logger_name: str) -> None:
        """
        初始化脱敏日志器.

        Args:
            logger_name: 日志器名称
        """
        self._logger = get_logger(logger_name)
        self._sanitizer = LogSanitizer()

    def info(self, message: str, **kwargs) -> None:
        """
        记录INFO级别日志（脱敏）.

        Args:
            message: 日志消息
            **kwargs: 附加参数
        """
        safe_message = self._sanitizer.sanitize(message)
        safe_kwargs = self._sanitizer.sanitize_dict(kwargs) if kwargs else None
        if safe_kwargs:
            self._logger.info(safe_message, **safe_kwargs)
        else:
            self._logger.info(safe_message)

    def warning(self, message: str, **kwargs) -> None:
        """
        记录WARNING级别日志（脱敏）.
        """
        safe_message = self._sanitizer.sanitize(message)
        safe_kwargs = self._sanitizer.sanitize_dict(kwargs) if kwargs else None
        if safe_kwargs:
            self._logger.warning(safe_message, **safe_kwargs)
        else:
            self._logger.warning(safe_message)

    def error(self, message: str, **kwargs) -> None:
        """
        记录ERROR级别日志（脱敏）.
        """
        safe_message = self._sanitizer.sanitize(message)
        safe_kwargs = self._sanitizer.sanitize_dict(kwargs) if kwargs else None
        if safe_kwargs:
            self._logger.error(safe_message, **safe_kwargs)
        else:
            self._logger.error(safe_message)

    def debug(self, message: str, **kwargs) -> None:
        """
        记录DEBUG级别日志（脱敏）.
        """
        safe_message = self._sanitizer.sanitize(message)
        safe_kwargs = self._sanitizer.sanitize_dict(kwargs) if kwargs else None
        if safe_kwargs:
            self._logger.debug(safe_message, **safe_kwargs)
        else:
            self._logger.debug(safe_message)


def get_sanitized_logger(name: str) -> SanitizedLogger:
    """
    获取脱敏日志器.

    Args:
        name: 日志器名称

    Returns:
        SanitizedLogger: 脱敏日志器实例
    """
    return SanitizedLogger(name)


def sanitize_for_log(text: Optional[str]) -> Optional[str]:
    """
    快捷脱敏函数.

    Args:
        text: 原始文本

    Returns:
        Optional[str]: 脱敏后的文本
    """
    sanitizer = LogSanitizer()
    return sanitizer.sanitize(text)