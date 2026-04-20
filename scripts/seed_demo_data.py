"""
PM Digital Employee - Demo Data Seed Script
项目经理数字员工系统 - 演示数据种子脚本

生成测试用的项目、用户、任务等演示数据。
"""

import asyncio
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

# 设置路径
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.db.session import get_async_session, init_db
from app.domain.enums import (
    CostCategory,
    MilestoneStatus,
    ProjectStatus,
    RiskCategory,
    RiskLevel,
    RiskStatus,
    TaskPriority,
    TaskStatus,
    UserRole,
)
from app.domain.models.cost import ProjectCostActual, ProjectCostBudget
from app.domain.models.document import ProjectDocument
from app.domain.models.group_project_binding import GroupProjectBinding
from app.domain.models.milestone import Milestone
from app.domain.models.project import Project
from app.domain.models.risk import ProjectRisk
from app.domain.models.skill_definition import SkillDefinition
from app.domain.models.task import Task
from app.domain.models.user import User
from app.domain.models.user_project_role import UserProjectRole

logger = get_logger(__name__)


# 演示用户数据
DEMO_USERS = [
    {
        "feishu_user_id": "ou_demo_pm_001",
        "name": "张项目经理",
        "email": "zhang_pm@example.com",
        "department_name": "项目管理部",
        "position": "高级项目经理",
    },
    {
        "feishu_user_id": "ou_demo_pm_002",
        "name": "李项目经理",
        "email": "li_pm@example.com",
        "department_name": "项目管理部",
        "position": "项目经理",
    },
    {
        "feishu_user_id": "ou_demo_tech_001",
        "name": "王技术负责人",
        "email": "wang_tech@example.com",
        "department_name": "技术部",
        "position": "技术负责人",
    },
    {
        "feishu_user_id": "ou_demo_member_001",
        "name": "赵开发工程师",
        "email": "zhao_dev@example.com",
        "department_name": "技术部",
        "position": "高级开发工程师",
    },
    {
        "feishu_user_id": "ou_demo_member_002",
        "name": "刘测试工程师",
        "email": "liu_test@example.com",
        "department_name": "质量部",
        "position": "测试工程师",
    },
]

# 演示项目数据
DEMO_PROJECTS = [
    {
        "name": "核心交易系统升级项目",
        "code": "PRJ-2026-001",
        "description": "核心交易系统性能优化与功能升级项目",
        "status": ProjectStatus.IN_PROGRESS,
        "project_type": "系统升级",
        "priority": "high",
        "start_date": date(2026, 1, 1),
        "end_date": date(2026, 6, 30),
        "total_budget": Decimal("5000000.00"),
        "department_name": "技术部",
    },
    {
        "name": "移动银行APP改版项目",
        "code": "PRJ-2026-002",
        "description": "移动银行APP用户体验优化项目",
        "status": ProjectStatus.IN_PROGRESS,
        "project_type": "产品优化",
        "priority": "medium",
        "start_date": date(2026, 2, 1),
        "end_date": date(2026, 8, 31),
        "total_budget": Decimal("3000000.00"),
        "department_name": "产品部",
    },
]

