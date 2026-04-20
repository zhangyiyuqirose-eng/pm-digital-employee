"""
PM Digital Employee - Lark Signature Tests
Tests for Lark signature verification and challenge handling.
"""

import hashlib
import time
from unittest.mock import patch

import pytest

from app.integrations.lark.signature import (
    LarkSignatureVerifier,
    verify_lark_request,
)


class TestLarkSignatureVerifier:
    """Tests for LarkSignatureVerifier class."""

    def test_verify_signature_valid(self):
        """Valid signature should pass."""
        timestamp = str(int(time.time()))
        nonce = "test_nonce"
        encrypt_key = "test_encrypt_key"
        body = '{"test": "data"}'

        # Build correct signature
        sign_str = timestamp + nonce + encrypt_key + body
        signature = hashlib.sha256(sign_str.encode("utf-8")).hexdigest()

        with patch("app.integrations.lark.signature.settings") as mock_settings:
            mock_settings.lark_encrypt_key = encrypt_key
            result = LarkSignatureVerifier.verify_signature(
                signature=signature,
                timestamp=timestamp,
                nonce=nonce,
                body=body,
            )

        assert result is True

    def test_verify_signature_invalid(self):
        """Invalid signature should fail."""
        timestamp = str(int(time.time()))
        nonce = "test_nonce"
        encrypt_key = "test_encrypt_key"

        with patch("app.integrations.lark.signature.settings") as mock_settings:
            mock_settings.lark_encrypt_key = encrypt_key
            result = LarkSignatureVerifier.verify_signature(
                signature="invalid_signature",
                timestamp=timestamp,
                nonce=nonce,
                body="",
            )

        assert result is False

    def test_verify_signature_no_key_configured(self):
        """Should pass when encrypt_key is not configured (warn and skip)."""
        with patch("app.integrations.lark.signature.settings") as mock_settings:
            mock_settings.lark_encrypt_key = ""
            result = LarkSignatureVerifier.verify_signature(
                signature="",
                timestamp="",
                nonce="",
            )

        assert result is True

    def test_verify_request_expired_timestamp(self):
        """Should fail for expired timestamp."""
        old_timestamp = str(int(time.time()) - 600)  # 10 minutes ago

        with patch("app.integrations.lark.signature.settings") as mock_settings:
            mock_settings.lark_encrypt_key = "test_key"
            result = LarkSignatureVerifier.verify_request(
                signature="",
                timestamp=old_timestamp,
                nonce="",
                max_age_seconds=300,
            )

        assert result is False

    def test_verify_request_invalid_timestamp(self):
        """Should fail for non-numeric timestamp."""
        with patch("app.integrations.lark.signature.settings") as mock_settings:
            mock_settings.lark_encrypt_key = "test_key"
            result = LarkSignatureVerifier.verify_request(
                signature="",
                timestamp="not_a_number",
                nonce="",
            )

        assert result is False

    def test_handle_challenge(self):
        """Challenge verification should echo back challenge."""
        challenge = "test_challenge_value"
        result = LarkSignatureVerifier.handle_challenge(challenge)

        assert result == {"challenge": challenge}


class TestVerifyLarkRequest:
    """Tests for verify_lark_request convenience function."""

    def test_valid_request(self):
        """Valid request should pass."""
        timestamp = str(int(time.time()))
        nonce = "test_nonce"
        encrypt_key = "test_key"
        body = ""

        sign_str = timestamp + nonce + encrypt_key + body
        signature = hashlib.sha256(sign_str.encode("utf-8")).hexdigest()

        with patch("app.integrations.lark.signature.settings") as mock_settings:
            mock_settings.lark_encrypt_key = encrypt_key
            result = verify_lark_request(
                signature=signature,
                timestamp=timestamp,
                nonce=nonce,
                body=body,
            )

        assert result is True

    def test_invalid_request(self):
        """Invalid request should fail."""
        with patch("app.integrations.lark.signature.settings") as mock_settings:
            mock_settings.lark_encrypt_key = "test_key"
            result = verify_lark_request(
                signature="bad",
                timestamp=str(int(time.time())),
                nonce="nonce",
                body="",
            )

        assert result is False
