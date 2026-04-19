"""
PM Digital Employee - Weekly Report Service
项目经理数字员工系统 - 周报业务服务

提供周报的三种录入方式、自动生成、审批流程、历史查询和导出功能。

功能：
1. 三种方式录入周报数据（飞书卡片、Excel、飞书表格）
2. 自动从Task和MeetingMinutes模块提取数据生成周报初稿
3. 周报模板自定义功能
4. 周报审批流程与飞书审批集成
5. 历史周报查询和导出
"""

import json
import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErrorCode, ProjectNotFoundError, WeeklyReportNotFoundError
from app.core.logging import get_logger
from app.domain.enums import DataSource, WeeklyReportStatus, TaskStatus, ApprovalStatus
from app.domain.models.weekly_report import WeeklyReport
from app.domain.models.task import Task
from app.domain.models.meeting_minutes import MeetingMinutes
from app.repositories.weekly_report_repository import WeeklyReportRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.services.validation_service import ValidationService
from app.services.excel_service import ExcelService
from app.services.sync_engine import SyncEngine

logger = get_logger(__name__)


class WeeklyReportService:
    """
    周报业务服务.

    封装周报相关的业务逻辑，包括三种录入方式、自动生成、审批、历史查询等。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化周报服务.

        Args:
            session: 数据库会话
        """
        self.session = session
        self._repository = WeeklyReportRepository(session)
        self._project_repository = ProjectRepository(session)
        self._task_repository = TaskRepository(session)
        self._validation_service = ValidationService()
        self._excel_service = ExcelService(session)
        self._sync_engine = SyncEngine(session)

    # ==================== 基础周报操作 ====================

    async def create_report(
        self,
        project_id: uuid.UUID,
        report_date: date,
        week_start: date,
        week_end: date,
        summary: Optional[str] = None,
        completed_tasks: Optional[List[Dict]] = None,
        in_progress_tasks: Optional[List[Dict]] = None,
        next_week_plan: Optional[str] = None,
        risks_and_issues: Optional[str] = None,
        author_id: Optional[str] = None,
        author_name: Optional[str] = None,
        data_source: DataSource = DataSource.LARK_CARD,
        user_id: Optional[str] = None,
    ) -> WeeklyReport:
        """
        创建周报.

        Args:
            project_id: 项目ID（必填）
            report_date: 周报日期（必填）
            week_start: 周开始日期（必填）
            week_end: 周结束日期（必填）
            summary: 本周工作总结
            completed_tasks: 已完成任务列表
            in_progress_tasks: 进行中任务列表
            next_week_plan: 下周计划
            risks_and_issues: 风险和问题
            author_id: 作者飞书用户ID
            author_name: 作者姓名
            data_source: 数据来源
            user_id: 创建用户ID

        Returns:
            WeeklyReport: 创建的周报

        Raises:
            ProjectNotFoundError: 项目不存在
        """
        # 验证项目存在
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id=str(project_id))

        # 生成周报编码
        code = await self._repository.generate_report_code(project_id)

        # 创建周报数据
        report_data = {
            "id": uuid.uuid4(),
            "project_id": project_id,
            "report_code": code,
            "report_date": report_date,
            "week_start": week_start,
            "week_end": week_end,
            "summary": summary,
            "completed_tasks": json.dumps(completed_tasks) if completed_tasks else None,
            "in_progress_tasks": json.dumps(in_progress_tasks) if in_progress_tasks else None,
            "next_week_plan": next_week_plan,
            "risks_and_issues": risks_and_issues,
            "status": WeeklyReportStatus.DRAFT,
            "approval_status": ApprovalStatus.PENDING.value,
            "author_id": author_id,
            "author_name": author_name,
            "data_source": data_source,
            "created_by": user_id,
        }

        report = await self._repository.create(report_data)
        logger.info(f"Weekly report created: id={report.id}, code={code}")

        return report

    async def update_report(
        self,
        report_id: uuid.UUID,
        **update_data: Any,
    ) -> WeeklyReport:
        """
        更新周报.

        Args:
            report_id: 周报ID
            **update_data: 更新数据

        Returns:
            WeeklyReport: 更新后的周报

        Raises:
            WeeklyReportNotFoundError: 周报不存在
        """
        report = await self._repository.get_by_id(report_id)
        if report is None:
            raise WeeklyReportNotFoundError(report_id=str(report_id))

        # 处理JSON字段
        if "completed_tasks" in update_data and isinstance(update_data["completed_tasks"], list):
            update_data["completed_tasks"] = json.dumps(update_data["completed_tasks"])
        if "in_progress_tasks" in update_data and isinstance(update_data["in_progress_tasks"], list):
            update_data["in_progress_tasks"] = json.dumps(update_data["in_progress_tasks"])

        # 更新版本号
        update_data["version"] = report.version + 1

        report = await self._repository.update(report_id, update_data)
        logger.info(f"Weekly report updated: id={report_id}, version={update_data['version']}")

        return report

    async def get_report(self, report_id: uuid.UUID) -> Optional[WeeklyReport]:
        """
        获取周报详情.

        Args:
            report_id: 周报ID

        Returns:
            Optional[WeeklyReport]: 周报对象或None
        """
        return await self._repository.get_by_id(report_id)

    async def delete_report(self, report_id: uuid.UUID) -> None:
        """
        删除周报.

        Args:
            report_id: 周报ID

        Raises:
            WeeklyReportNotFoundError: 周报不存在
        """
        report = await self._repository.get_by_id(report_id)
        if report is None:
            raise WeeklyReportNotFoundError(report_id=str(report_id))

        await self._repository.delete(report_id)
        logger.info(f"Weekly report deleted: id={report_id}")

    # ==================== 多源数据录入 ====================

    async def import_from_excel(
        self,
        project_id: uuid.UUID,
        file_path: str,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
    ) -> Tuple[List[WeeklyReport], List[Dict]]:
        """
        从Excel导入周报数据.

        Args:
            project_id: 项目ID
            file_path: Excel文件路径
            operator_id: 操作人ID
            operator_name: 操作人姓名

        Returns:
            Tuple[List[WeeklyReport], List[Dict]]: 导入的周报列表和错误列表
        """
        # 创建同步日志
        sync_log = await self._sync_engine.create_sync_log(
            sync_type="excel_import",
            sync_direction="import",
            module="weekly_report",
            project_id=project_id,
            operator_id=operator_id,
            operator_name=operator_name,
            excel_file_name=file_path,
        )

        try:
            # 解析Excel文件
            parsed_data = self._excel_service.parse_excel_file(file_path, "weekly_report")

            # 校验数据
            validation_result = self._validation_service.validate_data(parsed_data, "weekly_report")

            if not validation_result.is_valid:
                await self._sync_engine.update_sync_status(
                    sync_log.id,
                    status="failed",
                    error_details=validation_result.errors,
                )
                return [], validation_result.errors

            # 导入数据
            imported_reports = []
            errors = []

            for row_data in parsed_data:
                try:
                    report = await self.create_report(
                        project_id=project_id,
                        data_source=DataSource.EXCEL_IMPORT,
                        user_id=operator_id,
                        **row_data,
                    )
                    imported_reports.append(report)
                except Exception as e:
                    errors.append({
                        "row": row_data,
                        "error": str(e),
                    })

            # 更新同步日志
            await self._sync_engine.update_sync_status(
                sync_log.id,
                status="success" if not errors else "partial",
                records_total=len(parsed_data),
                records_success=len(imported_reports),
                records_failed=len(errors),
            )

            logger.info(
                f"Excel import completed: project_id={project_id}, "
                f"success={len(imported_reports)}, failed={len(errors)}"
            )

            return imported_reports, errors

        except Exception as e:
            await self._sync_engine.update_sync_status(
                sync_log.id,
                status="failed",
                error_details=[{"error": str(e)}],
            )
            logger.error(f"Excel import failed: {e}")
            raise

    async def import_from_lark_sheet(
        self,
        project_id: uuid.UUID,
        sheet_token: str,
        sheet_id: str,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
    ) -> Tuple[List[WeeklyReport], List[Dict]]:
        """
        从飞书在线表格导入周报数据.

        Args:
            project_id: 项目ID
            sheet_token: 飞书表格Token
            sheet_id: 子表格ID
            operator_id: 操作人ID
            operator_name: 操作人姓名

        Returns:
            Tuple[List[WeeklyReport], List[Dict]]: 导入的周报列表和错误列表
        """
        # TODO: 实现飞书表格同步逻辑
        # 需要调用飞书API获取表格数据，然后转换为周报数据
        logger.info(
            f"Lark sheet import initiated: project_id={project_id}, "
            f"sheet_token={sheet_token}, sheet_id={sheet_id}"
        )
        return [], []

    async def import_from_lark_card(
        self,
        project_id: uuid.UUID,
        card_data: Dict[str, Any],
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> WeeklyReport:
        """
        从飞书卡片导入周报数据.

        Args:
            project_id: 项目ID
            card_data: 飞书卡片数据
            user_id: 用户ID
            user_name: 用户姓名

        Returns:
            WeeklyReport: 创建的周报
        """
        # 从卡片数据提取周报字段
        report_date = date.today()
        week_start = report_date - timedelta(days=report_date.weekday())
        week_end = week_start + timedelta(days=6)

        report = await self.create_report(
            project_id=project_id,
            report_date=report_date,
            week_start=week_start,
            week_end=week_end,
            summary=card_data.get("summary"),
            completed_tasks=card_data.get("completed_tasks"),
            in_progress_tasks=card_data.get("in_progress_tasks"),
            next_week_plan=card_data.get("next_week_plan"),
            risks_and_issues=card_data.get("risks_and_issues"),
            author_id=user_id,
            author_name=user_name,
            data_source=DataSource.LARK_CARD,
            user_id=user_id,
        )

        logger.info(f"Lark card import completed: report_id={report.id}")
        return report

    # ==================== 自动生成周报 ====================

    async def generate_report(
        self,
        project_id: uuid.UUID,
        week_start: date,
        week_end: date,
        author_id: Optional[str] = None,
        author_name: Optional[str] = None,
    ) -> WeeklyReport:
        """
        自动生成周报初稿.

        从Task和MeetingMinutes模块提取数据，生成周报初稿。

        Args:
            project_id: 项目ID
            week_start: 周开始日期
            week_end: 周结束日期
            author_id: 作者ID
            author_name: 作者姓名

        Returns:
            WeeklyReport: 生成的周报初稿
        """
        # 获取本周已完成的任务
        completed_tasks_result = await self.session.execute(
            select(Task)
            .where(
                and_(
                    Task.project_id == project_id,
                    Task.status == TaskStatus.COMPLETED,
                    Task.updated_at >= week_start,
                    Task.updated_at <= week_end + timedelta(days=1),
                )
            )
        )
        completed_tasks = list(completed_tasks_result.scalars().all())

        # 获取本周进行中的任务
        in_progress_tasks_result = await self.session.execute(
            select(Task)
            .where(
                and_(
                    Task.project_id == project_id,
                    Task.status == TaskStatus.IN_PROGRESS,
                )
            )
        )
        in_progress_tasks = list(in_progress_tasks_result.scalars().all())

        # 获取本周的会议纪要
        meetings_result = await self.session.execute(
            select(MeetingMinutes)
            .where(
                and_(
                    MeetingMinutes.project_id == project_id,
                    MeetingMinutes.meeting_date >= week_start,
                    MeetingMinutes.meeting_date <= week_end,
                    MeetingMinutes.is_current == True,
                )
            )
        )
        meetings = list(meetings_result.scalars().all())

        # 构建周报内容
        completed_tasks_list = [
            {
                "name": task.name,
                "code": task.code,
                "assignee": task.assignee_name,
                "completed_at": str(task.updated_at.date()) if task.updated_at else None,
            }
            for task in completed_tasks
        ]

        in_progress_tasks_list = [
            {
                "name": task.name,
                "code": task.code,
                "assignee": task.assignee_name,
                "progress": task.progress,
                "end_date": str(task.end_date) if task.end_date else None,
            }
            for task in in_progress_tasks
        ]

        # 构建会议摘要
        meeting_summary = "\n".join([
            f"- {m.meeting_title}（{m.meeting_date}）"
            for m in meetings
        ])

        # 生成周报摘要
        summary = f"""本周工作总结：

已完成任务：{len(completed_tasks)}项
{chr(10).join([f'  ✓ {t.name}' for t in completed_tasks[:10]])}

进行中任务：{len(in_progress_tasks)}项
{chr(10).join([f'  ○ {t.name}（进度{t.progress}%）' for t in in_progress_tasks[:10]])}

本周会议：{len(meetings)}场
{meeting_summary}
"""

        # 创建周报
        report = await self.create_report(
            project_id=project_id,
            report_date=date.today(),
            week_start=week_start,
            week_end=week_end,
            summary=summary,
            completed_tasks=completed_tasks_list,
            in_progress_tasks=in_progress_tasks_list,
            author_id=author_id,
            author_name=author_name,
            data_source=DataSource.SYSTEM_GENERATED,
        )

        logger.info(f"Auto-generated weekly report: id={report.id}, project_id={project_id}")
        return report

    # ==================== 审批流程 ====================

    async def submit_for_approval(
        self,
        report_id: uuid.UUID,
        submitter_id: Optional[str] = None,
        submitter_name: Optional[str] = None,
    ) -> WeeklyReport:
        """
        提交周报审批.

        Args:
            report_id: 周报ID
            submitter_id: 提交人ID
            submitter_name: 提交人姓名

        Returns:
            WeeklyReport: 更新后的周报

        Raises:
            WeeklyReportNotFoundError: 周报不存在
        """
        report = await self._repository.get_by_id(report_id)
        if report is None:
            raise WeeklyReportNotFoundError(report_id=str(report_id))

        # 更新状态为已提交
        report = await self._repository.update(
            report_id,
            {
                "status": WeeklyReportStatus.SUBMITTED,
                "approval_status": ApprovalStatus.PENDING.value,
            },
        )

        # TODO: 调用飞书审批API创建审批流程
        logger.info(f"Weekly report submitted for approval: id={report_id}")

        return report

    async def approve_report(
        self,
        report_id: uuid.UUID,
        approver_id: str,
        approver_name: str,
        approval_comment: Optional[str] = None,
    ) -> WeeklyReport:
        """
        批准周报.

        Args:
            report_id: 周报ID
            approver_id: 审批人ID
            approver_name: 审批人姓名
            approval_comment: 审批意见

        Returns:
            WeeklyReport: 更新后的周报

        Raises:
            WeeklyReportNotFoundError: 周报不存在
        """
        report = await self._repository.get_by_id(report_id)
        if report is None:
            raise WeeklyReportNotFoundError(report_id=str(report_id))

        # 更新状态为已批准
        report = await self._repository.update(
            report_id,
            {
                "status": WeeklyReportStatus.APPROVED,
                "approval_status": ApprovalStatus.APPROVED.value,
                "approver_id": approver_id,
                "approver_name": approver_name,
                "approved_at": datetime.now(timezone.utc),
            },
        )

        logger.info(f"Weekly report approved: id={report_id}, approver={approver_name}")

        return report

    async def reject_report(
        self,
        report_id: uuid.UUID,
        approver_id: str,
        approver_name: str,
        reject_reason: str,
    ) -> WeeklyReport:
        """
        拒绝周报.

        Args:
            report_id: 周报ID
            approver_id: 审批人ID
            approver_name: 审批人姓名
            reject_reason: 拒绝原因

        Returns:
            WeeklyReport: 更新后的周报

        Raises:
            WeeklyReportNotFoundError: 周报不存在
        """
        report = await self._repository.get_by_id(report_id)
        if report is None:
            raise WeeklyReportNotFoundError(report_id=str(report_id))

        # 更新状态为草稿，审批状态为拒绝
        report = await self._repository.update(
            report_id,
            {
                "status": WeeklyReportStatus.DRAFT,
                "approval_status": ApprovalStatus.REJECTED.value,
                "approver_id": approver_id,
                "approver_name": approver_name,
                "approved_at": datetime.now(timezone.utc),
            },
        )

        logger.info(f"Weekly report rejected: id={report_id}, reason={reject_reason}")

        return report

    # ==================== 历史查询和导出 ====================

    async def get_history(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[WeeklyReportStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[WeeklyReport]:
        """
        获取历史周报列表.

        Args:
            project_id: 项目ID
            skip: 跳过数量
            limit: 返回数量限制
            status: 状态筛选
            start_date: 开始日期筛选
            end_date: 结束日期筛选

        Returns:
            List[WeeklyReport]: 周报列表
        """
        if status:
            return await self._repository.get_by_status(project_id, status, skip, limit)
        elif start_date and end_date:
            return await self._repository.get_by_date_range(project_id, start_date, end_date)
        else:
            return await self._repository.get_current_reports(project_id, skip, limit)

    async def export_to_excel(
        self,
        project_id: uuid.UUID,
        report_ids: Optional[List[uuid.UUID]] = None,
    ) -> BytesIO:
        """
        导出周报为Excel.

        Args:
            project_id: 项目ID
            report_ids: 要导出的周报ID列表（可选，不传则导出全部）

        Returns:
            BytesIO: Excel文件流
        """
        # 获取要导出的周报
        if report_ids:
            reports = [await self._repository.get_by_id(id) for id in report_ids]
            reports = [r for r in reports if r is not None]
        else:
            reports = await self._repository.get_current_reports(project_id)

        # 构建导出数据
        export_data = []
        for report in reports:
            export_data.append({
                "周报编码": report.report_code,
                "周报日期": str(report.report_date),
                "周开始日期": str(report.week_start),
                "周结束日期": str(report.week_end),
                "作者": report.author_name,
                "状态": report.status,
                "本周总结": report.summary,
                "已完成任务": report.completed_tasks,
                "进行中任务": report.in_progress_tasks,
                "下周计划": report.next_week_plan,
                "风险和问题": report.risks_and_issues,
                "审批状态": report.approval_status,
                "审批人": report.approver_name,
                "审批时间": str(report.approved_at) if report.approved_at else "",
            })

        # 生成Excel
        buffer = self._excel_service.export_data_to_excel(export_data, "weekly_report")

        logger.info(f"Exported weekly reports: count={len(reports)}, project_id={project_id}")
        return buffer

    async def count_reports(
        self,
        project_id: uuid.UUID,
    ) -> int:
        """
        统计项目周报数量.

        Args:
            project_id: 项目ID

        Returns:
            int: 周报数量
        """
        return await self._repository.count_by_project(project_id)