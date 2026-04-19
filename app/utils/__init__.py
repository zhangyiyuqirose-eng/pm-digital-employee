"""
PM Digital Employee - Utils Module
项目经理数字员工系统 - 工具模块

提供各种工具函数：文档导出、时间处理、加密、验证等。
"""

from app.utils.docx_exporter import (
    DocxExporter,
    get_docx_exporter,
    export_report,
)
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
    generate_key,
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
    is_valid_status,
    sanitize_text,
    validate_dict_schema,
    validate_non_empty_string,
    validate_length,
)

__all__ = [
    # Docx Exporter
    "DocxExporter",
    "get_docx_exporter",
    "export_report",
    # Datetime Utils
    "format_datetime",
    "format_date",
    "to_china_timezone",
    "from_china_timezone",
    "get_week_range",
    "get_month_range",
    "get_quarter_range",
    "days_between",
    "is_workday",
    "get_workdays_between",
    "format_duration",
    "parse_chinese_date",
    # Crypto Utils
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
    # Validators
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