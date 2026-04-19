"""
PM Digital Employee - Lark Sheet Sync Service
项目经理数字员工系统 - 飞书在线表格同步服务

v1.2.0新增：实现飞书在线表格与系统数据的双向同步功能。

主要功能：
1. sync_from_sheet(binding_id) - 从飞书表格同步到系统
2. sync_to_sheet(binding_id) - 从系统同步到飞书表格
3. handle_sheet_webhook(event_data) - 处理飞书表格修改事件
4. field_mapping(data, mappings) - 字段映射转换
"""

import json
import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.exceptions import ProjectNotFoundError
from app.domain.models.lark_sheet_binding import LarkSheetBinding
from app.domain.models.project import Project
from app.services.sync_engine import SyncEngine, SyncStatus
from app.services.validation_service import ValidationService
from app.integrations.lark.client import LarkClient

logger = get_logger(__name__)


class LarkSheetSyncService:
    """
    飞书在线表格同步服务.

    实现飞书表格与系统数据的双向同步，支持字段映射、数据校验、冲突检测。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化飞书表格同步服务.

        Args:
            session: 数据库会话
        """
        self.session = session
        self.sync_engine = SyncEngine(session)
        self.validation_service = ValidationService()
        self._lark_client: Optional[LarkClient] = None

    def _get_lark_client(self) -> LarkClient:
        """
        获取飞书客户端.

        Returns:
            LarkClient: 飞书API客户端
        """
        if self._lark_client is None:
            from app.integrations.lark.service import get_lark_service
            lark_service = get_lark_service()
            self._lark_client = lark_service.client
        return self._lark_client

    # ==================== 从飞书表格同步到系统 ====================

    async def sync_from_sheet(
        self,
        binding_id: uuid.UUID,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        从飞书表格同步数据到系统.

        Args:
            binding_id: 绑定配置ID
            operator_id: 操作人ID
            operator_name: 操作人姓名

        Returns:
            Dict: 同步结果统计
        """
        # 获取绑定配置
        binding = await self.sync_engine.get_lark_sheet_binding(binding_id)
        if not binding:
            raise ValueError(f"Binding not found: {binding_id}")

        if not binding.sync_enabled:
            logger.warning(f"Binding {binding_id} is disabled")
            return {"status": "disabled", "message": "绑定已禁用"}

        # 创建同步日志
        sync_log = await self.sync_engine.create_sync_log(
            sync_type="lark_sheet",
            sync_direction="import",
            module=binding.module,
            project_id=binding.project_id,
            operator_id=operator_id,
            operator_name=operator_name,
            lark_sheet_token=binding.lark_sheet_token,
        )

        try:
            # 更新状态为运行中
            await self.sync_engine.update_sync_status(
                sync_log.id, SyncStatus.RUNNING
            )

            # 从飞书表格读取数据
            sheet_data = await self._read_sheet_data(binding)

            # 字段映射转换
            mapped_data = self._apply_field_mappings(sheet_data, binding)

            # 数据校验
            validation_results = self.validation_service.validate_batch(
                mapped_data, binding.module
            )

            # 统计结果
            valid_data = []
            errors = []

            for idx, result in enumerate(validation_results):
                if result.is_valid:
                    valid_data.append(result.validated_data)
                else:
                    errors.append({
                        "row_index": idx + 1,
                        "errors": result.errors,
                    })

            # 导入数据到系统
            import_result = await self._import_data_to_system(
                valid_data,
                binding.module,
                binding.project_id,
                binding,
            )

            # 更新同步日志
            status = SyncStatus.SUCCESS if len(errors) == 0 else SyncStatus.PARTIAL
            await self.sync_engine.update_sync_status(
                sync_log.id,
                status,
                records_total=len(sheet_data),
                records_success=import_result.get("imported", 0),
                records_failed=len(errors),
                records_skipped=import_result.get("skipped", 0),
                error_details=errors[:100],
            )

            # 更新绑定状态
            await self.sync_engine.update_binding_sync_status(
                binding_id, status
            )

            return {
                "status": status,
                "total": len(sheet_data),
                "imported": import_result.get("imported", 0),
                "updated": import_result.get("updated", 0),
                "skipped": import_result.get("skipped", 0),
                "failed": len(errors),
                "errors": errors[:10],  # 只返回前10个错误
            }

        except Exception as e:
            logger.error(f"Sync from sheet failed: {e}", binding_id=str(binding_id))

            # 更新同步日志为失败
            await self.sync_engine.update_sync_status(
                sync_log.id,
                SyncStatus.FAILED,
                error_details=[{"error": str(e)}],
            )

            # 更新绑定状态
            await self.sync_engine.update_binding_sync_status(
                binding_id, SyncStatus.FAILED
            )

            raise

    async def _read_sheet_data(
        self,
        binding: LarkSheetBinding,
    ) -> List[Dict[str, Any]]:
        """
        从飞书表格读取数据.

        Args:
            binding: 绑定配置

        Returns:
            List[Dict]: 表格数据列表
        """
        client = self._get_lark_client()

        try:
            # 构造读取范围
            sheet_range = binding.data_range_start or "A1"
            if binding.data_range_end:
                sheet_range = f"{sheet_range}:{binding.data_range_end}"

            # 调用飞书API读取表格数据
            # 注意：这里需要根据实际的飞书表格API进行实现
            # 预留接口，实际实现可能需要调整

            response = await client.sheets.read_cells(
                spreadsheet_token=binding.lark_sheet_token,
                sheet_id=binding.lark_sheet_id,
                range=sheet_range,
            )

            if not response or not response.get("valueRanges"):
                logger.warning(f"No data found in sheet: {binding.lark_sheet_token}")
                return []

            # 解析表格数据
            values = response.get("valueRanges", [{}])[0].get("values", [])
            if len(values) < 2:  # 至少需要标题行和一行数据
                return []

            # 第一行作为标题（字段名）
            headers = values[0]
            data_rows = values[1:]

            # 转换为字典列表
            data_list = []
            for row in data_rows:
                row_data = {}
                for col_idx, header in enumerate(headers):
                    if col_idx < len(row):
                        row_data[header] = row[col_idx]
                    else:
                        row_data[header] = None
                # 添加飞书表格行号
                row_data["_lark_sheet_row"] = data_rows.index(row) + 2  # 从第2行开始
                data_list.append(row_data)

            logger.info(
                f"Read {len(data_list)} rows from sheet: "
                f"token={binding.lark_sheet_token}, sheet_id={binding.lark_sheet_id}"
            )

            return data_list

        except Exception as e:
            logger.error(f"Failed to read sheet data: {e}")
            raise

    def _apply_field_mappings(
        self,
        sheet_data: List[Dict[str, Any]],
        binding: LarkSheetBinding,
    ) -> List[Dict[str, Any]]:
        """
        应用字段映射转换.

        将飞书表格的列标题映射到系统的字段名。

        Args:
            sheet_data: 飞书表格原始数据
            binding: 绑定配置

        Returns:
            List[Dict]: 映射后的数据列表
        """
        try:
            mappings = json.loads(binding.field_mappings)
        except json.JSONDecodeError:
            logger.warning(f"Invalid field mappings in binding: {binding.id}")
            return sheet_data

        mapped_data = []
        for row_data in sheet_data:
            mapped_row = self.field_mapping(row_data, mappings)
            mapped_row["_lark_sheet_row"] = row_data.get("_lark_sheet_row")
            mapped_data.append(mapped_row)

        return mapped_data

    def field_mapping(
        self,
        data: Dict[str, Any],
        mappings: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        字段映射转换.

        根据映射配置将数据字段名进行转换。

        Args:
            data: 原始数据
            mappings: 映射配置（飞书列标题 -> 系统字段名）

        Returns:
            Dict: 映射后的数据
        """
        mapped_data = {}

        for sheet_column, system_field in mappings.items():
            value = data.get(sheet_column)

            # 类型转换
            converted_value = self._convert_field_value(value, system_field)

            mapped_data[system_field] = converted_value

        # 保留飞书表格行号
        if "_lark_sheet_row" in data:
            mapped_data["_lark_sheet_row"] = data["_lark_sheet_row"]

        return mapped_data

    def _convert_field_value(
        self,
        value: Any,
        field_name: str,
    ) -> Any:
        """
        字段值类型转换.

        根据字段名推断类型并进行转换。

        Args:
            value: 原始值
            field_name: 字段名

        Returns:
            Any: 转换后的值
        """
        if value is None or value == "":
            return None

        # 日期字段
        if field_name in ["start_date", "end_date", "actual_start_date",
                          "actual_end_date", "due_date", "planned_date"]:
            if isinstance(value, str):
                try:
                    # 尝试多种日期格式
                    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"]:
                        try:
                            return datetime.strptime(value, fmt).date()
                        except ValueError:
                            continue
                except Exception:
                    return value

        # 数值字段
        if field_name in ["total_budget", "amount", "progress", "priority"]:
            if isinstance(value, str):
                try:
                    # 去除可能的单位或符号
                    clean_value = value.replace("元", "").replace("%", "").strip()
                    if "." in clean_value:
                        return Decimal(clean_value)
                    return int(clean_value)
                except (ValueError, TypeError):
                    return value

        # 状态字段映射
        if field_name == "status":
            # 飞书表格可能使用中文状态
            status_mapping = {
                "草稿": "draft",
                "筹备中": "pre_initiation",
                "已立项": "initiated",
                "进行中": "in_progress",
                "已完成": "completed",
                "已归档": "archived",
                "未开始": "未开始",
                "进行中": "进行中",
                "已完成": "已完成",
                "已延期": "已延期",
            }
            if isinstance(value, str):
                return status_mapping.get(value, value)

        return value

    async def _import_data_to_system(
        self,
        data_list: List[Dict[str, Any]],
        module: str,
        project_id: uuid.UUID,
        binding: LarkSheetBinding,
    ) -> Dict[str, int]:
        """
        导入数据到系统.

        Args:
            data_list: 数据列表
            module: 模块名称
            project_id: 项目ID
            binding: 绑定配置

        Returns:
            Dict: 导入统计 {imported, updated, skipped}
        """
        result = {"imported": 0, "updated": 0, "skipped": 0}

        if module == "project":
            # 项目数据导入
            for data in data_list:
                # 检查是否存在（根据code或external_id）
                existing = await self._find_existing_project(data)

                if existing:
                    # 更新现有项目
                    data_before = await self._get_project_data(existing.id)
                    await self._update_project(existing, data)
                    result["updated"] += 1

                    # 记录版本
                    await self.sync_engine.record_version(
                        entity_type="project",
                        entity_id=existing.id,
                        operation="update",
                        data_before=data_before,
                        data_after=data,
                        data_source="lark_sheet_sync",
                        lark_sheet_token=binding.lark_sheet_token,
                        lark_sheet_row=data.get("_lark_sheet_row"),
                    )
                else:
                    # 创建新项目
                    new_project = await self._create_project(data, project_id)
                    result["imported"] += 1

                    # 记录版本
                    await self.sync_engine.record_version(
                        entity_type="project",
                        entity_id=new_project.id,
                        operation="create",
                        data_after=data,
                        data_source="lark_sheet_sync",
                        lark_sheet_token=binding.lark_sheet_token,
                        lark_sheet_row=data.get("_lark_sheet_row"),
                    )

        elif module == "task":
            # 任务数据导入
            for data in data_list:
                data["project_id"] = project_id
                existing = await self._find_existing_task(data, project_id)

                if existing:
                    await self._update_task(existing, data)
                    result["updated"] += 1
                else:
                    await self._create_task(data, project_id)
                    result["imported"] += 1

        elif module == "milestone":
            # 里程碑数据导入
            for data in data_list:
                data["project_id"] = project_id
                existing = await self._find_existing_milestone(data, project_id)

                if existing:
                    await self._update_milestone(existing, data)
                    result["updated"] += 1
                else:
                    await self._create_milestone(data, project_id)
                    result["imported"] += 1

        elif module == "risk":
            # 风险数据导入
            for data in data_list:
                data["project_id"] = project_id
                existing = await self._find_existing_risk(data, project_id)

                if existing:
                    await self._update_risk(existing, data)
                    result["updated"] += 1
                else:
                    await self._create_risk(data, project_id)
                    result["imported"] += 1

        elif module == "cost":
            # 成本数据导入
            for data in data_list:
                data["project_id"] = project_id
                await self._create_cost(data, project_id)
                result["imported"] += 1

        await self.session.flush()
        return result

    async def _find_existing_project(
        self,
        data: Dict[str, Any],
    ) -> Optional[Project]:
        """
        查找现有项目.

        Args:
            data: 项目数据

        Returns:
            Optional[Project]: 现有项目或None
        """
        # 根据code查找
        code = data.get("code")
        if code:
            result = await self.session.execute(
                select(Project).where(Project.code == code)
            )
            return result.scalar_one_or_none()

        # 根据external_id查找
        external_id = data.get("external_id")
        if external_id:
            result = await self.session.execute(
                select(Project).where(Project.external_id == external_id)
            )
            return result.scalar_one_or_none()

        return None

    async def _get_project_data(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取项目数据.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 项目数据字典
        """
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if project:
            return {
                "id": str(project.id),
                "name": project.name,
                "code": project.code,
                "status": project.status,
                "start_date": project.start_date,
                "end_date": project.end_date,
                "total_budget": project.total_budget,
            }

        return {}

    async def _create_project(
        self,
        data: Dict[str, Any],
        project_id: uuid.UUID,
    ) -> Project:
        """创建项目."""
        from app.services.project_service import ProjectService
        service = ProjectService(self.session)
        return await service.create_project(
            name=data.get("name"),
            code=data.get("code"),
            description=data.get("description"),
            project_type=data.get("project_type", "研发项目"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            total_budget=data.get("total_budget"),
            pm_id=data.get("pm_id"),
            department_id=data.get("department_id"),
        )

    async def _update_project(
        self,
        project: Project,
        data: Dict[str, Any],
    ) -> None:
        """更新项目."""
        for key, value in data.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)
        project.last_sync_at = datetime.now(timezone.utc)
        project.data_source = "lark_sheet_sync"
        project.sync_version += 1

    async def _find_existing_task(self, data: Dict, project_id: uuid.UUID):
        """查找现有任务."""
        from app.domain.models.task import Task
        result = await self.session.execute(
            select(Task).where(
                and_(
                    Task.project_id == project_id,
                    Task.name == data.get("name"),
                )
            )
        )
        return result.scalar_one_or_none()

    async def _create_task(self, data: Dict, project_id: uuid.UUID):
        """创建任务."""
        from app.services.task_service import TaskService
        service = TaskService(self.session)
        return await service.create_task(
            project_id=project_id,
            name=data.get("name"),
            description=data.get("description"),
            assignee_id=data.get("assignee_id"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            priority=data.get("priority"),
            status=data.get("status", "未开始"),
        )

    async def _update_task(self, task, data: Dict):
        """更新任务."""
        for key, value in data.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)

    async def _find_existing_milestone(self, data: Dict, project_id: uuid.UUID):
        """查找现有里程碑."""
        from app.domain.models.milestone import Milestone
        result = await self.session.execute(
            select(Milestone).where(
                and_(
                    Milestone.project_id == project_id,
                    Milestone.name == data.get("name"),
                )
            )
        )
        return result.scalar_one_or_none()

    async def _create_milestone(self, data: Dict, project_id: uuid.UUID):
        """创建里程碑."""
        from app.services.milestone_service import MilestoneService
        service = MilestoneService(self.session)
        return await service.create_milestone(
            project_id=project_id,
            name=data.get("name"),
            due_date=data.get("due_date"),
            description=data.get("description"),
            status=data.get("status", "未完成"),
        )

    async def _update_milestone(self, milestone, data: Dict):
        """更新里程碑."""
        for key, value in data.items():
            if hasattr(milestone, key) and value is not None:
                setattr(milestone, key, value)

    async def _find_existing_risk(self, data: Dict, project_id: uuid.UUID):
        """查找现有风险."""
        from app.domain.models.risk import ProjectRisk
        result = await self.session.execute(
            select(ProjectRisk).where(
                and_(
                    ProjectRisk.project_id == project_id,
                    ProjectRisk.title == data.get("title") or data.get("name"),
                )
            )
        )
        return result.scalar_one_or_none()

    async def _create_risk(self, data: Dict, project_id: uuid.UUID):
        """创建风险."""
        from app.services.risk_service import RiskService
        service = RiskService(self.session)
        return await service.create_risk(
            project_id=project_id,
            title=data.get("title") or data.get("name"),
            description=data.get("description"),
            level=data.get("level", "中"),
            category=data.get("category", "schedule"),
            mitigation_plan=data.get("mitigation_plan"),
            owner_id=data.get("owner_id"),
        )

    async def _update_risk(self, risk, data: Dict):
        """更新风险."""
        for key, value in data.items():
            if hasattr(risk, key) and value is not None:
                setattr(risk, key, value)

    async def _create_cost(self, data: Dict, project_id: uuid.UUID):
        """创建成本."""
        from app.services.cost_service import CostService
        service = CostService(self.session)
        cost_type = data.get("cost_type", "budget")
        if cost_type == "budget":
            return await service.create_budget(
                project_id=project_id,
                category=data.get("category"),
                amount=data.get("amount"),
                description=data.get("description"),
            )
        else:
            return await service.create_actual(
                project_id=project_id,
                category=data.get("category"),
                amount=data.get("amount"),
                expense_date=data.get("expense_date"),
                description=data.get("description"),
            )

    # ==================== 从系统同步到飞书表格 ====================

    async def sync_to_sheet(
        self,
        binding_id: uuid.UUID,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        从系统同步数据到飞书表格.

        Args:
            binding_id: 绑定配置ID
            operator_id: 操作人ID
            operator_name: 操作人姓名

        Returns:
            Dict: 同步结果统计
        """
        # 获取绑定配置
        binding = await self.sync_engine.get_lark_sheet_binding(binding_id)
        if not binding:
            raise ValueError(f"Binding not found: {binding_id}")

        if not binding.sync_enabled:
            logger.warning(f"Binding {binding_id} is disabled")
            return {"status": "disabled", "message": "绑定已禁用"}

        # 创建同步日志
        sync_log = await self.sync_engine.create_sync_log(
            sync_type="lark_sheet",
            sync_direction="export",
            module=binding.module,
            project_id=binding.project_id,
            operator_id=operator_id,
            operator_name=operator_name,
            lark_sheet_token=binding.lark_sheet_token,
        )

        try:
            # 更新状态为运行中
            await self.sync_engine.update_sync_status(
                sync_log.id, SyncStatus.RUNNING
            )

            # 从系统读取数据
            system_data = await self._read_system_data(binding)

            # 应用反向字段映射（系统字段 -> 飞书列标题）
            sheet_formatted_data = self._apply_reverse_field_mappings(
                system_data, binding
            )

            # 写入飞书表格
            write_result = await self._write_sheet_data(binding, sheet_formatted_data)

            # 更新同步日志
            await self.sync_engine.update_sync_status(
                sync_log.id,
                SyncStatus.SUCCESS,
                records_total=len(system_data),
                records_success=len(system_data),
            )

            # 更新绑定状态
            await self.sync_engine.update_binding_sync_status(
                binding_id, SyncStatus.SUCCESS
            )

            return {
                "status": SyncStatus.SUCCESS,
                "total": len(system_data),
                "written": write_result.get("written", len(system_data)),
            }

        except Exception as e:
            logger.error(f"Sync to sheet failed: {e}", binding_id=str(binding_id))

            # 更新同步日志为失败
            await self.sync_engine.update_sync_status(
                sync_log.id,
                SyncStatus.FAILED,
                error_details=[{"error": str(e)}],
            )

            # 更新绑定状态
            await self.sync_engine.update_binding_sync_status(
                binding_id, SyncStatus.FAILED
            )

            raise

    async def _read_system_data(
        self,
        binding: LarkSheetBinding,
    ) -> List[Dict[str, Any]]:
        """
        从系统读取数据.

        Args:
            binding: 绑定配置

        Returns:
            List[Dict]: 系统数据列表
        """
        module = binding.module
        project_id = binding.project_id

        if module == "project":
            # 查询项目数据
            result = await self.session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            if project:
                return [{
                    "id": str(project.id),
                    "name": project.name,
                    "code": project.code,
                    "status": project.status,
                    "start_date": str(project.start_date) if project.start_date else None,
                    "end_date": str(project.end_date) if project.end_date else None,
                    "total_budget": float(project.total_budget) if project.total_budget else None,
                    "pm_name": project.pm_name,
                    "department_name": project.department_name,
                }]
            return []

        elif module == "task":
            from app.domain.models.task import Task
            result = await self.session.execute(
                select(Task).where(Task.project_id == project_id)
            )
            tasks = result.scalars().all()
            return [{
                "id": str(t.id),
                "name": t.name,
                "status": t.status,
                "progress": t.progress,
                "start_date": str(t.start_date) if t.start_date else None,
                "end_date": str(t.end_date) if t.end_date else None,
                "assignee_name": t.assignee_name,
            } for t in tasks]

        elif module == "milestone":
            from app.domain.models.milestone import Milestone
            result = await self.session.execute(
                select(Milestone).where(Milestone.project_id == project_id)
            )
            milestones = result.scalars().all()
            return [{
                "id": str(m.id),
                "name": m.name,
                "status": m.status,
                "due_date": str(m.due_date) if m.due_date else None,
            } for m in milestones]

        elif module == "risk":
            from app.domain.models.risk import ProjectRisk
            result = await self.session.execute(
                select(ProjectRisk).where(ProjectRisk.project_id == project_id)
            )
            risks = result.scalars().all()
            return [{
                "id": str(r.id),
                "title": r.title,
                "level": r.level,
                "status": r.status,
            } for r in risks]

        elif module == "cost":
            from app.domain.models.cost import ProjectCostBudget, ProjectCostActual
            budgets_result = await self.session.execute(
                select(ProjectCostBudget).where(ProjectCostBudget.project_id == project_id)
            )
            budgets = budgets_result.scalars().all()
            actuals_result = await self.session.execute(
                select(ProjectCostActual).where(ProjectCostActual.project_id == project_id)
            )
            actuals = actuals_result.scalars().all()

            data = []
            for b in budgets:
                data.append({
                    "id": str(b.id),
                    "category": b.category,
                    "amount": float(b.amount) if b.amount else None,
                    "cost_type": "budget",
                })
            for a in actuals:
                data.append({
                    "id": str(a.id),
                    "category": a.category,
                    "amount": float(a.amount) if a.amount else None,
                    "expense_date": str(a.expense_date) if a.expense_date else None,
                    "cost_type": "actual",
                })
            return data

        return []

    def _apply_reverse_field_mappings(
        self,
        system_data: List[Dict[str, Any]],
        binding: LarkSheetBinding,
    ) -> List[Dict[str, Any]]:
        """
        应用反向字段映射.

        将系统字段名转换为飞书表格列标题。

        Args:
            system_data: 系统数据
            binding: 绑定配置

        Returns:
            List[Dict]: 映射后的数据（飞书格式）
        """
        try:
            mappings = json.loads(binding.field_mappings)
            # 反转映射关系：系统字段 -> 飞书列标题
            reverse_mappings = {v: k for k, v in mappings.items()}
        except json.JSONDecodeError:
            logger.warning(f"Invalid field mappings in binding: {binding.id}")
            return system_data

        mapped_data = []
        for row in system_data:
            mapped_row = {}
            for system_field, value in row.items():
                sheet_column = reverse_mappings.get(system_field, system_field)
                mapped_row[sheet_column] = self._format_sheet_value(value, sheet_column)
            mapped_data.append(mapped_row)

        return mapped_data

    def _format_sheet_value(
        self,
        value: Any,
        column_name: str,
    ) -> Any:
        """
        格式化飞书表格值.

        Args:
            value: 原始值
            column_name: 列名

        Returns:
            Any: 格式化后的值
        """
        if value is None:
            return ""

        if isinstance(value, (date, datetime)):
            return value.strftime("%Y-%m-%d")

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, uuid.UUID):
            return str(value)

        return value

    async def _write_sheet_data(
        self,
        binding: LarkSheetBinding,
        data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        写入数据到飞书表格.

        Args:
            binding: 绑定配置
            data: 要写入的数据

        Returns:
            Dict: 写入结果
        """
        client = self._get_lark_client()

        if not data:
            return {"written": 0}

        try:
            # 获取映射的列标题顺序
            try:
                mappings = json.loads(binding.field_mappings)
                columns = list(mappings.keys())  # 飞书列顺序
            except json.JSONDecodeError:
                columns = list(data[0].keys())

            # 构造写入数据（二维数组）
            values = [columns]  # 第一行是标题
            for row_data in data:
                row_values = []
                for col in columns:
                    row_values.append(row_data.get(col, ""))
                values.append(row_values)

            # 构造写入范围
            sheet_range = binding.data_range_start or "A1"
            if binding.data_range_end:
                sheet_range = f"{sheet_range}:{binding.data_range_end}"

            # 调用飞书API写入
            # 注意：这里需要根据实际的飞书表格API进行实现
            await client.sheets.write_cells(
                spreadsheet_token=binding.lark_sheet_token,
                sheet_id=binding.lark_sheet_id,
                range=sheet_range,
                values=values,
            )

            logger.info(
                f"Written {len(data)} rows to sheet: "
                f"token={binding.lark_sheet_token}, sheet_id={binding.lark_sheet_id}"
            )

            return {"written": len(data)}

        except Exception as e:
            logger.error(f"Failed to write sheet data: {e}")
            raise

    # ==================== 飞书表格Webhook处理 ====================

    async def handle_sheet_webhook(
        self,
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        处理飞书表格修改事件.

        当飞书表格数据发生变化时，触发同步流程。

        Args:
            event_data: 飞书Webhook事件数据

        Returns:
            Dict: 处理结果
        """
        event_type = event_data.get("type", "")
        spreadsheet_token = event_data.get("spreadsheet_token", "")
        sheet_id = event_data.get("sheet_id", "")

        logger.info(
            f"Handling sheet webhook: type={event_type}, "
            f"token={spreadsheet_token}, sheet_id={sheet_id}"
        )

        # 查找对应的绑定配置
        result = await self.session.execute(
            select(LarkSheetBinding).where(
                and_(
                    LarkSheetBinding.lark_sheet_token == spreadsheet_token,
                    LarkSheetBinding.lark_sheet_id == sheet_id,
                    LarkSheetBinding.sync_enabled == True,
                    LarkSheetBinding.sync_mode.in_(["bidirectional", "from_sheet"]),
                )
            )
        )
        bindings = result.scalars().all()

        if not bindings:
            logger.debug(f"No active bindings found for webhook event")
            return {"status": "ignored", "message": "无活跃绑定配置"}

        # 触发同步
        sync_results = []
        for binding in bindings:
            try:
                result = await self.sync_from_sheet(binding.id)
                sync_results.append({
                    "binding_id": str(binding.id),
                    "module": binding.module,
                    "result": result,
                })
            except Exception as e:
                logger.error(
                    f"Webhook sync failed for binding {binding.id}: {e}"
                )
                sync_results.append({
                    "binding_id": str(binding.id),
                    "module": binding.module,
                    "error": str(e),
                })

        return {
            "status": "processed",
            "sync_count": len(bindings),
            "results": sync_results,
        }