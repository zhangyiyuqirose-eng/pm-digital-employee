"""
PM Digital Employee - Knowledge Management Skills
知识管理领域Skill

包含制度问答、项目咨询等Skill。
"""

from app.skills.policy_qa_skill import PolicyQASkill
from app.skills.additional_skills import ProjectQuerySkill

__all__ = ["PolicyQASkill", "ProjectQuerySkill"]