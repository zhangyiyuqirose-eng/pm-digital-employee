"""
PM Digital Employee - Security Utilities Module
项目经理数字员工系统 - 安全工具模块

实现基础安全能力：
- 密码哈希与验证
- 签名生成与验签
- Token生成与验证
- 随机密钥生成
- 敏感数据处理
"""

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthError, ErrorCode, LarkError, SecurityError
from app.core.logging import get_logger

logger = get_logger(__name__)


# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordManager:
    """密码管理器."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        哈希密码.

        Args:
            password: 明文密码

        Returns:
            str: 哈希后的密码
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码.

        Args:
            plain_password: 明文密码
            hashed_password: 哈希后的密码

        Returns:
            bool: 密码是否匹配
        """
        return pwd_context.verify(plain_password, hashed_password)


class TokenManager:
    """Token管理器."""

    ALGORITHM = "HS256"

    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        创建访问令牌.

        Args:
            data: 令牌负载数据
            expires_delta: 过期时间增量

        Returns:
            str: JWT令牌
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.security.jwt_access_token_expire_minutes
            )

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "jti": str(secrets.token_urlsafe(16)),
            }
        )

        encoded_jwt = jwt.encode(
            to_encode,
            settings.app.secret_key,
            algorithm=TokenManager.ALGORITHM,
        )

        logger.debug(
            "Access token created",
            subject=data.get("sub"),
            expires_at=expire.isoformat(),
        )

        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        创建刷新令牌.

        Args:
            data: 令牌负载数据
            expires_delta: 过期时间增量

        Returns:
            str: JWT刷新令牌
        """
        to_encode = data.copy()
        to_encode["type"] = "refresh"

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.security.jwt_refresh_token_expire_days
            )

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "jti": str(secrets.token_urlsafe(16)),
            }
        )

        encoded_jwt = jwt.encode(
            to_encode,
            settings.app.secret_key,
            algorithm=TokenManager.ALGORITHM,
        )

        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        解码并验证令牌.

        Args:
            token: JWT令牌

        Returns:
            Dict[str, Any]: 令牌负载数据

        Raises:
            AuthError: 令牌无效或已过期
        """
        try:
            payload = jwt.decode(
                token,
                settings.app.secret_key,
                algorithms=[TokenManager.ALGORITHM],
            )
            return payload
        except JWTError as exc:
            logger.warning(
                "Token decode failed",
                error=str(exc),
            )
            raise AuthError(
                error_code=ErrorCode.INVALID_TOKEN,
                message="认证令牌无效或已过期",
            )

    @staticmethod
    def verify_token(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
        """
        验证令牌并返回负载.

        Args:
            token: JWT令牌
            expected_type: 期望的令牌类型

        Returns:
            Dict[str, Any]: 令牌负载数据

        Raises:
            AuthError: 令牌验证失败
        """
        payload = TokenManager.decode_token(token)

        if expected_type and payload.get("type") != expected_type:
            raise AuthError(
                error_code=ErrorCode.INVALID_TOKEN,
                message="令牌类型不正确",
            )

        return payload


class LarkSignatureVerifier:
    """
    飞书签名验证器.

    实现飞书开放平台的事件签名验证算法。
    """

    @staticmethod
    def verify_signature(
        timestamp: str,
        nonce: str,
        body: str,
        signature: str,
        encrypt_key: Optional[str] = None,
    ) -> bool:
        """
        验证飞书事件签名.

        签名算法：
        1. 将timestamp + nonce + encrypt_key + body拼接
        2. 计算SHA256摘要
        3. 与签名对比

        Args:
            timestamp: 请求时间戳
            nonce: 请求随机数
            body: 请求体字符串
            signature: 请求签名
            encrypt_key: 加密密钥（可选）

        Returns:
            bool: 签名是否有效
        """
        if not settings.lark.verification_token:
            logger.warning("Lark verification token not configured, skipping signature verification")
            return True

        # 计算签名
        sign_base = timestamp + nonce + (encrypt_key or settings.lark.encrypt_key or "") + body
        calculated_signature = hashlib.sha256(sign_base.encode("utf-8")).hexdigest()

        # 使用常量时间比较防止时序攻击
        is_valid = secrets.compare_digest(calculated_signature, signature)

        if not is_valid:
            logger.warning(
                "Lark signature verification failed",
                calculated_signature_prefix=calculated_signature[:8],
                provided_signature_prefix=signature[:8],
            )

        return is_valid

    @staticmethod
    def verify_request(
        timestamp: str,
        nonce: str,
        body: str,
        signature: str,
        max_age_seconds: int = 300,
    ) -> bool:
        """
        验证飞书请求（包含时间戳检查）.

        Args:
            timestamp: 请求时间戳
            nonce: 请求随机数
            body: 请求体字符串
            signature: 请求签名
            max_age_seconds: 最大时间差（秒）

        Returns:
            bool: 请求是否有效

        Raises:
            LarkError: 签名验证失败
        """
        import time

        # 检查时间戳（防重放攻击）
        try:
            request_time = int(timestamp)
            current_time = int(time.time())

            if abs(current_time - request_time) > max_age_seconds:
                logger.warning(
                    "Lark request timestamp expired",
                    request_time=request_time,
                    current_time=current_time,
                    max_age_seconds=max_age_seconds,
                )
                raise LarkError(
                    error_code=ErrorCode.INVALID_SIGNATURE,
                    message="请求时间戳已过期",
                )
        except ValueError:
            raise LarkError(
                error_code=ErrorCode.INVALID_SIGNATURE,
                message="无效的时间戳格式",
            )

        # 验证签名
        if not LarkSignatureVerifier.verify_signature(timestamp, nonce, body, signature):
            raise LarkError(
                error_code=ErrorCode.INVALID_SIGNATURE,
                message="签名验证失败",
            )

        return True


class SecretGenerator:
    """密钥生成器."""

    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """
        生成API密钥.

        Args:
            length: 密钥长度

        Returns:
            str: URL安全的随机密钥
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_numeric_code(length: int = 6) -> str:
        """
        生成数字验证码.

        Args:
            length: 验证码长度

        Returns:
            str: 数字验证码
        """
        return "".join(secrets.choice("0123456789") for _ in range(length))

    @staticmethod
    def generate_uuid() -> str:
        """
        生成UUID.

        Returns:
            str: UUID字符串
        """
        return str(uuid.uuid4()) if "uuid" in dir() else secrets.token_hex(16)


class DataMasker:
    """数据脱敏器."""

    @staticmethod
    def mask_phone(phone: str) -> str:
        """
        脱敏手机号.

        保留前3后4位，中间用*代替。
        例：13812345678 -> 138****5678

        Args:
            phone: 手机号

        Returns:
            str: 脱敏后的手机号
        """
        if len(phone) != 11:
            return phone[:3] + "****" + phone[-2:] if len(phone) > 5 else phone

        return phone[:3] + "****" + phone[-4:]

    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """
        脱敏身份证号.

        保留前6后4位，中间用*代替。
        例：110101199001011234 -> 110101********1234

        Args:
            id_card: 身份证号

        Returns:
            str: 脱敏后的身份证号
        """
        if len(id_card) < 10:
            return id_card[:2] + "****"

        return id_card[:6] + "*" * (len(id_card) - 10) + id_card[-4:]

    @staticmethod
    def mask_bank_card(card_no: str) -> str:
        """
        脱敏银行卡号.

        保留前4后4位，中间用*代替。
        例：6222021234567890 -> 6222********7890

        Args:
            card_no: 银行卡号

        Returns:
            str: 脱敏后的银行卡号
        """
        if len(card_no) < 8:
            return card_no[:2] + "****"

        return card_no[:4] + "*" * (len(card_no) - 8) + card_no[-4:]

    @staticmethod
    def mask_email(email: str) -> str:
        """
        脱敏邮箱地址.

        例：test@example.com -> t***@example.com

        Args:
            email: 邮箱地址

        Returns:
            str: 脱敏后的邮箱地址
        """
        if "@" not in email:
            return email[:1] + "***"

        parts = email.split("@")
        username = parts[0]
        domain = parts[1]

        if len(username) <= 1:
            masked_username = username
        elif len(username) <= 3:
            masked_username = username[0] + "***"
        else:
            masked_username = username[0] + "***" + username[-1]

        return f"{masked_username}@{domain}"

    @staticmethod
    def mask_name(name: str) -> str:
        """
        脱敏姓名.

        保留姓氏，其余用*代替。
        例：张三 -> 张*

        Args:
            name: 姓名

        Returns:
            str: 脱敏后的姓名
        """
        if len(name) <= 1:
            return name

        return name[0] + "*" * (len(name) - 1)

    @staticmethod
    def mask_amount(amount: str) -> str:
        """
        脱敏金额.

        显示区间而非精确值。
        例：123456.78 -> 10万-50万

        Args:
            amount: 金额字符串

        Returns:
            str: 脱敏后的金额区间
        """
        try:
            value = float(amount)

            if value < 10000:
                return "1万以下"
            elif value < 100000:
                return "1万-10万"
            elif value < 500000:
                return "10万-50万"
            elif value < 1000000:
                return "50万-100万"
            elif value < 5000000:
                return "100万-500万"
            else:
                return "500万以上"
        except (ValueError, TypeError):
            return "***"


# 导入uuid用于SecretGenerator
import uuid  # noqa: E402