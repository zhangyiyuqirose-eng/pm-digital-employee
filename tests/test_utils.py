"""
PM Digital Employee - Comprehensive Utils Tests
项目经理数字员工系统 - 工具函数全面测试
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.utils.datetime_utils import (
    format_datetime,
    format_date,
    to_china_timezone,
    from_china_timezone,
    get_week_range,
    get_month_range,
    get_quarter_range,
    days_between,
    is_workday,
    get_workdays_between,
    format_duration,
    parse_chinese_date,
)
from app.utils.crypto_utils import (
    encrypt,
    decrypt,
    sha256_hash,
    hmac_sha256,
    verify_hmac,
    base64_encode,
    base64_decode,
    mask_sensitive,
    is_valid_token_format,
)
from app.utils.validators import (
    is_valid_uuid,
    is_valid_email,
    is_valid_phone,
    is_valid_date_string,
    is_valid_project_code,
    is_valid_task_code,
    is_valid_feishu_user_id,
    is_valid_feishu_chat_id,
    is_valid_percentage,
    is_valid_amount,
    is_valid_priority,
    sanitize_text,
    validate_dict_schema,
    validate_length,
)


class TestDatetimeUtils:
    """Datetime utility tests."""

    def test_format_datetime_default(self):
        """Test default datetime format."""
        dt = datetime(2026, 4, 19, 14, 30, 45)
        result = format_datetime(dt)
        assert result == "2026-04-19 14:30:45"

    def test_format_datetime_custom(self):
        """Test custom datetime format."""
        dt = datetime(2026, 4, 19)
        result = format_datetime(dt, "%Y/%m/%d")
        assert result == "2026/04/19"

    def test_format_date_default(self):
        """Test default date format."""
        d = date(2026, 4, 19)
        result = format_date(d)
        assert result == "2026-04-19"

    def test_to_china_timezone_utc(self):
        """Test convert UTC to China timezone."""
        dt = datetime(2026, 4, 19, 6, 0, 0, tzinfo=timezone.utc)
        result = to_china_timezone(dt)
        assert result.hour == 14

    def test_get_week_range_monday(self):
        """Test week range from Monday."""
        d = date(2026, 4, 19)  # Saturday
        start, end = get_week_range(d)
        assert start == date(2026, 4, 13)  # Monday
        assert end == date(2026, 4, 19)  # Sunday

    def test_get_week_range_sunday(self):
        """Test week range from Sunday."""
        # 2026-04-19 is Sunday (weekday=6)
        d = date(2026, 4, 19)  # Sunday
        start, end = get_week_range(d)
        # Sunday 4/19 has weekday=6, so week starts 6 days earlier = 4/13 (Monday)
        assert start == date(2026, 4, 13)  # Monday of that week
        assert end == date(2026, 4, 19)  # Sunday of that week

    def test_get_month_range(self):
        """Test month range."""
        d = date(2026, 4, 15)
        start, end = get_month_range(d)
        assert start == date(2026, 4, 1)
        assert end == date(2026, 4, 30)

    def test_get_month_range_december(self):
        """Test December month range."""
        d = date(2026, 12, 15)
        start, end = get_month_range(d)
        assert start == date(2026, 12, 1)
        assert end == date(2026, 12, 31)

    def test_days_between(self):
        """Test days between dates."""
        start = date(2026, 4, 1)
        end = date(2026, 4, 19)
        result = days_between(start, end)
        assert result == 18

    def test_is_workday_weekday(self):
        """Test weekday is workday."""
        # 2026-04-21 is Monday (weekday=0)
        d = date(2026, 4, 21)  # Monday
        assert is_workday(d) is True

    def test_is_workday_weekend(self):
        """Test weekend is not workday."""
        d = date(2026, 4, 19)  # Saturday
        assert is_workday(d) is False

    def test_format_duration_minutes(self):
        """Test duration format minutes."""
        assert format_duration(45) == "45分钟"

    def test_format_duration_hours(self):
        """Test duration format hours."""
        assert format_duration(120) == "2小时"

    def test_format_duration_mixed(self):
        """Test duration format mixed."""
        assert format_duration(150) == "2小时30分钟"

    def test_parse_chinese_date_full(self):
        """Test parse full Chinese date."""
        result = parse_chinese_date("2026年4月19日")
        assert result == date(2026, 4, 19)

    def test_parse_chinese_date_short(self):
        """Test parse short Chinese date."""
        result = parse_chinese_date("4月19日")
        assert result.month == 4
        assert result.day == 19


class TestCryptoUtils:
    """Crypto utility tests."""

    def test_sha256_hash_string(self):
        """Test SHA256 hash string."""
        result = sha256_hash("test")
        assert len(result) == 64  # SHA256 produces 64 hex chars

    def test_sha256_hash_consistency(self):
        """Test SHA256 hash consistency."""
        hash1 = sha256_hash("test")
        hash2 = sha256_hash("test")
        assert hash1 == hash2

    def test_hmac_sha256(self):
        """Test HMAC-SHA256."""
        result = hmac_sha256("data", "key")
        assert len(result) == 64

    def test_verify_hmac_valid(self):
        """Test HMAC verification valid."""
        signature = hmac_sha256("data", "key")
        assert verify_hmac("data", "key", signature) is True

    def test_verify_hmac_invalid(self):
        """Test HMAC verification invalid."""
        signature = hmac_sha256("data", "key")
        assert verify_hmac("wrong", "key", signature) is False

    def test_base64_encode_decode(self):
        """Test base64 encode/decode."""
        encoded = base64_encode("test")
        decoded = base64_decode(encoded)
        assert decoded == "test"

    def test_mask_sensitive_short(self):
        """Test mask short value."""
        result = mask_sensitive("abcd")
        assert "*" in result

    def test_mask_sensitive_long(self):
        """Test mask long value."""
        result = mask_sensitive("1234567890abcdef", 4, 4)
        assert result.startswith("1234")
        assert result.endswith("cdef")
        assert "*" in result

    def test_is_valid_token_format_valid(self):
        """Test valid token format."""
        # Token should be at least 20 characters
        assert is_valid_token_format("abc123_-xyz789abcdefghijklmnop") is True

    def test_is_valid_token_format_invalid(self):
        """Test invalid token format."""
        assert is_valid_token_format("") is False
        assert is_valid_token_format("short") is False


class TestValidators:
    """Validator tests."""

    def test_is_valid_uuid_valid(self):
        """Test valid UUID."""
        assert is_valid_uuid("123e4567-e89b-12d3-a456-426614174000") is True

    def test_is_valid_uuid_invalid(self):
        """Test invalid UUID."""
        assert is_valid_uuid("not-a-uuid") is False

    def test_is_valid_email_valid(self):
        """Test valid email."""
        assert is_valid_email("test@example.com") is True

    def test_is_valid_email_invalid(self):
        """Test invalid email."""
        assert is_valid_email("invalid") is False
        assert is_valid_email("test@") is False

    def test_is_valid_phone_valid(self):
        """Test valid Chinese phone."""
        assert is_valid_phone("13812345678") is True

    def test_is_valid_phone_invalid(self):
        """Test invalid phone."""
        assert is_valid_phone("12345678") is False

    def test_is_valid_date_string_valid(self):
        """Test valid date string."""
        assert is_valid_date_string("2026-04-19") is True

    def test_is_valid_date_string_invalid(self):
        """Test invalid date string."""
        assert is_valid_date_string("2026/04/19") is False

    def test_is_valid_project_code_valid(self):
        """Test valid project code."""
        assert is_valid_project_code("PRJ-2026-001") is True

    def test_is_valid_project_code_invalid(self):
        """Test invalid project code."""
        assert is_valid_project_code("PRJ001") is False

    def test_is_valid_feishu_user_id_valid(self):
        """Test valid Feishu user ID."""
        assert is_valid_feishu_user_id("ou_abc123xyz") is True

    def test_is_valid_feishu_user_id_invalid(self):
        """Test invalid Feishu user ID."""
        assert is_valid_feishu_user_id("invalid") is False

    def test_is_valid_percentage_valid(self):
        """Test valid percentage."""
        assert is_valid_percentage(50) is True
        assert is_valid_percentage(100) is True
        assert is_valid_percentage(0) is True

    def test_is_valid_percentage_invalid(self):
        """Test invalid percentage."""
        assert is_valid_percentage(150) is False
        assert is_valid_percentage(-10) is False

    def test_is_valid_amount_valid(self):
        """Test valid amount."""
        assert is_valid_amount(1000) is True
        assert is_valid_amount("1000") is True

    def test_is_valid_priority_valid(self):
        """Test valid priority."""
        assert is_valid_priority("high") is True
        assert is_valid_priority("medium") is True
        assert is_valid_priority("low") is True

    def test_sanitize_text_basic(self):
        """Test text sanitization."""
        result = sanitize_text("  test  ")
        assert result == "test"

    def test_sanitize_text_html(self):
        """Test HTML stripping."""
        result = sanitize_text("<script>alert('xss')</script>test", strip_html=True)
        assert "<script>" not in result

    def test_sanitize_text_max_length(self):
        """Test max length truncation."""
        result = sanitize_text("abcdefghij", max_length=5)
        assert result == "abcde"

    def test_validate_dict_schema_valid(self):
        """Test valid dict schema."""
        data = {"name": "test", "value": 123}
        # Specify optional_fields to avoid unexpected field error
        result = validate_dict_schema(data, required_fields=["name"], optional_fields=["value"])
        assert result["valid"] is True

    def test_validate_dict_schema_missing(self):
        """Test missing required field."""
        data = {"value": 123}
        result = validate_dict_schema(data, required_fields=["name"])
        assert result["valid"] is False

    def test_validate_length_valid(self):
        """Test valid length."""
        result = validate_length("test", 1, 10, "field")
        assert result["valid"] is True

    def test_validate_length_too_short(self):
        """Test too short."""
        result = validate_length("", 1, 10, "field")
        assert result["valid"] is False

    def test_validate_length_too_long(self):
        """Test too long."""
        result = validate_length("abcdefghijk", 1, 10, "field")
        assert result["valid"] is False