"""
PM Digital Employee - Validators
项目经理数字员工系统 - 输入验证工具

提供常用输入验证函数。
"""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from uuid import UUID


def is_valid_uuid(
    value: str,
) -> bool:
    """
    Validate UUID string.

    Args:
        value: UUID string

    Returns:
        bool: True if valid
    """
    try:
        UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def is_valid_email(
    email: str,
) -> bool:
    """
    Validate email format.

    Args:
        email: Email string

    Returns:
        bool: True if valid
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_phone(
    phone: str,
) -> bool:
    """
    Validate Chinese phone number.

    Args:
        phone: Phone string

    Returns:
        bool: True if valid
    """
    # Chinese mobile: 11 digits starting with 1
    pattern = r"^1[3-9]\d{9}$"
    return bool(re.match(pattern, phone))


def is_valid_date_string(
    date_str: str,
    format_str: str = "%Y-%m-%d",
) -> bool:
    """
    Validate date string format.

    Args:
        date_str: Date string
        format_str: Expected format

    Returns:
        bool: True if valid
    """
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False


def is_valid_project_code(
    code: str,
) -> bool:
    """
    Validate project code format.

    Args:
        code: Project code

    Returns:
        bool: True if valid
    """
    # Format: PRJ-YYYY-NNNN
    pattern = r"^PRJ-[0-9]{4}-[0-9]{3,4}$"
    return bool(re.match(pattern, code))


def is_valid_task_code(
    code: str,
) -> bool:
    """
    Validate task code format.

    Args:
        code: Task code

    Returns:
        bool: True if valid
    """
    # Format: PRJ-YYYY-NNNN-TNNN
    pattern = r"^PRJ-[0-9]{4}-[0-9]{3,4}-T[0-9]{3}$"
    return bool(re.match(pattern, code))


def is_valid_feishu_user_id(
    user_id: str,
) -> bool:
    """
    Validate Feishu user ID format.

    Args:
        user_id: User ID

    Returns:
        bool: True if valid
    """
    # Feishu open_id format: ou_xxxxx
    pattern = r"^ou_[a-zA-Z0-9_-]+$"
    return bool(re.match(pattern, user_id))


def is_valid_feishu_chat_id(
    chat_id: str,
) -> bool:
    """
    Validate Feishu chat ID format.

    Args:
        chat_id: Chat ID

    Returns:
        bool: True if valid
    """
    # Feishu chat_id format: oc_xxxxx
    pattern = r"^oc_[a-zA-Z0-9_-]+$"
    return bool(re.match(pattern, chat_id))


def is_valid_percentage(
    value: Union[int, float, str],
) -> bool:
    """
    Validate percentage value (0-100).

    Args:
        value: Percentage value

    Returns:
        bool: True if valid
    """
    try:
        num = float(value)
        return 0 <= num <= 100
    except (ValueError, TypeError):
        return False


def is_valid_amount(
    value: Union[int, float, str, Decimal],
    allow_negative: bool = False,
) -> bool:
    """
    Validate monetary amount.

    Args:
        value: Amount value
        allow_negative: Allow negative values

    Returns:
        bool: True if valid
    """
    try:
        num = float(value)
        if allow_negative:
            return True
        return num >= 0
    except (ValueError, TypeError):
        return False


def is_valid_priority(
    priority: str,
) -> bool:
    """
    Validate task priority.

    Args:
        priority: Priority string

    Returns:
        bool: True if valid
    """
    valid_priorities = ["low", "medium", "high", "critical"]
    return priority.lower() in valid_priorities


def is_valid_status(
    status: str,
    valid_statuses: List[str],
) -> bool:
    """
    Validate status against allowed values.

    Args:
        status: Status string
        valid_statuses: List of valid statuses

    Returns:
        bool: True if valid
    """
    return status.lower() in [s.lower() for s in valid_statuses]


def sanitize_text(
    text: str,
    max_length: Optional[int] = None,
    strip_html: bool = True,
) -> str:
    """
    Sanitize text input.

    Args:
        text: Input text
        max_length: Maximum length
        strip_html: Remove HTML tags

    Returns:
        str: Sanitized text
    """
    # Strip whitespace
    text = text.strip()

    # Remove HTML tags if requested
    if strip_html:
        text = re.sub(r"<[^>]+>", "", text)

    # Truncate if max_length
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def validate_dict_schema(
    data: Dict[str, Any],
    required_fields: List[str],
    optional_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validate dictionary against schema.

    Args:
        data: Data dictionary
        required_fields: Required field names
        optional_fields: Optional field names

    Returns:
        Dict: Validation result with 'valid' and 'errors' keys
    """
    errors = []

    # Check required fields
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif data[field] is None:
            errors.append(f"Required field is None: {field}")

    # Check for unexpected fields
    all_expected = set(required_fields + (optional_fields or []))
    unexpected = set(data.keys()) - all_expected
    if unexpected:
        errors.append(f"Unexpected fields: {', '.join(unexpected)}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def validate_non_empty_string(
    value: str,
    field_name: str,
) -> Dict[str, Any]:
    """
    Validate non-empty string.

    Args:
        value: String value
        field_name: Field name for error message

    Returns:
        Dict: Validation result
    """
    if not value or not value.strip():
        return {
            "valid": False,
            "error": f"{field_name} cannot be empty",
        }
    return {"valid": True}


def validate_length(
    value: str,
    min_length: int,
    max_length: int,
    field_name: str,
) -> Dict[str, Any]:
    """
    Validate string length.

    Args:
        value: String value
        min_length: Minimum length
        max_length: Maximum length
        field_name: Field name

    Returns:
        Dict: Validation result
    """
    length = len(value)
    if length < min_length:
        return {
            "valid": False,
            "error": f"{field_name} must be at least {min_length} characters",
        }
    if length > max_length:
        return {
            "valid": False,
            "error": f"{field_name} must be at most {max_length} characters",
        }
    return {"valid": True}


__all__ = [
    "is_valid_uuid",
    "is_valid_email",
    "is_valid_phone",
    "is_valid_date_string",
    "is_valid_project_code",
    "is_valid_task_code",
    "is_valid_feishu_user_id",
    "is_valid_feishu_chat_id",
    "is_valid_percentage",
    "is_valid_amount",
    "is_valid_priority",
    "is_valid_status",
    "sanitize_text",
    "validate_dict_schema",
    "validate_non_empty_string",
    "validate_length",
]