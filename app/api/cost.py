"""
PM Digital Employee - Cost API
项目经理数字员工系统 - 成本管理API端点

提供成本导入导出、成本分析、阈值设置、超支预警等接口。
"""

import os
import uuid
import tempfile
import json
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query, Body, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.dependencies import get_db_session
from app.core.logging import get_logger
from app.domain.enums import CostCategory, ImportMode
from app.services.cost_service import CostService
from app.services.excel_service import ExcelService
from app.services.validation_service import ValidationService
from app.services.sync_engine import SyncEngine
from app.services.notification_service import NotificationService

logger = get_logger(__name__)

# 创建成本API路由
cost_router = APIRouter(prefix="/api/v1/cost", tags=["Cost Management"])


# ==================== Pydantic模型 ====================

class CostThresholdModel(BaseModel):
    """成本阈值设置模型."""
    project_id: str = Field(..., description="项目ID")
    threshold_percent: float = Field(..., ge=0, le=100, description="阈值百分比（如80表示80%预算时预警）")
    warning_level: str = Field(default="medium", description="预警等级：low/medium/high")
    notify_users: Optional[List[str]] = Field(default=None, description="通知用户ID列表")


class CostBudgetImportModel(BaseModel):
    """成本预算导入模型."""
    project_id: str
    category: str
    amount: float = Field(..., ge=0)
    description: Optional[str] = None
    fiscal_year: Optional[int] = None


class CostActualImportModel(BaseModel):
    """成本实际支出导入模型."""
    project_id: str
    category: str
    amount: float = Field(..., ge=0)
    expense_date: str
    description: Optional[str] = None
    invoice_number: Optional[str] = None


# ==================== 成本导入 ====================

