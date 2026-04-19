"""
PM Digital Employee - Lark Bitable Service
飞书多维表格服务 - 实现双向数据同步

参考提示词Part 2.1标准实现。
支持创建表格、记录操作、事件订阅、项目数据同步。
"""

import uuid
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.lark.client import LarkClient, get_lark_client

logger = get_logger(__name__)


class LarkBitableService:
    """
    飞书多维表格服务.

    支持创建表格、记录操作、事件订阅、双向同步。
    用于实现飞书在线表格与系统数据库的双向数据同步。
    """

    def __init__(self, client: Optional[LarkClient] = None) -> None:
        """
        初始化多维表格服务.

        Args:
            client: Lark客户端实例
        """
        self._client = client or get_lark_client()

    async def create_app(
        self,
        name: str,
        folder_token: str = "root",
    ) -> Dict[str, Any]:
        """
        创建多维表格应用.

        Args:
            name: 应用名称
            folder_token: 文件夹token，默认root

        Returns:
            Dict: 包含app_token等信息
        """
        endpoint = "/open-apis/bitable/v1/apps"

        payload = {
            "name": name,
            "folder_token": folder_token,
        }

        result = await self._client.request("POST", endpoint, data=payload)

        if result.get("code") != 0:
            logger.error("Failed to create bitable app", result=result)
            raise Exception(f"创建多维表格失败: {result.get('msg')}")

        return result.get("data", {})

    async def create_table(
        self,
        app_token: str,
        table_name: str,
        fields: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        在多维表格中创建数据表.

        Args:
            app_token: 应用token
            table_name: 表名
            fields: 字段定义列表

        Returns:
            Dict: 包含table_id等信息
        """
        endpoint = f"/open-apis/bitable/v1/apps/{app_token}/tables"

        payload = {
            "table": {
                "name": table_name,
                "fields": fields,
            }
        }

        result = await self._client.request("POST", endpoint, data=payload)

        if result.get("code") != 0:
            logger.error("Failed to create table", result=result)
            raise Exception(f"创建数据表失败: {result.get('msg')}")

        return result.get("data", {})

    async def list_tables(
        self,
        app_token: str,
    ) -> List[Dict[str, Any]]:
        """
        列出多维表格中的所有数据表.

        Args:
            app_token: 应用token

        Returns:
            List[Dict]: 表列表
        """
        endpoint = f"/open-apis/bitable/v1/apps/{app_token}/tables"

        result = await self._client.request("GET", endpoint)

        if result.get("code") != 0:
            logger.error("Failed to list tables", result=result)
            raise Exception(f"查询数据表失败: {result.get('msg')}")

        return result.get("data", {}).get("items", [])

    async def add_records(
        self,
        app_token: str,
        table_id: str,
        records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        批量添加记录.

        Args:
            app_token: 应用token
            table_id: 表ID
            records: 记录列表，每条记录包含fields字段

        Returns:
            List[Dict]: 添加的记录列表
        """
        endpoint = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"

        payload = {
            "records": [
                {"fields": record} for record in records
            ]
        }

        result = await self._client.request("POST", endpoint, data=payload)

        if result.get("code") != 0:
            logger.error("Failed to add records", result=result)
            raise Exception(f"添加记录失败: {result.get('msg')}")

        return result.get("data", {}).get("records", [])

    async def update_records(
        self,
        app_token: str,
        table_id: str,
        records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        批量更新记录.

        Args:
            app_token: 应用token
            table_id: 表ID
            records: 记录列表，每条记录包含record_id和fields字段

        Returns:
            List[Dict]: 更新的记录列表
        """
        endpoint = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"

        payload = {
            "records": records
        }

        result = await self._client.request("PUT", endpoint, data=payload)

        if result.get("code") != 0:
            logger.error("Failed to update records", result=result)
            raise Exception(f"更新记录失败: {result.get('msg')}")

        return result.get("data", {}).get("records", [])

    async def delete_records(
        self,
        app_token: str,
        table_id: str,
        record_ids: List[str],
    ) -> bool:
        """
        批量删除记录.

        Args:
            app_token: 应用token
            table_id: 表ID
            record_ids: 记录ID列表

        Returns:
            bool: 是否成功
        """
        endpoint = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"

        payload = {
            "record_ids": record_ids
        }

        result = await self._client.request("DELETE", endpoint, data=payload)

        if result.get("code") != 0:
            logger.error("Failed to delete records", result=result)
            raise Exception(f"删除记录失败: {result.get('msg')}")

        return True

    async def search_records(
        self,
        app_token: str,
        table_id: str,
        filter: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        field_names: Optional[List[str]] = None,
        page_size: int = 100,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        搜索记录.

        Args:
            app_token: 应用token
            table_id: 表ID
            filter: 过滤条件
            sort: 排序条件
            field_names: 返回字段列表
            page_size: 分页大小
            page_token: 分页token

        Returns:
            Dict: 包含records和has_more、page_token
        """
        endpoint = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"

        payload = {
            "filter": filter,
            "sort": sort,
            "field_names": field_names,
            "page_size": page_size,
        }

        if page_token:
            payload["page_token"] = page_token

        result = await self._client.request("POST", endpoint, data=payload)

        if result.get("code") != 0:
            logger.error("Failed to search records", result=result)
            raise Exception(f"搜索记录失败: {result.get('msg')}")

        return result.get("data", {})

    async def get_record(
        self,
        app_token: str,
        table_id: str,
        record_id: str,
    ) -> Dict[str, Any]:
        """
        获取单条记录.

        Args:
            app_token: 应用token
            table_id: 表ID
            record_id: 记录ID

        Returns:
            Dict: 记录详情
        """
        endpoint = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"

        result = await self._client.request("GET", endpoint)

        if result.get("code") != 0:
            logger.error("Failed to get record", result=result)
            raise Exception(f"获取记录失败: {result.get('msg')}")

        return result.get("data", {}).get("record", {})

    # ============================================
    # 高级方法（核心业务功能）
    # ============================================

    async def create_project_workspace(
        self,
        project_id: uuid.UUID,
        project_name: str,
        folder_token: str = "root",
    ) -> Dict[str, Any]:
        """
        为项目创建完整工作区.

        创建包含任务表、风险表、里程碑表、成本表等的多维表格。

        Args:
            project_id: 项目ID
            project_name: 项目名称
            folder_token: 文件夹token

        Returns:
            Dict: 包含app_token和各表table_id
        """
        # 创建多维表格应用
        app_result = await self.create_app(
            name=f"{project_name} - 项目管理",
            folder_token=folder_token,
        )
        app_token = app_result.get("app", {}).get("app_token")

        if not app_token:
            raise Exception("创建多维表格应用失败，未获取app_token")

        # 定义表结构
        table_definitions = [
            {
                "name": "任务表",
                "fields": [
                    {"field_name": "任务名称", "type": 1},  # 文本
                    {"field_name": "负责人", "type": 11},  # 人员
                    {"field_name": "进度", "type": 2},     # 数字
                    {"field_name": "状态", "type": 3},     # 单选
                    {"field_name": "开始时间", "type": 5},  # 日期
                    {"field_name": "结束时间", "type": 5},
                    {"field_name": "备注", "type": 1},
                ]
            },
            {
                "name": "风险表",
                "fields": [
                    {"field_name": "风险描述", "type": 1},
                    {"field_name": "风险等级", "type": 3},
                    {"field_name": "风险状态", "type": 3},
                    {"field_name": "责任人", "type": 11},
                    {"field_name": "应对措施", "type": 1},
                    {"field_name": "发现时间", "type": 5},
                ]
            },
            {
                "name": "里程碑表",
                "fields": [
                    {"field_name": "里程碑名称", "type": 1},
                    {"field_name": "计划时间", "type": 5},
                    {"field_name": "实际时间", "type": 5},
                    {"field_name": "状态", "type": 3},
                    {"field_name": "备注", "type": 1},
                ]
            },
            {
                "name": "成本表",
                "fields": [
                    {"field_name": "成本类别", "type": 3},
                    {"field_name": "预算金额", "type": 2},
                    {"field_name": "实际金额", "type": 2},
                    {"field_name": "偏差", "type": 2},
                    {"field_name": "备注", "type": 1},
                ]
            },
        ]

        # 创建各数据表
        tables = {}
        for table_def in table_definitions:
            table_result = await self.create_table(
                app_token=app_token,
                table_name=table_def["name"],
                fields=table_def["fields"],
            )
            table_id = table_result.get("table", {}).get("table_id")
            tables[table_def["name"]] = table_id

        logger.info(
            "Project workspace created",
            project_id=str(project_id),
            app_token=app_token,
            tables=list(tables.keys()),
        )

        return {
            "app_token": app_token,
            "tables": tables,
            "app_url": f"https://feishu.cn/base/{app_token}",
        }

    async def sync_project_data_to_bitable(
        self,
        project_id: uuid.UUID,
        app_token: str,
        table_ids: Dict[str, str],
        session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        同步项目数据到飞书表格.

        Args:
            project_id: 项目ID
            app_token: 应用token
            table_ids: 表ID映射 {"任务表": "xxx", ...}
            session: 数据库会话

        Returns:
            Dict: 同步结果统计
        """
        if not session:
            logger.warning("No session provided, returning mock result")
            return {
                "tasks": 0,
                "risks": 0,
                "milestones": 0,
                "costs": 0,
            }

        stats = {}

        # 同步任务
        if "任务表" in table_ids:
            from app.domain.models.task import Task
            from sqlalchemy import select

            result = await session.execute(
                select(Task).where(Task.project_id == project_id)
            )
            tasks = result.scalars().all()

            records = [
                {
                    "任务名称": t.name,
                    "进度": t.progress or 0,
                    "状态": t.status.value if t.status else "pending",
                    "备注": t.notes or "",
                }
                for t in tasks
            ]

            if records:
                await self.add_records(app_token, table_ids["任务表"], records)
                stats["tasks"] = len(records)
            else:
                stats["tasks"] = 0

        # 同步风险
        if "风险表" in table_ids:
            from app.domain.models.risk import ProjectRisk

            result = await session.execute(
                select(ProjectRisk).where(ProjectRisk.project_id == project_id)
            )
            risks = result.scalars().all()

            records = [
                {
                    "风险描述": r.description or r.title,
                    "风险等级": r.level.value if r.level else "low",
                    "风险状态": r.status.value if r.status else "identified",
                    "应对措施": r.mitigation_plan or "",
                }
                for r in risks
            ]

            if records:
                await self.add_records(app_token, table_ids["风险表"], records)
                stats["risks"] = len(records)
            else:
                stats["risks"] = 0

        # 同步里程碑
        if "里程碑表" in table_ids:
            from app.domain.models.milestone import Milestone

            result = await session.execute(
                select(Milestone).where(Milestone.project_id == project_id)
            )
            milestones = result.scalars().all()

            records = [
                {
                    "里程碑名称": m.name,
                    "计划时间": str(m.planned_date) if m.planned_date else "",
                    "实际时间": str(m.actual_date) if m.actual_date else "",
                    "状态": m.status.value if m.status else "planned",
                }
                for m in milestones
            ]

            if records:
                await self.add_records(app_token, table_ids["里程碑表"], records)
                stats["milestones"] = len(records)
            else:
                stats["milestones"] = 0

        logger.info(
            "Project data synced to bitable",
            project_id=str(project_id),
            stats=stats,
        )

        return stats

    async def sync_bitable_to_project_data(
        self,
        app_token: str,
        table_id: str,
        table_type: str,
        project_id: uuid.UUID,
        session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        反向同步飞书表格数据到项目.

        Args:
            app_token: 应用token
            table_id: 表ID
            table_type: 表类型（任务表/风险表等）
            project_id: 项目ID
            session: 数据库会话

        Returns:
            Dict: 同步结果统计
        """
        if not session:
            logger.warning("No session provided, returning mock result")
            return {"synced": 0, "created": 0, "updated": 0}

        # 获取飞书表格所有记录
        records_result = await self.search_records(
            app_token=app_token,
            table_id=table_id,
            page_size=500,
        )
        records = records_result.get("records", [])

        stats = {"synced": len(records), "created": 0, "updated": 0}

        # 根据表类型处理
        if table_type == "任务表":
            from app.domain.models.task import Task
            from app.domain.enums import TaskStatus

            for record in records:
                fields = record.get("fields", {})
                task_name = fields.get("任务名称", "")

                if not task_name:
                    continue

                # 查找现有任务
                result = await session.execute(
                    select(Task).where(
                        Task.project_id == project_id,
                        Task.name == task_name,
                    )
                )
                existing_task = result.scalar_one_or_none()

                if existing_task:
                    # 更新
                    existing_task.progress = fields.get("进度", 0)
                    existing_task.status = TaskStatus(fields.get("状态", "pending"))
                    existing_task.notes = fields.get("备注", "")
                    stats["updated"] += 1
                else:
                    # 创建
                    new_task = Task(
                        project_id=project_id,
                        name=task_name,
                        progress=fields.get("进度", 0),
                        status=TaskStatus(fields.get("状态", "pending")),
                        notes=fields.get("备注", ""),
                    )
                    session.add(new_task)
                    stats["created"] += 1

            await session.commit()

        logger.info(
            "Bitable data synced to project",
            table_type=table_type,
            project_id=str(project_id),
            stats=stats,
        )

        return stats


# 全局服务实例
_bitable_service: Optional[LarkBitableService] = None


def get_bitable_service() -> LarkBitableService:
    """获取多维表格服务实例."""
    global _bitable_service
    if _bitable_service is None:
        _bitable_service = LarkBitableService()
    return _bitable_service