# Skill定义数据（12个核心Skill）
SKILL_DEFINITIONS = [
    {
        "skill_name": "project_overview",
        "display_name": "项目总览查询",
        "description": "查询项目的整体状态信息，包括进度、里程碑、风险、成本等",
        "domain": "project_query",
        "version": "1.0.0",
    },
    {
        "skill_name": "weekly_report",
        "display_name": "项目周报生成",
        "description": "自动生成项目周报，汇总本周任务进展、下周计划、风险状态等",
        "domain": "report",
        "version": "1.0.0",
    },
    {
        "skill_name": "wbs_generation",
        "display_name": "WBS自动生成",
        "description": "根据项目信息自动生成工作分解结构",
        "domain": "planning",
        "version": "1.0.0",
    },
    {
        "skill_name": "task_update",
        "display_name": "任务进度更新",
        "description": "更新任务进度状态，包括完成百分比、状态变更、备注添加",
        "domain": "task_management",
        "version": "1.0.0",
    },
    {
        "skill_name": "risk_alert",
        "display_name": "风险识别与预警",
        "description": "识别项目风险并发出预警，分析风险等级、影响范围、应对措施",
        "domain": "risk_management",
        "version": "1.0.0",
    },
    {
        "skill_name": "cost_monitor",
        "display_name": "成本监控",
        "description": "监控项目成本执行情况，对比预算与实际支出，预警超支风险",
        "domain": "cost_management",
        "version": "1.0.0",
    },
    {
        "skill_name": "policy_qa",
        "display_name": "项目制度规范答疑",
        "description": "回答项目管理规章制度相关问题，基于知识库检索并引用来源",
        "domain": "knowledge",
        "version": "1.0.0",
    },
    {
        "skill_name": "project_query",
        "display_name": "项目情况咨询",
        "description": "回答项目具体情况相关问题",
        "domain": "project_query",
        "version": "1.0.0",
    },
    {
        "skill_name": "meeting_minutes",
        "display_name": "会议纪要生成",
        "description": "根据会议内容生成结构化会议纪要",
        "domain": "report",
        "version": "1.0.0",
    },
    {
        "skill_name": "compliance_review",
        "display_name": "预立项/立项材料合规初审",
        "description": "审核预立项/立项材料的合规性",
        "domain": "compliance",
        "version": "1.0.0",
    },
    {
        "skill_name": "document_parse",
        "display_name": "文档智能解析",
        "description": "解析用户发送的项目文档，自动提取信息并入库",
        "domain": "data_entry",
        "version": "1.0.0",
    },
    {
        "skill_name": "document_confirm",
        "display_name": "文档确认处理",
        "description": "确认文档解析结果并执行入库",
        "domain": "data_entry",
        "version": "1.0.0",
    },
]


async def seed_users(session) -> list:
    """创建演示用户."""
    logger.info("Seeding demo users...")
    users = []

    for user_data in DEMO_USERS:
        user = User(
            id=uuid.uuid4(),
            feishu_user_id=user_data["feishu_user_id"],
            name=user_data["name"],
            email=user_data.get("email"),
            department_name=user_data.get("department_name"),
            position=user_data.get("position"),
            is_active=True,
        )
        session.add(user)
        users.append(user)

    await session.flush()
    logger.info(f"Created {len(users)} demo users")
    return users


async def seed_projects(session, users: list) -> list:
    """创建演示项目."""
    logger.info("Seeding demo projects...")
    projects = []

    for i, project_data in enumerate(DEMO_PROJECTS):
        pm_user = users[i % len(users)]
        project = Project(
            id=uuid.uuid4(),
            name=project_data["name"],
            code=project_data["code"],
            description=project_data.get("description"),
            status=project_data.get("status", ProjectStatus.IN_PROGRESS),
            project_type=project_data.get("project_type"),
            priority=project_data.get("priority", "medium"),
            start_date=project_data.get("start_date"),
            end_date=project_data.get("end_date"),
            total_budget=project_data.get("total_budget"),
            department_name=project_data.get("department_name"),
            pm_id=pm_user.id,
            pm_name=pm_user.name,
            is_active=True,
        )
        session.add(project)
        projects.append(project)

    await session.flush()
    logger.info(f"Created {len(projects)} demo projects")
    return projects


async def seed_user_roles(session, users: list, projects: list) -> None:
    """创建用户项目角色关联."""
    logger.info("Seeding user project roles...")

    for project in projects:
        # 项目经理
        pm_role = UserProjectRole(
            user_id=project.pm_id,
            project_id=project.id,
            role=UserRole.PROJECT_MANAGER,
        )
        session.add(pm_role)

        # 其他成员
        for user in users[:3]:
            if user.id != project.pm_id:
                role = UserProjectRole(
                    user_id=user.id,
                    project_id=project.id,
                    role=random.choice([UserRole.MEMBER, UserRole.TECH_LEAD]),
                )
                session.add(role)

    await session.flush()
    logger.info("Created user project roles")


