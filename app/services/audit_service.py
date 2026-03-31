"""
PM Digital Employee - Audit Service
项目经理数字员工系统 - 审计日志写入与查询服务

实现全流程审计日志记录、查询、归档能力。
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.domain.enums import AuditAction
from app.domain.models.audit_log import AuditLog

logger = get_logger(__name__)


class AuditService:
    """
    审计日志服务.

    实现审计日志的写入、查询、归档能力。
    所有操作必须记录审计日志，日志仅追加写入。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化审计服务.

        Args:
            session: 数据库会话
        """
        self.session = session

    async def log(
        self,
        action: str,
        trace_id: str,
        user_id: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        result: str = "success",
        details: Optional[Dict] = None,
        request_params: Optional[Dict] = None,
        response_summary: Optional[str] = None,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        duration_ms: Optional[int] = None,
        skill_name: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_tokens_input: Optional[int] = None,
        llm_tokens_output: Optional[int] = None,
    ) -> AuditLog:
        """
        记录审计日志.

        Args:
            action: 操作类型
            trace_id: 追踪ID
            user_id: 用户飞书ID
            project_id: 项目ID
            resource_type: 资源类型
            resource_id: 资源ID
            result: 操作结果
            details: 详细信息
            request_params: 请求参数
            response_summary: 响应摘要
            error_message: 错误信息
            ip_address: 客户端IP
            user_agent: 用户代理
            duration_ms: 耗时毫秒
            skill_name: Skill名称
            llm_model: LLM模型
            llm_tokens_input: LLM输入Token数
            llm_tokens_output: LLM输出Token数

        Returns:
            AuditLog: 审计日志记录
        """
        log_entry = AuditLog(
            id=uuid.uuid4(),
            trace_id=trace_id,
            user_id=user_id,
            project_id=project_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            duration_ms=duration_ms,
            skill_name=skill_name,
            llm_model=llm_model,
            llm_tokens_input=llm_tokens_input,
            llm_tokens_output=llm_tokens_output,
        )

        # 序列化JSON字段
        if details:
            log_entry.details = json.dumps(details, ensure_ascii=False)
        if request_params:
            # 过滤敏感参数
            filtered_params = self._filter_sensitive_params(request_params)
            log_entry.request_params = json.dumps(filtered_params, ensure_ascii=False)
        if response_summary:
            log_entry.response_summary = response_summary[:1000] if len(response_summary) > 1000 else response_summary

        self.session.add(log_entry)

        logger.debug(
            "Audit log created",
            action=action,
            trace_id=trace_id,
            result=result,
        )

        return log_entry

    async def log_user_action(
        self,
        user_id: str,
        action: str,
        trace_id: str,
        project_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
    ) -> AuditLog:
        """
        记录用户操作审计日志.

        Args:
            user_id: 用户飞书ID
            action: 操作类型
            trace_id: 追踪ID
            project_id: 项目ID
            resource_type: 资源类型
            resource_id: 资源ID
            details: 详细信息

        Returns:
            AuditLog: 审计日志记录
        """
        return await self.log(
            action=action,
            trace_id=trace_id,
            user_id=user_id,
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )

    async def log_skill_execution(
        self,
        user_id: str,
        skill_name: str,
        trace_id: str,
        project_id: Optional[uuid.UUID] = None,
        params: Optional[Dict] = None,
        result: str = "success",
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """
        记录Skill执行审计日志.

        Args:
            user_id: 用户飞书ID
            skill_name: Skill名称
            trace_id: 追踪ID
            project_id: 项目ID
            params: 执行参数
            result: 执行结果
            duration_ms: 耗时
            error_message: 错误信息

        Returns:
            AuditLog: 审计日志记录
        """
        return await self.log(
            action=AuditAction.EXECUTE_SKILL,
            trace_id=trace_id,
            user_id=user_id,
            project_id=project_id,
            resource_type="skill",
            resource_id=skill_name,
            result=result,
            request_params=params,
            duration_ms=duration_ms,
            skill_name=skill_name,
            error_message=error_message,
        )

    async def log_llm_request(
        self,
        user_id: str,
        trace_id: str,
        model: str,
        tokens_input: int,
        tokens_output: int,
        duration_ms: int,
        project_id: Optional[uuid.UUID] = None,
        skill_name: Optional[str] = None,
        prompt_preview: Optional[str] = None,
    ) -> AuditLog:
        """
        记录LLM请求审计日志.

        Args:
            user_id: 用户飞书ID
            trace_id: 追踪ID
            model: 模型名称
            tokens_input: 输入Token数
            tokens_output: 输出Token数
            duration_ms: 耗时
            project_id: 项目ID
            skill_name: Skill名称
            prompt_preview: Prompt预览

        Returns:
            AuditLog: 审计日志记录
        """
        return await self.log(
            action=AuditAction.LLM_REQUEST,
            trace_id=trace_id,
            user_id=user_id,
            project_id=project_id,
            resource_type="llm",
            resource_id=model,
            duration_ms=duration_ms,
            skill_name=skill_name,
            llm_model=model,
            llm_tokens_input=tokens_input,
            llm_tokens_output=tokens_output,
            details={"prompt_preview": prompt_preview[:200] if prompt_preview else None},
        )

    async def log_security_event(
        self,
        action: str,
        trace_id: str,
        user_id: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        violation_type: Optional[str] = None,
        details: Optional[Dict] = None,
    ) -> AuditLog:
        """
        记录安全事件审计日志.

        Args:
            action: 操作类型
            trace_id: 追踪ID
            user_id: 用户飞书ID
            project_id: 项目ID
            violation_type: 违规类型
            details: 详细信息

        Returns:
            AuditLog: 审计日志记录
        """
        log_details = details or {}
        if violation_type:
            log_details["violation_type"] = violation_type

        return await self.log(
            action=action,
            trace_id=trace_id,
            user_id=user_id,
            project_id=project_id,
            result="blocked",
            details=log_details,
        )

    async def query_logs(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        result: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        查询审计日志.

        Args:
            user_id: 用户飞书ID
            project_id: 项目ID
            action: 操作类型
            result: 操作结果
            start_time: 开始时间
            end_time: 结束时间
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[AuditLog]: 审计日志列表
        """
        query = select(AuditLog)

        conditions = []
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if project_id:
            conditions.append(AuditLog.project_id == project_id)
        if action:
            conditions.append(AuditLog.action == action)
        if result:
            conditions.append(AuditLog.result == result)
        if start_time:
            conditions.append(AuditLog.created_at >= start_time)
        if end_time:
            conditions.append(AuditLog.created_at <= end_time)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    def _filter_sensitive_params(self, params: Dict) -> Dict:
        """
        过滤敏感参数.

        Args:
            params: 原始参数

        Returns:
            Dict: 过滤后的参数
        """
        sensitive_keys = [
            "password",
            "secret",
            "token",
            "key",
            "credential",
            "api_key",
            "app_secret",
            "access_token",
            "refresh_token",
        ]

        filtered = {}
        for key, value in params.items():
            if any(sk in key.lower() for sk in sensitive_keys):
                filtered[key] = "[FILTERED]"
            elif isinstance(value, str) and len(value) > 500:
                filtered[key] = value[:500] + "..."
            else:
                filtered[key] = value

        return filtered