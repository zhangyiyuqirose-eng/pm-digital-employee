"""
PM Digital Employee - Risk API
项目经理数字员工系统 - 风险预警API端点

提供风险导入导出、批量状态更新、风险统计、预警通知等接口。
"""

import os
import uuid
import tempfile
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query, Body, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.dependencies import get_db_session
from app.core.logging import get_logger
from app.domain.enums import RiskLevel, RiskStatus, RiskCategory, ImportMode
from app.services.risk_service import RiskService
from app.services.excel_service import ExcelService
from app.services.validation_service import ValidationService
from app.services.sync_engine import SyncEngine
from app.services.notification_service import NotificationService

logger = get_logger(__name__)

# 创建风险API路由
risk_router = APIRouter(prefix="/api/v1/risk", tags=["Risk Management"])


# ==================== Pydantic模型 ====================

class RiskImportModel(BaseModel):
    """风险导入模型."""
    project_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    level: str = Field(default="medium")
    category: str = Field(default="schedule")
    probability: int = Field(default=3, ge=1, le=5)
    impact: int = Field(default=3, ge=1, le=5)
    mitigation_plan: Optional[str] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    due_date: Optional[str] = None


class RiskBatchUpdateModel(BaseModel):
    """风险批量更新模型."""
    risk_ids: List[str] = Field(..., min_items=1)
    status: str
    resolution_note: Optional[str] = None


# ==================== 风险导入 ====================

