"""
PM Digital Employee - Datetime Utilities
项目经理数字员工系统 - 时间处理工具

提供时间格式化、时区转换、周期计算等工具函数。
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional, Tuple


def format_datetime(
    dt: datetime,
    format_str: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """
    Format datetime to string.

    Args:
        dt: Datetime object
        format_str: Format string

    Returns:
        str: Formatted string
    """
    return dt.strftime(format_str)


def format_date(
    d: date,
    format_str: str = "%Y-%m-%d",
) -> str:
    """
    Format date to string.

    Args:
        d: Date object
        format_str: Format string

    Returns:
        str: Formatted string
    """
    return d.strftime(format_str)


def to_china_timezone(
    dt: datetime,
) -> datetime:
    """
    Convert datetime to China timezone (UTC+8).

    Args:
        dt: Datetime object

    Returns:
        datetime: Datetime in China timezone
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    china_tz = timezone(timedelta(hours=8))
    return dt.astimezone(china_tz)


def from_china_timezone(
    dt: datetime,
) -> datetime:
    """
    Convert datetime from China timezone to UTC.

    Args:
        dt: Datetime in China timezone

    Returns:
        datetime: Datetime in UTC
    """
    if dt.tzinfo is None:
        china_tz = timezone(timedelta(hours=8))
        dt = dt.replace(tzinfo=china_tz)
    return dt.astimezone(timezone.utc)


def get_week_range(
    dt: Optional[date] = None,
) -> Tuple[date, date]:
    """
    Get the start and end dates of the week.

    Args:
        dt: Reference date (defaults to today)

    Returns:
        Tuple: (week_start, week_end) dates
    """
    if dt is None:
        dt = date.today()

    # Monday is day 0 in Python
    weekday = dt.weekday()
    week_start = dt - timedelta(days=weekday)
    week_end = week_start + timedelta(days=6)

    return week_start, week_end


def get_month_range(
    dt: Optional[date] = None,
) -> Tuple[date, date]:
    """
    Get the start and end dates of the month.

    Args:
        dt: Reference date (defaults to today)

    Returns:
        Tuple: (month_start, month_end) dates
    """
    if dt is None:
        dt = date.today()

    month_start = dt.replace(day=1)

    # Calculate last day of month
    if dt.month == 12:
        month_end = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = dt.replace(month=dt.month + 1, day=1) - timedelta(days=1)

    return month_start, month_end


def get_quarter_range(
    dt: Optional[date] = None,
) -> Tuple[date, date]:
    """
    Get the start and end dates of the quarter.

    Args:
        dt: Reference date (defaults to today)

    Returns:
        Tuple: (quarter_start, quarter_end) dates
    """
    if dt is None:
        dt = date.today()

    quarter = (dt.month - 1) // 3
    quarter_start_month = quarter * 3 + 1
    quarter_start = dt.replace(month=quarter_start_month, day=1)

    if quarter_start_month == 10:
        quarter_end = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        quarter_end = dt.replace(month=quarter_start_month + 3, day=1) - timedelta(days=1)

    return quarter_start, quarter_end


def days_between(
    start: date,
    end: date,
) -> int:
    """
    Calculate days between two dates.

    Args:
        start: Start date
        end: End date

    Returns:
        int: Number of days
    """
    return (end - start).days


def is_workday(
    d: date,
    holidays: Optional[List[date]] = None,
) -> bool:
    """
    Check if date is a workday (Mon-Fri, excluding holidays).

    Args:
        d: Date to check
        holidays: List of holiday dates

    Returns:
        bool: True if workday
    """
    # Monday=0, Friday=4
    if d.weekday() > 4:
        return False

    if holidays and d in holidays:
        return False

    return True


def get_workdays_between(
    start: date,
    end: date,
    holidays: Optional[List[date]] = None,
) -> int:
    """
    Calculate workdays between two dates.

    Args:
        start: Start date
        end: End date
        holidays: List of holiday dates

    Returns:
        int: Number of workdays
    """
    workdays = 0
    current = start

    while current <= end:
        if is_workday(current, holidays):
            workdays += 1
        current += timedelta(days=1)

    return workdays


def format_duration(
    minutes: int,
) -> str:
    """
    Format duration in minutes to human-readable string.

    Args:
        minutes: Duration in minutes

    Returns:
        str: Human-readable duration
    """
    if minutes < 60:
        return f"{minutes}分钟"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return f"{hours}小时"

    return f"{hours}小时{remaining_minutes}分钟"


def parse_chinese_date(
    text: str,
) -> Optional[date]:
    """
    Parse Chinese date formats.

    Args:
        text: Date text (supports: 2026年1月1日, 1月1日, etc.)

    Returns:
        date: Parsed date or None
    """
    import re

    # Full date: 2026年1月1日
    pattern_full = r"(\d{4})年(\d{1,2})月(\d{1,2})日"
    match = re.match(pattern_full, text)
    if match:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    # Short date: 1月1日 (uses current year)
    pattern_short = r"(\d{1,2})月(\d{1,2})日"
    match = re.match(pattern_short, text)
    if match:
        return date(date.today().year, int(match.group(1)), int(match.group(2)))

    return None


__all__ = [
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
]