async def seed_tasks(session, projects: list, users: list) -> None:
    """创建演示任务."""
    logger.info("Seeding demo tasks...")

    task_templates = [
        ("需求分析与评审", "完成系统需求分析和评审", TaskStatus.COMPLETED, 100),
        ("系统架构设计", "完成系统架构设计文档", TaskStatus.COMPLETED, 100),
        ("数据库设计", "完成数据库表结构设计", TaskStatus.COMPLETED, 100),
        ("接口开发", "开发核心业务接口", TaskStatus.IN_PROGRESS, 65),
        ("前端开发", "开发前端页面", TaskStatus.IN_PROGRESS, 45),
        ("单元测试", "编写单元测试用例", TaskStatus.IN_PROGRESS, 30),
        ("集成测试", "执行系统集成测试", TaskStatus.PENDING, 0),
        ("性能测试", "执行系统性能测试", TaskStatus.PENDING, 0),
        ("UAT测试", "用户验收测试", TaskStatus.PENDING, 0),
        ("上线部署", "生产环境部署上线", TaskStatus.PENDING, 0),
    ]

    for project in projects:
        start_date = project.start_date or date.today()
        for i, (name, desc, status, progress) in enumerate(task_templates):
            task = Task(
                id=uuid.uuid4(),
                project_id=project.id,
                code=f"{project.code}-T{str(i+1).zfill(3)}",
                name=name,
                description=desc,
                status=status,
                priority=random.choice(list(TaskPriority)),
                progress=progress,
                start_date=start_date + timedelta(days=i * 7),
                end_date=start_date + timedelta(days=(i + 1) * 7),
                assignee_id=random.choice(users).feishu_user_id,
                level=1,
            )
            session.add(task)

    await session.flush()
    logger.info(f"Created demo tasks")


async def seed_milestones(session, projects: list) -> None:
    """创建演示里程碑."""
    logger.info("Seeding demo milestones...")

    for project in projects:
        start_date = project.start_date or date.today()
        milestones = [
            ("需求确认", start_date + timedelta(days=30), MilestoneStatus.ACHIEVED),
            ("设计评审", start_date + timedelta(days=60), MilestoneStatus.ACHIEVED),
            ("开发完成", start_date + timedelta(days=120), MilestoneStatus.IN_PROGRESS),
            ("测试完成", start_date + timedelta(days=150), MilestoneStatus.PLANNED),
            ("上线验收", start_date + timedelta(days=180), MilestoneStatus.PLANNED),
        ]

        for i, (name, due_date, status) in enumerate(milestones):
            milestone = Milestone(
                id=uuid.uuid4(),
                project_id=project.id,
                name=name,
                due_date=due_date,
                status=status,
                sort_order=i,
            )
            session.add(milestone)

    await session.flush()
    logger.info("Created demo milestones")


async def seed_costs(session, projects: list) -> None:
    """创建演示成本数据."""
    logger.info("Seeding demo costs...")

    for project in projects:
        # 预算
        budget_items = [
            (CostCategory.LABOR, Decimal("3000000.00")),
            (CostCategory.EQUIPMENT, Decimal("800000.00")),
            (CostCategory.SOFTWARE, Decimal("500000.00")),
            (CostCategory.OUTSOURCING, Decimal("700000.00")),
        ]

        for category, amount in budget_items:
            budget = ProjectCostBudget(
                id=uuid.uuid4(),
                project_id=project.id,
                category=category,
                amount=amount,
            )
            session.add(budget)

        # 实际支出
        actual_items = [
            (CostCategory.LABOR, Decimal("1500000.00"), date(2026, 3, 15)),
            (CostCategory.EQUIPMENT, Decimal("600000.00"), date(2026, 2, 20)),
            (CostCategory.SOFTWARE, Decimal("400000.00"), date(2026, 1, 30)),
        ]

        for category, amount, expense_date in actual_items:
            actual = ProjectCostActual(
                id=uuid.uuid4(),
                project_id=project.id,
                category=category,
                amount=amount,
                expense_date=expense_date,
            )
            session.add(actual)

    await session.flush()
    logger.info("Created demo costs")


