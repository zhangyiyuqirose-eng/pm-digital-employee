"""
PM Digital Employee - Encryption & Log Sanitizer Tests
Tests for data encryption and log sanitization.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestDataEncryptor:
    """Tests for DataEncryptor."""

    def test_encryptor_initialization(self):
        """Should initialize encryptor."""
        from app.core.encryption import DataEncryptor

        encryptor = DataEncryptor()
        assert encryptor is not None
        assert encryptor._fernet is not None

    def test_encrypt_decrypt_cycle(self):
        """Should encrypt and decrypt correctly."""
        from app.core.encryption import DataEncryptor

        encryptor = DataEncryptor()
        plaintext = "13812345678"

        encrypted = encryptor.encrypt(plaintext)
        assert encrypted is not None
        assert encrypted != plaintext

        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_none_returns_none(self):
        """Should return None for None input."""
        from app.core.encryption import DataEncryptor

        encryptor = DataEncryptor()
        result = encryptor.encrypt(None)
        assert result is None

    def test_decrypt_none_returns_none(self):
        """Should return None for None input."""
        from app.core.encryption import DataEncryptor

        encryptor = DataEncryptor()
        result = encryptor.decrypt(None)
        assert result is None

    def test_encrypt_empty_returns_none(self):
        """Should return None for empty string."""
        from app.core.encryption import DataEncryptor

        encryptor = DataEncryptor()
        result = encryptor.encrypt("")
        assert result is None

    def test_encrypt_phone(self):
        """Should encrypt phone number."""
        from app.core.encryption import DataEncryptor

        encryptor = DataEncryptor()
        phone = "13812345678"

        encrypted = encryptor.encrypt_phone(phone)
        assert encrypted is not None
        assert encrypted != phone

        decrypted = encryptor.decrypt_phone(encrypted)
        assert decrypted == phone

    def test_encrypt_email(self):
        """Should encrypt email."""
        from app.core.encryption import DataEncryptor

        encryptor = DataEncryptor()
        email = "test@example.com"

        encrypted = encryptor.encrypt_email(email)
        assert encrypted is not None
        assert encrypted != email

        decrypted = encryptor.decrypt_email(encrypted)
        assert decrypted == email


class TestMaskUtils:
    """Tests for MaskUtils."""

    def test_mask_phone(self):
        """Should mask phone number."""
        from app.core.encryption import MaskUtils

        result = MaskUtils.mask_phone("13812345678")
        assert result == "138****5678"

    def test_mask_phone_short(self):
        """Should return original for short phone."""
        from app.core.encryption import MaskUtils

        result = MaskUtils.mask_phone("123")
        assert result == "123"

    def test_mask_phone_none(self):
        """Should return None for None input."""
        from app.core.encryption import MaskUtils

        result = MaskUtils.mask_phone(None)
        assert result is None

    def test_mask_email(self):
        """Should mask email."""
        from app.core.encryption import MaskUtils

        result = MaskUtils.mask_email("test@example.com")
        assert result == "te***@example.com"

    def test_mask_email_short(self):
        """Should mask short email prefix."""
        from app.core.encryption import MaskUtils

        result = MaskUtils.mask_email("a@example.com")
        assert result == "*@example.com"

    def test_mask_email_none(self):
        """Should return None for None input."""
        from app.core.encryption import MaskUtils

        result = MaskUtils.mask_email(None)
        assert result is None

    def test_mask_id_card(self):
        """Should mask ID card."""
        from app.core.encryption import MaskUtils

        result = MaskUtils.mask_id_card("123456789012345678")
        assert result == "123456********5678"

    def test_mask_bank_card(self):
        """Should mask bank card."""
        from app.core.encryption import MaskUtils

        result = MaskUtils.mask_bank_card("1234567890123456")
        assert result == "1234****3456"

    def test_mask_name(self):
        """Should mask name."""
        from app.core.encryption import MaskUtils

        result = MaskUtils.mask_name("张三")
        assert result == "张*"

    def test_mask_name_long(self):
        """Should mask long name."""
        from app.core.encryption import MaskUtils

        result = MaskUtils.mask_name("张三丰")
        assert result == "张**"


class TestLogSanitizer:
    """Tests for LogSanitizer."""

    def test_sanitize_phone(self):
        """Should sanitize phone in text."""
        from app.core.log_sanitizer import LogSanitizer

        sanitizer = LogSanitizer()
        result = sanitizer.sanitize("用户手机号13812345678登录成功")
        assert "13812345678" not in result
        assert "1****0000" in result

    def test_sanitize_email(self):
        """Should sanitize email in text."""
        from app.core.log_sanitizer import LogSanitizer

        sanitizer = LogSanitizer()
        result = sanitizer.sanitize("发送邮件到test@example.com")
        assert "test@example.com" not in result

    def test_sanitize_multiple(self):
        """Should sanitize multiple patterns."""
        from app.core.log_sanitizer import LogSanitizer

        sanitizer = LogSanitizer()
        result = sanitizer.sanitize("手机13812345678邮箱test@example.com")
        assert "13812345678" not in result
        assert "test@example.com" not in result

    def test_sanitize_none(self):
        """Should return None for None input."""
        from app.core.log_sanitizer import LogSanitizer

        sanitizer = LogSanitizer()
        result = sanitizer.sanitize(None)
        assert result is None

    def test_sanitize_dict(self):
        """Should sanitize dict values."""
        from app.core.log_sanitizer import LogSanitizer

        sanitizer = LogSanitizer()
        data = {
            "phone": "13812345678",
            "email": "test@example.com",
            "name": "张三"
        }
        result = sanitizer.sanitize_dict(data)

        assert "13812345678" not in result.get("phone", "")
        assert "test@example.com" not in result.get("email", "")

    def test_sanitize_dict_sensitive_keys(self):
        """Should redact sensitive keys."""
        from app.core.log_sanitizer import LogSanitizer

        sanitizer = LogSanitizer()
        data = {
            "password": "secret123",
            "token": "abc123",
            "name": "张三"
        }
        result = sanitizer.sanitize_dict(data)

        assert result["password"] == "[REDACTED]"
        assert result["token"] == "[REDACTED]"
        assert result["name"] == "张三"

    def test_is_sensitive_key(self):
        """Should detect sensitive keys."""
        from app.core.log_sanitizer import LogSanitizer

        sanitizer = LogSanitizer()

        assert sanitizer._is_sensitive_key("password")
        assert sanitizer._is_sensitive_key("user_phone")
        assert sanitizer._is_sensitive_key("email_address")
        assert not sanitizer._is_sensitive_key("name")
        assert not sanitizer._is_sensitive_key("id")

    def test_sanitize_user_id(self):
        """Should sanitize Lark user ID."""
        from app.core.log_sanitizer import LogSanitizer

        sanitizer = LogSanitizer()
        result = sanitizer.sanitize_user_id("ou_abc123def456")
        assert result == "ou_****f456"


class TestGenerateEncryptionKey:
    """Tests for generate_encryption_key."""

    def test_generate_key(self):
        """Should generate valid encryption key."""
        from app.core.encryption import generate_encryption_key

        key = generate_encryption_key()
        assert key is not None
        assert len(key) > 0

        # Verify key is usable
        from app.core.encryption import DataEncryptor
        encryptor = DataEncryptor(encryption_key=key)
        encrypted = encryptor.encrypt("test")
        assert encrypted is not None


class TestGetEncryptor:
    """Tests for get_encryptor."""

    def test_get_encryptor_singleton(self):
        """Should return same instance."""
        from app.core.encryption import get_encryptor

        e1 = get_encryptor()
        e2 = get_encryptor()
        assert e1 is e2


class TestSanitizeForLog:
    """Tests for sanitize_for_log shortcut."""

    def test_sanitize_for_log(self):
        """Should sanitize text."""
        from app.core.log_sanitizer import sanitize_for_log

        result = sanitize_for_log("手机13812345678")
        assert "13812345678" not in result