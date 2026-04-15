"""
PM Digital Employee - Security Module
项目经理数字员工系统 - 金融级安全治理模块
"""

import re
import html
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SecurityConfig:
    """安全配置"""
    # 参数校验配置
    max_input_length: int = 10000
    allowed_chars_pattern: str = r'^[\w\s\u4e00-\u9fff.,!?;:\-"\'\(\)\[\]\{\}/\\@#$%^&*+=<>|~`\r\n]+$'
    forbidden_patterns: List[str] = None

    # 敏感数据配置
    sensitive_keywords: List[str] = None
    mask_char: str = '*'
    mask_length: int = 4

    def __post_init__(self):
        if self.forbidden_patterns is None:
            self.forbidden_patterns = [
                r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',  # XSS
                r'(?:union|select|insert|delete|drop|create|alter)\b',  # SQL注入
                r'(["\']\s*(?:or|and)\s*["\']\s*[=<>])',  # SQL注入
                r'\b(?:exec|execute|sp_|xp_|sysobjects|information_schema)\b',  # SQL注入
                r'(?:--|\#|/\*|\*/)',  # SQL注释
            ]
        if self.sensitive_keywords is None:
            self.sensitive_keywords = [
                'password', 'secret', 'token', 'key', 'credential',
                'phone', 'mobile', 'email', 'id_card', 'bank_card',
                'account', 'balance', 'credit_card', 'cvv', 'pin'
            ]


class SecurityValidator:
    """安全校验器"""

    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()

    def validate_input(self, input_value: str) -> bool:
        """验证输入参数"""
        if not input_value:
            return False

        # 长度检查
        if len(input_value) > self.config.max_input_length:
            return False

        # 字符检查
        if not re.match(self.config.allowed_chars_pattern, input_value):
            return False

        # 恶意模式检查
        for pattern in self.config.forbidden_patterns:
            if re.search(pattern, input_value, re.IGNORECASE | re.MULTILINE):
                logger.warning(f"Suspicious input detected: {input_value[:100]}...")
                return False

        return True

    def sanitize_input(self, input_value: str) -> str:
        """净化输入参数"""
        if not input_value:
            return input_value

        # 去除多余空白
        sanitized = input_value.strip()

        # 转义HTML标签
        sanitized = html.escape(sanitized, quote=True)

        # 移除潜在危险字符序列
        dangerous_sequences = [
            'javascript:', 'vbscript:', 'data:',
            '<script', '</script>', '<iframe', '</iframe>',
            'onload=', 'onerror=', 'onclick='
        ]

        for seq in dangerous_sequences:
            # 不区分大小写替换
            sanitized = re.sub(seq, '', sanitized, flags=re.IGNORECASE)

        return sanitized

    def is_sensitive_field(self, field_name: str) -> bool:
        """检查字段是否为敏感字段"""
        field_lower = field_name.lower()
        return any(keyword in field_lower for keyword in self.config.sensitive_keywords)


