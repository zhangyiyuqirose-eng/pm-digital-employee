"""
PM Digital Employee - Communication Management Skills
沟通管理领域Skill

包含周报生成、会议纪要等Skill。
"""

from app.skills.weekly_report_skill import WeeklyReportSkill
from app.skills.additional_skills import MeetingMinutesSkill

__all__ = ["WeeklyReportSkill", "MeetingMinutesSkill"]