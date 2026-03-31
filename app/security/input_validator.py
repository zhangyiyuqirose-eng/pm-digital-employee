"""
PM Digital Employee - Security Module
项目经理数字员工系统 - 金融级安全治理模块
"""

import re
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class InputValidator:
    """
    输入校验器.

    实现输入数据的校验和净化。
    """

    # SQL注入模式
    SQL_INJECTION_PATTERNS = [
        r"(?i)(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b)",
        r"(?i)(\b(UNION|JOIN)\b.*\b(SELECT|FROM)\b)",
        r"(--|#|/\*|\*/)",
        r"(?i)(\b(OR|AND)\b.*=)",
        r"(\bEXEC\b|\bEXECUTE\b)",
    ]

    # XSS模式
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    @classmethod
    def validate_sql_injection(
        cls,
        input_string: str,
    ) -> bool:
        """
        检测SQL注入.

        Args:
            input_string: 输入字符串

        Returns:
            bool: 是否存在SQL注入风险
        """
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_string):
                logger.warning(
                    "Potential SQL injection detected",
                    input_preview=input_string[:50],
                )
                return False
        return True

    @classmethod
    def validate_xss(
        cls,
        input_string: str,
    ) -> bool:
        """
        检测XSS攻击.

        Args:
            input_string: 输入字符串

        Returns:
            bool: 是否存在XSS风险
        """
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                logger.warning(
                    "Potential XSS detected",
                    input_preview=input_string[:50],
                )
                return False
        return True

    @classmethod
    def sanitize_input(
        cls,
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
        # 截断
        sanitized = input_string[:max_length]

        # 移除危险字符
        sanitized = re.sub(r"<[^>]*>", "", sanitized)
        sanitized = sanitized.replace("'", "''")
        sanitized = sanitized.replace(";", "")

        return sanitized

    @classmethod
    def validate_input(
        cls,
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

        if check_sql and not cls.validate_sql_injection(input_string):
            result["is_valid"] = False
            result["errors"].append("Potential SQL injection detected")

        if check_xss and not cls.validate_xss(input_string):
            result["is_valid"] = False
            result["errors"].append("Potential XSS detected")

        if len(input_string) > max_length:
            result["is_valid"] = False
            result["errors"].append(f"Input exceeds maximum length of {max_length}")

        result["sanitized"] = cls.sanitize_input(input_string, max_length)

        return result


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
        if len(phone) != 11:
            return phone
        return phone[:3] + "****" + phone[-4:]

    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """
        脱敏身份证号.

        Args:
            id_card: 身份证号

        Returns:
            str: 脱敏后的身份证号
        """
        if len(id_card) != 18:
            return id_card
        return id_card[:6] + "********" + id_card[-4:]

    @staticmethod
    def mask_bank_card(card: str) -> str:
        """
        脱敏银行卡号.

        Args:
            card: 银行卡号

        Returns:
            str: 脱敏后的银行卡号
        """
        if len(card) < 8:
            return card
        return card[:4] + "****" + card[-4:]

    @staticmethod
    def mask_email(email: str) -> str:
        """
        脱敏邮箱.

        Args:
            email: 邮箱地址

        Returns:
            str: 脱敏后的邮箱
        """
        if "@" not in email:
            return email

        parts = email.split("@")
        username = parts[0]

        if len(username) <= 2:
            masked = username[0] + "***"
        else:
            masked = username[:2] + "***"

        return masked + "@" + parts[1]

    @classmethod
    def auto_mask(
        cls,
        text: str,
    ) -> str:
        """
        自动脱敏文本中的敏感信息.

        Args:
            text: 原始文本

        Returns:
            str: 脱敏后的文本
        """
        result = text

        # 手机号
        phone_pattern = re.compile(r"1[3-9]\d{9}")
        result = phone_pattern.sub(
            lambda m: cls.mask_phone(m.group()),
            result,
        )

        # 身份证
        id_pattern = re.compile(r"\d{17}[\dXx]")
        result = id_pattern.sub(
            lambda m: cls.mask_id_card(m.group()),
            result,
        )

        # 银行卡
        card_pattern = re.compile(r"\d{16,19}")
        result = card_pattern.sub(
            lambda m: cls.mask_bank_card(m.group()),
            result,
        )

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
                patterns=detected_patterns,
                prompt_preview=prompt[:100],
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
]