@risk_router.post("/import")
async def import_risk_data(
    file: UploadFile = File(..., description="Excel文件"),
    project_id: str = Query(..., description="项目ID"),
    mode: str = Query(
        default=ImportMode.APPEND_ONLY.value,
        description="导入模式: full_replace/incremental_update/append_only",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    导入风险清单.

    支持Excel批量导入风险数据。

    Args:
        file: Excel文件
        project_id: 项目ID
        mode: 导入模式
        session: 数据库会话

    Returns:
        Dict: 导入结果
    """
    # 参数校验
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="项目ID格式错误")

    # 文件类型校验
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="请上传Excel文件（.xlsx或.xls格式）",
        )

    try:
        # 保存上传文件到临时目录
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)

        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 创建服务实例
        risk_service = RiskService(session)
        excel_service = ExcelService(session)
        validation_service = ValidationService()

        # 解析Excel数据
        data_list, parse_errors = excel_service.parse_excel(temp_file_path, "risk")

        if not data_list:
            os.remove(temp_file_path)
            os.rmdir(temp_dir)
            return {
                "code": 0,
                "msg": "Excel文件中没有有效数据",
                "data": {
                    "rows_total": 0,
                    "rows_imported": 0,
                    "rows_failed": 0,
                    "parse_errors": parse_errors,
                },
            }

        # 执行校验
        validation_results = validation_service.validate_batch(data_list, "risk")
        valid_data = []
        row_errors = []

        for idx, result in enumerate(validation_results):
            if result.is_valid:
                valid_data.append(result.validated_data)
            else:
                row_errors.append({
                    "row_index": idx + 1,
                    "errors": result.errors,
                })

        # 执行导入
        import_result = await risk_service.import_risk_batch(
            project_uuid,
            valid_data,
            mode,
        )

        # 清理临时文件
        os.remove(temp_file_path)
        os.rmdir(temp_dir)

        logger.info(
            f"Risk import completed: project={project_id}, mode={mode}, "
            f"imported={import_result['imported']}, failed={len(row_errors)}"
        )

        return {
            "code": 0,
            "msg": "导入完成",
            "data": {
                "rows_total": len(data_list),
                "rows_imported": import_result["imported"],
                "rows_updated": import_result.get("updated", 0),
                "rows_failed": len(row_errors),
                "validation_errors": row_errors[:100] if row_errors else None,
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to import risk data: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


# ==================== 风险导出 ====================

@risk_router.get("/export/{project_id}")
async def export_risk_data(
    project_id: str,
    export_format: str = Query(
        default="excel",
        description="导出格式: excel/json",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    导出风险清单.

    导出项目风险数据为Excel或JSON格式。

    Args:
        project_id: 项目ID
        export_format: 导出格式
        session: 数据库会话

    Returns:
        StreamingResponse或Dict: 导出结果
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="项目ID格式错误")

    if export_format not in ["excel", "json"]:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的导出格式 '{export_format}'，支持: excel/json",
        )

    try:
        risk_service = RiskService(session)

        # 获取风险数据
        risks = await risk_service.list_risks(project_uuid)
        data_list = [
            {
                "code": r.code,
                "title": r.title,
                "description": r.description,
                "level": r.level,
                "category": r.category,
                "status": r.status,
                "probability": r.probability,
                "impact": r.impact,
                "identified_date": str(r.identified_date) if r.identified_date else None,
                "due_date": str(r.due_date) if r.due_date else None,
                "mitigation_plan": r.mitigation_plan,
                "owner_id": r.owner_id,
                "owner_name": r.owner_name,
            }
            for r in risks
        ]

        if export_format == "json":
            # JSON格式直接返回
            logger.info(f"Risk export completed: project={project_id}, format=json")
            return {
                "code": 0,
                "msg": "导出成功",
                "data": {
                    "total": len(data_list),
                    "risks": data_list,
                },
            }

        # Excel格式
        buffer = await risk_service.generate_export_excel(project_uuid)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"风险清单_{project_id}_{timestamp}.xlsx"

        logger.info(f"Risk export completed: project={project_id}, format=excel")

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to export risk data: {e}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


# ==================== 风险批量状态更新 ====================

@risk_router.post("/batch-update")
async def batch_update_risk_status(
    update_data: RiskBatchUpdateModel,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    批量更新风险状态.

    批量更新多条风险的状态，支持闭环管理。

    Args:
        update_data: 批量更新参数
        session: 数据库会话

    Returns:
        Dict: 更新结果
    """
    # 状态校验
    valid_statuses = [
        RiskStatus.IDENTIFIED.value,
        RiskStatus.ANALYZING.value,
        RiskStatus.MITIGATING.value,
        RiskStatus.RESOLVED.value,
        RiskStatus.ACCEPTED.value,
        RiskStatus.CLOSED.value,
    ]

    if update_data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"无效的风险状态 '{update_data.status}'，支持: {valid_statuses}",
        )

    # ID解析
    risk_uuids = []
    for risk_id in update_data.risk_ids:
        try:
            risk_uuids.append(uuid.UUID(risk_id))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"风险ID格式错误: {risk_id}",
            )

    try:
        risk_service = RiskService(session)
        notification_service = NotificationService(session)

        # 执行批量更新
        result = await risk_service.batch_update_status(
            risk_uuids,
            update_data.status,
            update_data.resolution_note,
        )

        # 对高风险或已解决的风险发送通知
        if result["success_count"] > 0:
            # 发送预警通知（如果有高风险）
            if update_data.status in [RiskStatus.IDENTIFIED.value, RiskStatus.MITIGATING.value]:
                for risk_id in result["updated_ids"]:
                    try:
                        # 查询风险详情，判断是否需要发送预警
                        # 这里简化处理，实际应根据风险等级判断
                        pass
                    except Exception as e:
                        logger.warning(f"Failed to send notification for risk {risk_id}: {e}")

        logger.info(
            f"Risk batch update completed: count={len(risk_uuids)}, "
            f"success={result['success_count']}, status={update_data.status}"
        )

        return {
            "code": 0,
            "msg": "批量更新完成",
            "data": {
                "total": len(risk_uuids),
                "success_count": result["success_count"],
                "failed_count": result["failed_count"],
                "updated_ids": [str(id) for id in result["updated_ids"]],
                "failed_ids": result["failed_ids"],
            },
        }

    except Exception as e:
        logger.error(f"Failed to batch update risk status: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


# ==================== 风险统计 ====================

@risk_router.get("/statistics/{project_id}")
async def get_risk_statistics(
    project_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    获取风险统计报表数据.

    用于生成风险统计图表和预警报告。

    Args:
        project_id: 项目ID
        session: 数据库会话

    Returns:
        Dict: 统计报表数据
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="项目ID格式错误")

    try:
        risk_service = RiskService(session)

        # 获取统计数据
        statistics = await risk_service.get_risk_statistics(project_uuid)

        # 扩展统计数据，增加图表数据
        enhanced_stats = await risk_service.get_enhanced_statistics(project_uuid)

        logger.info(f"Risk statistics retrieved: project={project_id}")

        return {
            "code": 0,
            "msg": "查询成功",
            "data": {
                "basic": statistics,
                "enhanced": enhanced_stats,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get risk statistics: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ==================== 风险预警通知 ====================

@risk_router.post("/warning/send")
async def send_risk_warning(
    project_id: str = Query(..., description="项目ID"),
    risk_level: str = Query(
        default="high",
        description="预警风险等级: high/critical",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    发送风险预警通知.

    根据风险等级自动发送飞书预警通知。

    Args:
        project_id: 项目ID
        risk_level: 预警风险等级
        session: 数据库会话

    Returns:
        Dict: 发送结果
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="项目ID格式错误")

    if risk_level not in ["high", "critical"]:
        raise HTTPException(
            status_code=400,
            detail=f"无效的风险等级 '{risk_level}'，支持: high/critical",
        )

    try:
        risk_service = RiskService(session)
        notification_service = NotificationService(session)

        # 获取高风险列表
        level_filter = RiskLevel.HIGH if risk_level == "high" else RiskLevel.CRITICAL
        high_risks = await risk_service.list_risks(
            project_uuid,
            level=level_filter,
            status=RiskStatus.IDENTIFIED,
        )

        if not high_risks:
            return {
                "code": 0,
                "msg": "没有需要预警的风险",
                "data": {
                    "total": 0,
                    "sent": 0,
                },
            }

        # 发送预警通知
        sent_count = 0
        failed_count = 0

        for risk in high_risks:
            try:
                # 发送飞书预警通知
                result = await notification_service.send_risk_warning_notification(
                    risk_id=risk.id,
                    project_id=project_uuid,
                    risk_level=risk.level,
                    risk_title=risk.title,
                    owner_id=risk.owner_id,
                )
                if result.get("status") == "success":
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.warning(f"Failed to send warning for risk {risk.id}: {e}")
                failed_count += 1

        logger.info(
            f"Risk warnings sent: project={project_id}, level={risk_level}, "
            f"sent={sent_count}, failed={failed_count}"
        )

        return {
            "code": 0,
            "msg": "预警通知发送完成",
            "data": {
                "total": len(high_risks),
                "sent": sent_count,
                "failed": failed_count,
            },
        }

    except Exception as e:
        logger.error(f"Failed to send risk warning: {e}")
        raise HTTPException(status_code=500, detail=f"发送失败: {str(e)}")


# ==================== 飞书表格同步 ====================

@risk_router.post("/sync/lark-sheet")
async def sync_risk_to_lark_sheet(
    project_id: str = Query(..., description="项目ID"),
    sheet_token: str = Query(..., description="飞书表格Token"),
    sync_direction: str = Query(
        default="to_sheet",
        description="同步方向: to_sheet/from_sheet/bidirectional",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    同步风险数据到飞书在线表格.

    支持单向和双向同步。

    Args:
        project_id: 项目ID
        sheet_token: 飞书表格Token
        sync_direction: 同步方向
        session: 数据库会话

    Returns:
        Dict: 同步结果
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="项目ID格式错误")

    if sync_direction not in ["to_sheet", "from_sheet", "bidirectional"]:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的同步方向 '{sync_direction}'",
        )

    try:
        risk_service = RiskService(session)
        sync_engine = SyncEngine(session)

        # 执行同步
        result = await risk_service.sync_risk_to_lark_sheet(
            project_uuid,
            sheet_token,
            sync_direction,
            sync_engine,
        )

        logger.info(
            f"Risk sync to Lark sheet completed: project={project_id}, "
            f"direction={sync_direction}, success={result['success']}"
        )

        return {
            "code": 0,
            "msg": "同步完成",
            "data": result,
        }

    except Exception as e:
        logger.error(f"Failed to sync risk to Lark sheet: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


# ==================== 风险闭环管理 ====================

@risk_router.post("/resolve/{risk_id}")
async def resolve_risk(
    risk_id: str,
    project_id: str = Query(..., description="项目ID"),
    resolution_note: Optional[str] = Query(None, description="解决说明"),
    root_cause: Optional[str] = Query(None, description="根因分析"),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    解决风险并完成闭环.

    Args:
        risk_id: 风险ID
        project_id: 项目ID
        resolution_note: 解决说明
        root_cause: 根因分析
        session: 数据库会话

    Returns:
        Dict: 解决结果
    """
    try:
        risk_uuid = uuid.UUID(risk_id)
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID格式错误")

    try:
        risk_service = RiskService(session)

        # 解决风险
        risk = await risk_service.resolve_risk(
            risk_uuid,
            project_uuid,
            resolution_note,
        )

        # 如果有根因分析，更新根因字段
        if root_cause:
            await risk_service.update_risk(
                risk_uuid,
                project_uuid,
                root_cause=root_cause,
            )

        logger.info(f"Risk resolved: risk={risk_id}, project={project_id}")

        return {
            "code": 0,
            "msg": "风险已解决",
            "data": {
                "risk_id": str(risk.id),
                "status": risk.status,
                "resolved_date": str(risk.resolved_date) if risk.resolved_date else None,
            },
        }

    except Exception as e:
        logger.error(f"Failed to resolve risk: {e}")
        raise HTTPException(status_code=500, detail=f"解决失败: {str(e)}")


# ==================== 高风险查询 ====================

@risk_router.get("/high-risks/{project_id}")
async def list_high_risks(
    project_id: str,
    include_critical: bool = Query(True, description="是否包含严重风险"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    查询高风险列表.

    用于重点关注和预警通知。

    Args:
        project_id: 项目ID
        include_critical: 是否包含严重风险
        limit: 返回数量限制
        session: 数据库会话

    Returns:
        Dict: 高风险列表
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="项目ID格式错误")

    try:
        risk_service = RiskService(session)
        notification_service = NotificationService(session)

        # 获取高风险
        high_risks = await risk_service.list_high_risks(project_uuid, limit=limit)

        # 如果包含严重风险，补充严重风险列表
        if include_critical:
            critical_risks = await risk_service.list_risks(
                project_uuid,
                level=RiskLevel.CRITICAL,
            )
            high_risks = high_risks + critical_risks

        # 转换为响应格式
        risk_list = []
        for risk in high_risks:
            risk_list.append({
                "id": str(risk.id),
                "code": risk.code,
                "title": risk.title,
                "description": risk.description,
                "level": risk.level,
                "category": risk.category,
                "status": risk.status,
                "probability": risk.probability,
                "impact": risk.impact,
                "risk_score": risk.risk_score,
                "owner_id": risk.owner_id,
                "owner_name": risk.owner_name,
                "due_date": str(risk.due_date) if risk.due_date else None,
                "identified_date": str(risk.identified_date) if risk.identified_date else None,
            })

        logger.info(f"High risks retrieved: project={project_id}, count={len(risk_list)}")

        return {
            "code": 0,
            "msg": "查询成功",
            "data": {
                "total": len(risk_list),
                "risks": risk_list,
            },
        }

    except Exception as e:
        logger.error(f"Failed to list high risks: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ==================== 风险详情 ====================

@risk_router.get("/{risk_id}")
async def get_risk_detail(
    risk_id: str,
    project_id: str = Query(..., description="项目ID"),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    获取风险详情.

    Args:
        risk_id: 风险ID
        project_id: 项目ID
        session: 数据库会话

    Returns:
        Dict: 风险详情
    """
    try:
        risk_uuid = uuid.UUID(risk_id)
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID格式错误")

    try:
        risk_service = RiskService(session)

        # 获取风险详情
        risk = await risk_service.get_risk(risk_uuid, project_uuid)

        logger.info(f"Risk detail retrieved: risk={risk_id}")

        return {
            "code": 0,
            "msg": "查询成功",
            "data": {
                "id": str(risk.id),
                "code": risk.code,
                "title": risk.title,
                "description": risk.description,
                "level": risk.level,
                "category": risk.category,
                "status": risk.status,
                "probability": risk.probability,
                "impact": risk.impact,
                "risk_score": risk.risk_score,
                "is_high_risk": risk.is_high_risk,
                "identified_date": str(risk.identified_date) if risk.identified_date else None,
                "due_date": str(risk.due_date) if risk.due_date else None,
                "resolved_date": str(risk.resolved_date) if risk.resolved_date else None,
                "mitigation_plan": risk.mitigation_plan,
                "mitigation_status": risk.mitigation_status,
                "owner_id": risk.owner_id,
                "owner_name": risk.owner_name,
                "root_cause": risk.root_cause,
                "ai_suggestion": risk.ai_suggestion,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get risk detail: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")