class DataMasker:
    """
    数据脱敏器.

    实现敏感数据的脱敏处理。
    """

    @staticmethod
    def mask_phone(phone: str) -> str:
        """
        脱敏手机号.

        Args:
            phone: 手机号

        Returns:
            str: 脱敏后的手机号
        """
        if not phone:
            return phone

        # 处理带分隔符的手机号，只保留数字
        phone_digits = re.sub(r'[^\d]', '', phone)

        if len(phone_digits) != 11:
            # 如果不是11位，尝试匹配常见的格式
            match = re.match(r'(\d{3})\D*(\d{4})\D*(\d{4})', phone)
            if match:
                return f"{match.group(1)}****{match.group(3)}"
            return phone

        return phone_digits[:3] + "****" + phone_digits[-4:]

    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """
        脱敏身份证号.

        Args:
            id_card: 身份证号

        Returns:
            str: 脱敏后的身份证号
        """
        if not id_card:
            return id_card

        # 移除非数字字符
        id_digits = re.sub(r'[^\dXx]', '', id_card)

        if len(id_digits) != 18:
            return id_card

        return id_digits[:6] + "********" + id_digits[-4:]

    @staticmethod
    def mask_bank_card(card: str) -> str:
        """
        脱敏银行卡号.

        Args:
            card: 银行卡号

        Returns:
            str: 脱敏后的银行卡号
        """
        if not card:
            return card

        # 只保留数字
        card_digits = re.sub(r'[^\d]', '', card)

        if len(card_digits) < 8:
            return card

        return card_digits[:4] + "****" + card_digits[-4:]

    @staticmethod
    def mask_email(email: str) -> str:
        """
        脱敏邮箱.

        Args:
            email: 邮箱地址

        Returns:
            str: 脱敏后的邮箱
        """
        if not email or '@' not in email:
            return email

        parts = email.split('@')
        username = parts[0]
        domain = '@' + parts[1] if len(parts) > 1 else ''

        if len(username) <= 2:
            masked = username[0] + "***"
        else:
            masked = username[:2] + "***" + username[-1:] if len(username) > 3 else username[:2] + "*"

        return masked + domain

    @staticmethod
    def mask_general(text: str, visible_start: int = 2, visible_end: int = 2, mask_char: str = '*') -> str:
        """
        通用脱敏方法.

        Args:
            text: 待脱敏文本
            visible_start: 开头保留字符数
            visible_end: 结尾保留字符数
            mask_char: 脱敏字符

        Returns:
            str: 脱敏后的文本
        """
        if not text or len(text) <= (visible_start + visible_end):
            return text if text else ''

        start_part = text[:visible_start]
        end_part = text[-visible_end:] if visible_end > 0 else ''
        mask_length = len(text) - visible_start - visible_end

        return start_part + (mask_char * mask_length) + end_part

    @classmethod
    def mask_sensitive_data(cls, data: Union[str, Dict, List, Any]) -> Any:
        """脱敏敏感数据"""
        if isinstance(data, str):
            return cls._mask_string(data)
        elif isinstance(data, dict):
            return cls._mask_dict(data)
        elif isinstance(data, list):
            return [cls.mask_sensitive_data(item) for item in data]
        else:
            return data

    @classmethod
    def _mask_string(cls, value: str) -> str:
        """脱敏字符串"""
        if not value or len(value) < 4:
            return value

        # 根据不同模式进行脱敏
        # 手机号: 138****8888
        if re.match(r'^1[3-9]\d{9}$', re.sub(r'[^\d]', '', value)):
            return cls.mask_phone(value)

        # 邮箱: zhang***@example.com
        elif '@' in value and '.' in value:
            return cls.mask_email(value)

        # 身份证: 110101**********1234
        elif re.match(r'^\d{17}[\dXx]$', re.sub(r'[^\dXx]', '', value)):
            return cls.mask_id_card(value)

        # 银行卡: **** **** **** 1234
        elif re.match(r'^\d{16,19}$', re.sub(r'[^\d]', '', value)):
            return cls.mask_bank_card(value)

        # 通用脱敏: 只保留前2位和后2位
        else:
            if len(value) > 4:
                return cls.mask_general(value)
            else:
                return '*' * len(value)

    @classmethod
    def _mask_dict(cls, data: Dict) -> Dict:
        """脱敏字典数据"""
        result = {}
        for key, value in data.items():
            if cls._is_sensitive_field(key):
                result[key] = cls.mask_sensitive_data(str(value))
            else:
                result[key] = cls.mask_sensitive_data(value)
        return result

    @staticmethod
    def _is_sensitive_field(field_name: str) -> bool:
        """检查字段是否为敏感字段"""
        config = SecurityConfig()
        field_lower = field_name.lower()
        return any(keyword in field_lower for keyword in config.sensitive_keywords)


