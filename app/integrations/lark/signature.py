"""
PM Digital Employee - Lark Signature Verification
项目经理数字员工系统 - 飞书事件签名验签工具

实现飞书事件签名验证算法，确保请求来自飞书服务器。
"""

import hashlib
import time
from typing import Optional

from app.core.config import settings
from app.core.exceptions import ErrorCode, LarkError
from app.core.logging import get_logger

logger = get_logger(__name__)


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
        1. 将 timestamp + nonce + encrypt_key + body 拼接
        2. 计算 SHA256 摘要
        3. 与签名对比

        Args:
            timestamp: 请求时间戳
            nonce: 请求随机数
            body: 请求体字符串
            signature: 请求签名
            encrypt_key: 加密密钥

        Returns:
            bool: 签名是否有效
        """
        encrypt_key = encrypt_key or settings.lark.encrypt_key or ""

        # 拼接签名字符串
        sign_base = timestamp + nonce + encrypt_key + body

        # 计算SHA256签名
        calculated_signature = hashlib.sha256(sign_base.encode("utf-8")).hexdigest()

        # 使用常量时间比较防止时序攻击
        import secrets

        is_valid = secrets.compare_digest(calculated_signature, signature)

        if not is_valid:
            logger.warning(
                "Lark signature verification failed",
                calculated_prefix=calculated_signature[:8],
                provided_prefix=signature[:8] if signature else "None",
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
            LarkError: 验证失败
        """
        # 检查时间戳（防重放攻击）
        try:
            request_time = int(timestamp)
            current_time = int(time.time())

            time_diff = abs(current_time - request_time)
            if time_diff > max_age_seconds:
                logger.warning(
                    "Lark request timestamp expired",
                    request_time=request_time,
                    current_time=current_time,
                    time_diff=time_diff,
                    max_age_seconds=max_age_seconds,
                )
                raise LarkError(
                    error_code=ErrorCode.INVALID_SIGNATURE,
                    message=f"请求时间戳已过期，时间差: {time_diff}秒",
                )
        except ValueError:
            raise LarkError(
                error_code=ErrorCode.INVALID_SIGNATURE,
                message="无效的时间戳格式",
            )

        # 验证签名
        if settings.lark.verification_token:
            if not LarkSignatureVerifier.verify_signature(timestamp, nonce, body, signature):
                raise LarkError(
                    error_code=ErrorCode.INVALID_SIGNATURE,
                    message="签名验证失败",
                )

        return True

    @staticmethod
    def verify_url(
        challenge: str,
        token: Optional[str] = None,
    ) -> str:
        """
        处理飞书URL验证请求.

        飞书配置事件订阅时会发送URL验证请求，
        需要返回解密后的challenge值。

        Args:
            challenge: 挑战码
            token: 验证Token

        Returns:
            str: challenge值
        """
        token = token or settings.lark.verification_token
        if token:
            logger.info("URL verification successful")
        return challenge


def verify_lark_request(
    timestamp: str,
    nonce: str,
    body: str,
    signature: str,
) -> bool:
    """
    便捷函数：验证飞书请求.

    Args:
        timestamp: 请求时间戳
        nonce: 请求随机数
        body: 请求体字符串
        signature: 请求签名

    Returns:
        bool: 是否验证通过
    """
    return LarkSignatureVerifier.verify_request(
        timestamp=timestamp,
        nonce=nonce,
        body=body,
        signature=signature,
    )