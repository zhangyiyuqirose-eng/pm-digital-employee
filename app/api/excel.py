"""
PM Digital Employee - Excel API
项目经理数字员工系统 - Excel导入导出API端点

提供模板下载、数据导入、数据导出、导入日志查询接口。
"""

import os
import uuid
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.core.logging import get_logger
from app.domain.enums import ImportMode
from app.services.excel_service import ExcelService

logger = get_logger(__name__)

# 创建Excel API路由
excel_router = APIRouter(prefix="/api/v1/excel", tags=["Excel Import/Export"])

# 支持的模块列表
SUPPORTED_MODULES = ["project", "task", "milestone", "risk", "cost"]

# 支持的导入模式
SUPPORTED_IMPORT_MODES = [
    ImportMode.FULL_REPLACE.value,
    ImportMode.INCREMENTAL_UPDATE.value,
    ImportMode.APPEND_ONLY.value,
]


# ==================== 模板下载 ====================

@excel_router.get("/template/{module}")
async def download_template(
    module: str,
) -> StreamingResponse:
    """
    下载Excel模板.

    Args:
        module: 模块名称（project/task/milestone/risk/cost）

    Returns:
        StreamingResponse: Excel文件流

    Raises:
        HTTPException: 模块不存在
    """
    if module not in SUPPORTED_MODULES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模块 '{module}'，支持的模块: {SUPPORTED_MODULES}",
        )

    try:
        # 创建Excel服务实例（不需要数据库会话）
        service = ExcelService(None)  # 模板生成不需要数据库

        # 生成模板
        buffer = service.generate_template(module)

        # 返回文件流
        filename = f"{module}_导入模板_{datetime.now().strftime('%Y%m%d')}.xlsx"

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
        logger.error(f"Failed to generate template: {e}")
        raise HTTPException(status_code=500, detail="模板生成失败")


# ==================== 数据导入 ====================