class InputValidator:
    """
    输入校验器.

    实现输入数据的校验和净化。
    """

    def __init__(self, config: SecurityConfig = None):
        self.security_validator = SecurityValidator(config or SecurityConfig())

    def validate_sql_injection(
        self,
        input_string: str,
    ) -> bool:
        """
        检测SQL注入.

        Args:
            input_string: 输入字符串

        Returns:
            bool: 是否存在SQL注入风险
        """
        sql_injection_patterns = [
            r"(?i)(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b)",
            r"(?i)(\b(UNION|JOIN)\b.*\b(SELECT|FROM)\b)",
            r"(--|#|/\*|\*/)",
            r"(?i)(\b(OR|AND)\b.*=)",
            r"(\bEXEC\b|\bEXECUTE\b)",
        ]

        for pattern in sql_injection_patterns:
            if re.search(pattern, input_string):
                logger.warning(
                    "Potential SQL injection detected",
                    extra={"input_preview": input_string[:50]},
                )
                return False
        return True

    def validate_xss(
        self,
        input_string: str,
    ) -> bool:
        """
        检测XSS攻击.

        Args:
            input_string: 输入字符串

        Returns:
            bool: 是否存在XSS风险
        """
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe",
            r"<object",
            r"<embed",
        ]

        for pattern in xss_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                logger.warning(
                    "Potential XSS detected",
                    extra={"input_preview": input_string[:50]},
                )
                return False
        return True

    def sanitize_input(
        self,
        input_string: str,
        max_length: int = 10000,
    ) -> str:
        """
        净化输入.

        Args:
            input_string: 输入字符串
            max_length: 最大长度

        Returns:
            str: 净化后的字符串
        """
        return self.security_validator.sanitize_input(input_string)[:max_length]

    def validate_input(
        self,
        input_string: str,
        check_sql: bool = True,
        check_xss: bool = True,
        max_length: int = 10000,
    ) -> Dict[str, Any]:
        """
        综合校验输入.

        Args:
            input_string: 输入字符串
            check_sql: 是否检查SQL注入
            check_xss: 是否检查XSS
            max_length: 最大长度

        Returns:
            Dict: 校验结果
        """
        result = {
            "is_valid": True,
            "errors": [],
            "sanitized": input_string,
        }

        # 长度检查
        if len(input_string) > max_length:
            result["is_valid"] = False
            result["errors"].append(f"Input exceeds maximum length of {max_length}")

        # 通用安全检查
        if not self.security_validator.validate_input(input_string):
            result["is_valid"] = False
            result["errors"].append("Input contains forbidden patterns")

        if check_sql and not self.validate_sql_injection(input_string):
            result["is_valid"] = False
            result["errors"].append("Potential SQL injection detected")

        if check_xss and not self.validate_xss(input_string):
            result["is_valid"] = False
            result["errors"].append("Potential XSS detected")

        result["sanitized"] = self.sanitize_input(input_string, max_length)

        return result


class ContentComplianceChecker:
    """
    内容合规检查器.

    检查内容是否符合合规要求。
    """

    # 敏感词列表（示例）
    SENSITIVE_WORDS = [
        "政治敏感词",
        "违禁词",
    ]

    @classmethod
    def check(
        cls,
        content: str,
    ) -> Dict[str, Any]:
        """
        检查内容合规性.

        Args:
            content: 待检查内容

        Returns:
            Dict: 检查结果
        """
        violations = []

        # 敏感词检查
        for word in cls.SENSITIVE_WORDS:
            if word in content:
                violations.append(f"包含敏感词: {word}")

        return {
            "is_compliant": len(violations) == 0,
            "violations": violations,
            "content_preview": content[:100],
        }


class PromptInjectionGuard:
    """
    提示词注入防护.

    检测和防护提示词注入攻击。
    """

    INJECTION_PATTERNS = [
        r"ignore\s+(previous|all|above)\s+(instructions?|prompts?)",
        r"(show|reveal|display)\s+(your|the)\s+(prompt|instructions?)",
        r"(you\s+are|act\s+as|pretend)",
        r"(bypass|override|disable)\s+(restrictions?|filters?)",
        r"system\s+message|system\s+prompt",
        r"forget\s+(everything|all|previous)",
    ]

    @classmethod
    def check(
        cls,
        prompt: str,
    ) -> Dict[str, Any]:
        """
        检查提示词注入.

        Args:
            prompt: 用户输入

        Returns:
            Dict: 检查结果
        """
        detected_patterns = []

        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                detected_patterns.append(pattern)

        is_safe = len(detected_patterns) == 0

        if not is_safe:
            logger.warning(
                "Prompt injection detected",
                extra={
                    "patterns": detected_patterns,
                    "prompt_preview": prompt[:100],
                },
            )

        return {
            "is_safe": is_safe,
            "detected_patterns": detected_patterns,
            "risk_level": "high" if detected_patterns else "low",
        }


# 导出安全模块
__all__ = [
    "InputValidator",
    "DataMasker",
    "ContentComplianceChecker",
    "PromptInjectionGuard",
    "SecurityValidator",
    "SecurityConfig",
]