async def seed_risks(session, projects: list) -> None:
    """创建演示风险数据."""
    logger.info("Seeding demo risks...")

    risk_templates = [
        ("人员流动风险", "核心开发人员可能离职", RiskCategory.RESOURCE, RiskLevel.MEDIUM, 3, 4),
        ("技术风险", "新技术方案存在不确定性", RiskCategory.TECHNICAL, RiskLevel.HIGH, 4, 4),
        ("进度风险", "部分任务可能延期", RiskCategory.SCHEDULE, RiskLevel.MEDIUM, 3, 3),
    ]

    for project in projects:
        for title, desc, category, level, prob, impact in risk_templates:
            risk = ProjectRisk(
                id=uuid.uuid4(),
                project_id=project.id,
                title=title,
                description=desc,
                category=category,
                level=level,
                status=RiskStatus.IDENTIFIED,
                probability=prob,
                impact=impact,
                identified_date=date.today() - timedelta(days=random.randint(10, 30)),
            )
            session.add(risk)

    await session.flush()
    logger.info("Created demo risks")


async def seed_group_bindings(session, projects: list) -> None:
    """创建飞书群绑定."""
    logger.info("Seeding group bindings...")

    for i, project in enumerate(projects):
        binding = GroupProjectBinding(
            id=uuid.uuid4(),
            chat_id=f"oc_demo_group_{i+1}",
            chat_name=f"{project.name}-项目群",
            project_id=project.id,
            is_active=True,
        )
        session.add(binding)

    await session.flush()
    logger.info("Created group bindings")


async def seed_skill_definitions(session) -> list:
    """创建Skill定义数据."""
    logger.info("Seeding skill definitions...")
    skill_defs = []

    for skill_data in SKILL_DEFINITIONS:
        # 检查是否已存在
        from sqlalchemy import select
        result = await session.execute(
            select(SkillDefinition).where(SkillDefinition.skill_name == skill_data["skill_name"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"Skill definition {skill_data['skill_name']} already exists, skipping")
            skill_defs.append(existing)
            continue

        skill_def = SkillDefinition(
            id=uuid.uuid4(),
            skill_name=skill_data["skill_name"],
            display_name=skill_data["display_name"],
            description=skill_data["description"],
            manifest=json.dumps({
                "name": skill_data["skill_name"],
                "display_name": skill_data["display_name"],
                "description": skill_data["description"],
                "version": skill_data["version"],
                "domain": skill_data["domain"],
            }),
            version=skill_data["version"],
            domain=skill_data["domain"],
            is_enabled=True,
            enabled_by_default=True,
            supports_async=False,
            supports_confirmation=False,
            timeout_seconds=120,
        )
        session.add(skill_def)
        skill_defs.append(skill_def)

    await session.flush()
    logger.info(f"Created {len(skill_defs)} skill definitions")
    return skill_defs


async def main() -> None:
    """主函数."""
    setup_logging()
    logger.info("Starting demo data seeding...")

    await init_db()

    async with get_async_session() as session:
        # 创建数据
        users = await seed_users(session)
        projects = await seed_projects(session, users)
        await seed_user_roles(session, users, projects)
        await seed_tasks(session, projects, users)
        await seed_milestones(session, projects)
        await seed_costs(session, projects)
        await seed_risks(session, projects)
        await seed_group_bindings(session, projects)
        await seed_skill_definitions(session)  # v1.3.0新增：Skill定义初始化

        await session.commit()

    logger.info("Demo data seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())