@excel_router.post("/import/{module}")
async def import_data(
    module: str,
    file: UploadFile = File(...),
    mode: str = Query(
        default=ImportMode.APPEND_ONLY.value,
        description="导入模式: full_replace/incremental_update/append_only",
    ),
    project_id: Optional[str] = Query(
        default=None,
        description="项目ID（任务/里程碑/风险/成本导入需要）",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    上传Excel导入数据.

    Args:
        module: 模块名称
        file: 上传的Excel文件
        mode: 导入模式
        project_id: 项目ID（可选）
        session: 数据库会话

    Returns:
        Dict: 导入结果

    Raises:
        HTTPException: 参数错误或导入失败
    """
    # 参数校验
    if module not in SUPPORTED_MODULES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模块 '{module}'，支持的模块: {SUPPORTED_MODULES}",
        )

    if mode not in SUPPORTED_IMPORT_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的导入模式 '{mode}'，支持的模式: {SUPPORTED_IMPORT_MODES}",
        )

    # 文件类型校验
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="请上传Excel文件（.xlsx或.xls格式）",
        )

    # 项目ID解析
    project_uuid = None
    if project_id:
        try:
            project_uuid = uuid.UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="项目ID格式错误")

    # 检查任务/里程碑/风险/成本导入是否提供了项目ID
    if module in ["task", "milestone", "risk", "cost"] and not project_uuid:
        raise HTTPException(
            status_code=400,
            detail=f"{module}模块导入需要指定项目ID",
        )

    try:
        # 保存上传文件到临时目录
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)

        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 创建Excel服务
        service = ExcelService(session)

        # 解析Excel数据
        data_list, parse_errors = service.parse_excel(temp_file_path, module)

        if not data_list:
            # 清理临时文件
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

        # 执行导入
        import_log = await service.import_data(
            data_list=data_list,
            module=module,
            import_mode=mode,
            project_id=project_uuid,
        )

        # 清理临时文件
        os.remove(temp_file_path)
        os.rmdir(temp_dir)

        logger.info(
            f"Excel import completed: module={module}, mode={mode}, "
            f"log_id={str(import_log.id)}, imported={import_log.rows_imported}"
        )

        return {
            "code": 0,
            "msg": "导入完成",
            "data": {
                "log_id": str(import_log.id),
                "file_name": import_log.file_name,
                "import_mode": import_log.import_mode,
                "validation_passed": import_log.validation_passed,
                "rows_total": import_log.rows_total,
                "rows_imported": import_log.rows_imported,
                "rows_updated": import_log.rows_updated,
                "rows_skipped": import_log.rows_skipped,
                "rows_failed": import_log.rows_failed,
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to import Excel data: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


# ==================== 数据导出 ====================

@excel_router.get("/export/{module}")
async def export_data(
    module: str,
    project_id: Optional[str] = Query(
        default=None,
        description="项目ID（可选，用于导出指定项目的数据）",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """
    导出数据为Excel.

    Args:
        module: 模块名称
        project_id: 项目ID（可选）
        session: 数据库会话

    Returns:
        StreamingResponse: Excel文件流

    Raises:
        HTTPException: 参数错误或导出失败
    """
    # 参数校验
    if module not in SUPPORTED_MODULES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模块 '{module}'，支持的模块: {SUPPORTED_MODULES}",
        )

    # 项目ID解析
    project_uuid = None
    if project_id:
        try:
            project_uuid = uuid.UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="项目ID格式错误")

    try:
        # 创建Excel服务
        service = ExcelService(session)

        # 执行导出
        buffer = await service.export_data(module, project_uuid)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        if project_id:
            filename = f"{module}_{project_id}_导出_{timestamp}.xlsx"
        else:
            filename = f"{module}_全部导出_{timestamp}.xlsx"

        logger.info(f"Excel export completed: module={module}, project_id={project_id}")

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
        logger.error(f"Failed to export Excel data: {e}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


# ==================== 导入日志查询 ====================

@excel_router.get("/import-logs")
async def get_import_logs(
    module: Optional[str] = Query(
        default=None,
        description="模块名称过滤",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="返回数量限制",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    获取导入日志列表.

    Args:
        module: 模块名称过滤（可选）
        limit: 返回数量限制
        session: 数据库会话

    Returns:
        Dict: 导入日志列表
    """
    # 参数校验
    if module and module not in SUPPORTED_MODULES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模块 '{module}'，支持的模块: {SUPPORTED_MODULES}",
        )

    try:
        # 创建Excel服务
        service = ExcelService(session)

        # 查询导入日志
        logs = await service.get_import_logs(module=module, limit=limit)

        # 转换为响应格式
        log_list = []
        for log in logs:
            log_list.append({
                "id": str(log.id),
                "file_name": log.file_name,
                "import_mode": log.import_mode,
                "template_version": log.template_version,
                "validation_passed": log.validation_passed,
                "rows_total": log.rows_total,
                "rows_imported": log.rows_imported,
                "rows_updated": log.rows_updated,
                "rows_failed": log.rows_failed,
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None,
            })

        return {
            "code": 0,
            "msg": "查询成功",
            "data": {
                "total": len(log_list),
                "logs": log_list,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get import logs: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ==================== 导入日志详情 ====================

@excel_router.get("/import-logs/{log_id}")
async def get_import_log_detail(
    log_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    获取导入日志详情.

    Args:
        log_id: 日志ID
        session: 数据库会话

    Returns:
        Dict: 导入日志详情
    """
    try:
        log_uuid = uuid.UUID(log_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="日志ID格式错误")

    try:
        from sqlalchemy import select
        from app.domain.models.excel_import_log import ExcelImportLog

        result = await session.execute(
            select(ExcelImportLog).where(ExcelImportLog.id == log_uuid)
        )
        log = result.scalar_one_or_none()

        if not log:
            raise HTTPException(status_code=404, detail="导入日志不存在")

        return {
            "code": 0,
            "msg": "查询成功",
            "data": {
                "id": str(log.id),
                "file_name": log.file_name,
                "file_path": log.file_path,
                "file_size": log.file_size,
                "import_mode": log.import_mode,
                "template_version": log.template_version,
                "validation_passed": log.validation_passed,
                "validation_errors": log.validation_errors,
                "rows_total": log.rows_total,
                "rows_imported": log.rows_imported,
                "rows_updated": log.rows_updated,
                "rows_skipped": log.rows_skipped,
                "rows_failed": log.rows_failed,
                "row_errors": log.row_errors,
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get import log detail: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ==================== 模块信息查询 ====================

@excel_router.get("/modules")
async def get_supported_modules() -> Dict[str, Any]:
    """
    获取支持的模块列表.

    Returns:
        Dict: 支持的模块列表和说明
    """
    return {
        "code": 0,
        "msg": "查询成功",
        "data": {
            "modules": [
                {
                    "name": "project",
                    "display_name": "项目",
                    "description": "项目基本信息，支持全量导出和导入",
                    "requires_project_id": False,
                },
                {
                    "name": "task",
                    "display_name": "任务",
                    "description": "项目任务数据，导入时需要指定项目ID",
                    "requires_project_id": True,
                },
                {
                    "name": "milestone",
                    "display_name": "里程碑",
                    "description": "项目里程碑数据，导入时需要指定项目ID",
                    "requires_project_id": True,
                },
                {
                    "name": "risk",
                    "display_name": "风险",
                    "description": "项目风险数据，导入时需要指定项目ID",
                    "requires_project_id": True,
                },
                {
                    "name": "cost",
                    "display_name": "成本",
                    "description": "项目成本数据，导入时需要指定项目ID",
                    "requires_project_id": True,
                },
            ],
            "import_modes": [
                {
                    "name": "full_replace",
                    "display_name": "全量替换",
                    "description": "删除旧数据，导入新数据（危险操作，谨慎使用）",
                },
                {
                    "name": "incremental_update",
                    "display_name": "增量更新",
                    "description": "根据ID判断，存在则更新，不存在则插入",
                },
                {
                    "name": "append_only",
                    "display_name": "仅追加",
                    "description": "只插入新数据，不更新已存在的数据",
                },
            ],
        },
    }