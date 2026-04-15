"""
PM Digital Employee - Lark Signature Verification
PM Digital Employee System - Lark Open Platform event signature verification

Lark uses SHA-256 signature verification for event push callbacks.
"""

import hashlib
import time
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LarkSignatureVerifier:
    """
    Lark signature verifier.

    Lark event push uses SHA-256 signature:
    signature = SHA256(timestamp + nonce + encrypt_key + body)

    For challenge verification (URL validation), Lark sends a POST request
    with a JSON body containing a `challenge` field that should be echoed back.
    """

    @staticmethod
    def verify_signature(
        signature: str,
        timestamp: str,
        nonce: str,
        body: str = "",
        encrypt_key: Optional[str] = None,
    ) -> bool:
        """
        Verify Lark event push signature.

        Signature algorithm:
        1. Concatenate: timestamp + nonce + encrypt_key + body
        2. Compute SHA-256 digest
        3. Compare with provided signature

        Args:
            signature: Request signature from Lark
            timestamp: Request timestamp
            nonce: Random nonce string
            body: Raw request body
            encrypt_key: Lark app encrypt key (verification_token)

        Returns:
            bool: Whether signature is valid
        """
        encrypt_key = encrypt_key or settings.lark_encrypt_key

        if not encrypt_key:
            logger.warning("Lark encrypt_key not configured, skipping signature verification")
            return True

        # Build signature string
        sign_str = timestamp + nonce + encrypt_key + body

        # Compute SHA-256 signature
        calculated_signature = hashlib.sha256(sign_str.encode("utf-8")).hexdigest()

        # Constant-time comparison to prevent timing attacks
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
        signature: str,
        timestamp: str,
        nonce: str,
        body: str = "",
        encrypt_key: Optional[str] = None,
        max_age_seconds: int = 300,
    ) -> bool:
        """
        Verify Lark callback request (with timestamp check).

        Args:
            signature: Request signature
            timestamp: Request timestamp
            nonce: Random nonce
            body: Raw request body
            encrypt_key: Encrypt key
            max_age_seconds: Maximum allowed time difference (seconds)

        Returns:
            bool: Whether request is valid
        """
        # Check timestamp (anti-replay attack)
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
                return False
        except ValueError:
            logger.warning("Invalid timestamp format", timestamp=timestamp)
            return False

        # Verify signature
        return LarkSignatureVerifier.verify_signature(
            signature=signature,
            timestamp=timestamp,
            nonce=nonce,
            body=body,
            encrypt_key=encrypt_key,
        )

    @staticmethod
    def handle_challenge(challenge: str) -> dict:
        """
        Handle Lark URL verification challenge.

        When configuring the callback URL, Lark sends a POST request
        with a `challenge` field. The server must echo it back.

        Args:
            challenge: The challenge string from Lark

        Returns:
            dict: Response with challenge echoed back
        """
        logger.info("Lark challenge verification successful")
        return {"challenge": challenge}


def verify_lark_request(
    signature: str,
    timestamp: str,
    nonce: str,
    body: str = "",
) -> bool:
    """
    Convenience function: verify Lark request.

    Args:
        signature: Request signature
        timestamp: Request timestamp
        nonce: Random nonce
        body: Raw request body

    Returns:
        bool: Whether verification passed
    """
    return LarkSignatureVerifier.verify_request(
        signature=signature,
        timestamp=timestamp,
        nonce=nonce,
        body=body,
    )