@cost_router.post("/import")
async def import_cost_data(
    file: UploadFile = File(..., description="Excel文件"),
    project_id: str = Query(..., description="项目ID"),
    mode: str = Query(
        default=ImportMode.APPEND_ONLY.value,
        description="导入模式: full_replace/incremental_update/append_only",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    导入成本数据.

    支持导入成本预算和实际支出明细。

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
        cost_service = CostService(session)
        excel_service = ExcelService(session)
        validation_service = ValidationService()

        # 解析Excel数据
        data_list, parse_errors = excel_service.parse_excel(temp_file_path, "cost")

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
        validation_results = validation_service.validate_batch(data_list, "cost")
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
        import_result = await cost_service.import_cost_batch(
            project_uuid,
            valid_data,
            mode,
        )

        # 清理临时文件
        os.remove(temp_file_path)
        os.rmdir(temp_dir)

        logger.info(
            f"Cost import completed: project={project_id}, mode={mode}, "
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
        logger.error(f"Failed to import cost data: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


# ==================== 成本导出 ====================

@cost_router.get("/export/{project_id}")
async def export_cost_data(
    project_id: str,
    export_type: str = Query(
        default="all",
        description="导出类型: all/budget/actual",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """
    导出成本数据.

    导出项目成本预算和实际支出明细。

    Args:
        project_id: 项目ID
        export_type: 导出类型（all/budget/actual）
        session: 数据库会话

    Returns:
        StreamingResponse: Excel文件流
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="项目ID格式错误")

    if export_type not in ["all", "budget", "actual"]:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的导出类型 '{export_type}'，支持: all/budget/actual",
        )

    try:
        cost_service = CostService(session)
        excel_service = ExcelService(session)

        # 获取成本数据
        if export_type == "budget":
            budgets = await cost_service.list_budgets(project_uuid)
            data_list = [
                {
                    "category": b.category,
                    "amount": float(b.amount),
                    "description": b.description,
                    "fiscal_year": b.fiscal_year,
                }
                for b in budgets
            ]
        elif export_type == "actual":
            actuals = await cost_service.list_actuals(project_uuid)
            data_list = [
                {
                    "category": a.category,
                    "amount": float(a.amount),
                    "expense_date": str(a.expense_date),
                    "description": a.description,
                    "invoice_number": a.invoice_number,
                }
                for a in actuals
            ]
        else:
            # 导出全部
            budgets = await cost_service.list_budgets(project_uuid)
            actuals = await cost_service.list_actuals(project_uuid)
            data_list = {
                "budgets": [
                    {
                        "category": b.category,
                        "amount": float(b.amount),
                        "description": b.description,
                        "fiscal_year": b.fiscal_year,
                    }
                    for b in budgets
                ],
                "actuals": [
                    {
                        "category": a.category,
                        "amount": float(a.amount),
                        "expense_date": str(a.expense_date),
                        "description": a.description,
                        "invoice_number": a.invoice_number,
                    }
                    for a in actuals
                ],
            }

        # 生成Excel文件
        buffer = await cost_service.generate_export_excel(project_uuid, export_type)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"成本数据_{project_id}_{export_type}_{timestamp}.xlsx"

        logger.info(f"Cost export completed: project={project_id}, type={export_type}")

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
        logger.error(f"Failed to export cost data: {e}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


# ==================== 成本分析 ====================

@cost_router.get("/analysis/{project_id}")
async def get_cost_analysis(
    project_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    获取成本分析报告.

    计算成本偏差、成本执行率、剩余预算等关键指标。

    Args:
        project_id: 项目ID
        session: 数据库会话

    Returns:
        Dict: 成本分析报告
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="项目ID格式错误")

    try:
        cost_service = CostService(session)

        # 获取成本分析数据
        analysis = await cost_service.get_cost_analysis(project_uuid)

        logger.info(f"Cost analysis completed: project={project_id}")

        return {
            "code": 0,
            "msg": "分析完成",
            "data": analysis,
        }

    except Exception as e:
        logger.error(f"Failed to analyze cost: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


# ==================== 成本阈值设置 ====================

@cost_router.post("/threshold")
async def set_cost_threshold(
    threshold: CostThresholdModel,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    设置成本预警阈值.

    当实际支出超过阈值百分比时，自动发送预警通知。

    Args:
        threshold: 阈值设置参数
        session: 数据库会话

    Returns:
        Dict: 设置结果
    """
    try:
        project_uuid = uuid.UUID(threshold.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="项目ID格式错误")

    if threshold.warning_level not in ["low", "medium", "high"]:
        raise HTTPException(
            status_code=400,
            detail="预警等级必须是 low/medium/high",
        )

    try:
        cost_service = CostService(session)

        # 设置阈值
        result = await cost_service.set_cost_threshold(
            project_uuid,
            threshold.threshold_percent,
            threshold.warning_level,
            threshold.notify_users,
        )

        logger.info(
            f"Cost threshold set: project={threshold.project_id}, "
            f"percent={threshold.threshold_percent}, level={threshold.warning_level}"
        )

        return {
            "code": 0,
            "msg": "阈值设置成功",
            "data": result,
        }

    except Exception as e:
        logger.error(f"Failed to set cost threshold: {e}")
        raise HTTPException(status_code=500, detail=f"设置失败: {str(e)}")


# ==================== 成本预警查询 ====================

@cost_router.get("/warning")
async def get_cost_warnings(
    project_id: Optional[str] = Query(None, description="项目ID过滤"),
    warning_level: Optional[str] = Query(None, description="预警等级过滤"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    获取超支预警列表.

    查询所有超过阈值的项目成本预警。

    Args:
        project_id: 项目ID过滤（可选）
        warning_level: 预警等级过滤（可选）
        limit: 返回数量限制
        session: 数据库会话

    Returns:
        Dict: 预警列表
    """
    try:
        cost_service = CostService(session)

        # 获取预警列表
        warnings = await cost_service.get_cost_warnings(
            project_id=uuid.UUID(project_id) if project_id else None,
            warning_level=warning_level,
            limit=limit,
        )

        logger.info(f"Cost warnings retrieved: count={len(warnings)}")

        return {
            "code": 0,
            "msg": "查询成功",
            "data": {
                "total": len(warnings),
                "warnings": warnings,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get cost warnings: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ==================== 飞书表格同步 ====================

@cost_router.post("/sync/lark-sheet")
async def sync_cost_to_lark_sheet(
    project_id: str = Query(..., description="项目ID"),
    sheet_token: str = Query(..., description="飞书表格Token"),
    sync_direction: str = Query(
        default="to_sheet",
        description="同步方向: to_sheet/from_sheet/bidirectional",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    同步成本数据到飞书在线表格.

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
        cost_service = CostService(session)
        sync_engine = SyncEngine(session)

        # 执行同步
        result = await cost_service.sync_cost_to_lark_sheet(
            project_uuid,
            sheet_token,
            sync_direction,
            sync_engine,
        )

        logger.info(
            f"Cost sync to Lark sheet completed: project={project_id}, "
            f"direction={sync_direction}, success={result['success']}"
        )

        return {
            "code": 0,
            "msg": "同步完成",
            "data": result,
        }

    except Exception as e:
        logger.error(f"Failed to sync cost to Lark sheet: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


# ==================== 成本统计报表 ====================

@cost_router.get("/statistics/{project_id}")
async def get_cost_statistics(
    project_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    获取成本统计报表数据.

    用于生成成本趋势分析图等可视化数据。

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
        cost_service = CostService(session)

        # 获取统计数据
        statistics = await cost_service.get_cost_statistics(project_uuid)

        logger.info(f"Cost statistics retrieved: project={project_id}")

        return {
            "code": 0,
            "msg": "查询成功",
            "data": statistics,
        }

    except Exception as e:
        logger.error(f"Failed to get cost statistics: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ==================== 成本审批集成 ====================

@cost_router.post("/approval/submit")
async def submit_cost_approval(
    project_id: str = Query(..., description="项目ID"),
    actual_id: str = Query(..., description="实际支出ID"),
    approval_type: str = Query(
        default="expense",
        description="审批类型: expense/budget_adjust",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    提交成本审批流程.

    集成飞书审批API，发起审批流程。

    Args:
        project_id: 项目ID
        actual_id: 实际支出ID
        approval_type: 审批类型
        session: 数据库会话

    Returns:
        Dict: 审批提交结果
    """
    try:
        project_uuid = uuid.UUID(project_id)
        actual_uuid = uuid.UUID(actual_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID格式错误")

    try:
        cost_service = CostService(session)

        # 提交审批
        result = await cost_service.submit_cost_approval(
            project_uuid,
            actual_uuid,
            approval_type,
        )

        logger.info(
            f"Cost approval submitted: project={project_id}, "
            f"actual={actual_id}, type={approval_type}"
        )

        return {
            "code": 0,
            "msg": "审批提交成功",
            "data": result,
        }

    except Exception as e:
        logger.error(f"Failed to submit cost approval: {e}")
        raise HTTPException(status_code=500, detail=f"提交失败: {str(e)}")


# ==================== 成本趋势分析 ====================

@cost_router.get("/trend/{project_id}")
async def get_cost_trend(
    project_id: str,
    period: str = Query(
        default="month",
        description="时间周期: week/month/quarter",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    获取成本趋势分析数据.

    用于生成成本趋势图表。

    Args:
        project_id: 项目ID
        period: 时间周期
        session: 数据库会话

    Returns:
        Dict: 趋势分析数据
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="项目ID格式错误")

    if period not in ["week", "month", "quarter"]:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的时间周期 '{period}'",
        )

    try:
        cost_service = CostService(session)

        # 获取趋势数据
        trend = await cost_service.get_cost_trend(project_uuid, period)

        logger.info(f"Cost trend retrieved: project={project_id}, period={period}")

        return {
            "code": 0,
            "msg": "查询成功",
            "data": trend,
        }

    except Exception as e:
        logger.error(f"Failed to get cost trend: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")