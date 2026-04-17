"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-04-17

创建PM数字员工项目初始数据库结构。

包含以下表：
- users: 用户表
- projects: 项目表
- tasks: 任务表
- milestones: 里程碑表
- risks: 风险表
- costs: 成本表（预算/实际）
- documents: 文档表
- knowledge_documents: 知识库表
- conversations: 会话表
- skill_definitions: Skill定义表
- user_project_roles: 用户项目角色表
- group_project_bindings: 群组项目绑定表
- audit_logs: 审计日志表
- event_records: 事件记录表
- llm_usage_logs: LLM使用日志表
- approvals: 审批流程表
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    升级到初始schema.
    
    注意：此迁移文件为模板，实际迁移应使用 autogenerate：
    alembic revision --autogenerate -m "initial schema"
    """
    # 此文件为模板，实际迁移由 autogenerate 生成
    # 执行命令: alembic revision --autogenerate -m "initial schema"
    pass


def downgrade() -> None:
    """
    回滚到空数据库.
    """
    # 此文件为模板，实际回滚由 autogenerate 生成
    pass