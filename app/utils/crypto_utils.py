"""
PM Digital Employee - Crypto Utilities
项目经理数字员工系统 - 加密工具

整合加密、解密、签名验证等功能。
"""

import hashlib
import hmac
import base64
from typing import Optional, Union

from cryptography.fernet import Fernet


def generate_key() -> bytes:
    """
    Generate a new Fernet encryption key.

    Returns:
        bytes: Encryption key
    """
    return Fernet.generate_key()


def encrypt(
    data: Union[str, bytes],
    key: bytes,
) -> str:
    """
    Encrypt data using Fernet symmetric encryption.

    Args:
        data: Data to encrypt
        key: Encryption key

    Returns:
        str: Encrypted data (base64 encoded)
    """
    fernet = Fernet(key)
    if isinstance(data, str):
        data = data.encode("utf-8")
    encrypted = fernet.encrypt(data)
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt(
    encrypted_data: str,
    key: bytes,
) -> str:
    """
    Decrypt data using Fernet symmetric encryption.

    Args:
        encrypted_data: Encrypted data (base64 encoded)
        key: Encryption key

    Returns:
        str: Decrypted data
    """
    fernet = Fernet(key)
    decoded = base64.b64decode(encrypted_data.encode("utf-8"))
    decrypted = fernet.decrypt(decoded)
    return decrypted.decode("utf-8")


def sha256_hash(
    data: Union[str, bytes],
) -> str:
    """
    Generate SHA-256 hash.

    Args:
        data: Data to hash

    Returns:
        str: Hex digest
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def hmac_sha256(
    data: Union[str, bytes],
    key: Union[str, bytes],
) -> str:
    """
    Generate HMAC-SHA256 signature.

    Args:
        data: Data to sign
        key: Secret key

    Returns:
        str: Hex digest
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    if isinstance(key, str):
        key = key.encode("utf-8")
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def verify_hmac(
    data: Union[str, bytes],
    key: Union[str, bytes],
    signature: str,
) -> bool:
    """
    Verify HMAC signature.

    Args:
        data: Original data
        key: Secret key
        signature: Expected signature

    Returns:
        bool: True if valid
    """
    expected = hmac_sha256(data, key)
    return hmac.compare_digest(expected, signature)


def base64_encode(
    data: Union[str, bytes],
) -> str:
    """
    Encode data to base64.

    Args:
        data: Data to encode

    Returns:
        str: Base64 encoded string
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.b64encode(data).decode("utf-8")


def base64_decode(
    encoded: str,
) -> str:
    """
    Decode base64 string.

    Args:
        encoded: Base64 encoded string

    Returns:
        str: Decoded string
    """
    return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")


def mask_sensitive(
    value: str,
    visible_prefix: int = 4,
    visible_suffix: int = 4,
) -> str:
    """
    Mask sensitive value for display.

    Args:
        value: Value to mask
        visible_prefix: Number of visible prefix chars
        visible_suffix: Number of visible suffix chars

    Returns:
        str: Masked value
    """
    if len(value) <= visible_prefix + visible_suffix:
        return "*" * len(value)

    prefix = value[:visible_prefix]
    suffix = value[-visible_suffix:]
    masked = "*" * (len(value) - visible_prefix - visible_suffix)
    return f"{prefix}{masked}{suffix}"


def is_valid_token_format(
    token: str,
    min_length: int = 20,
) -> bool:
    """
    Check if token has valid format.

    Args:
        token: Token string
        min_length: Minimum expected length

    Returns:
        bool: True if valid format
    """
    if not token:
        return False
    if len(token) < min_length:
        return False
    # Check for reasonable character set
    import re
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", token))


__all__ = [
    "generate_key",
    "encrypt",
    "decrypt",
    "sha256_hash",
    "hmac_sha256",
    "verify_hmac",
    "base64_encode",
    "base64_decode",
    "mask_sensitive",
    "is_valid_token_format",
]