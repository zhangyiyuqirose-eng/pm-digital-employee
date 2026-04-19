"""
PM Digital Employee - Document Parse Service
项目经理数字员工系统 - 文档解析核心服务

v1.3.0新增：协调文件下载、解析、分类、提取、入库全流程
"""

import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.exceptions import ServiceError
from app.domain.enums import DocumentParseStatus, DocumentImportStatus, DataSource
from app.domain.models.document_parse_record import DocumentParseRecord
from app.services.file_parser_service import (
    FileParserService,
    FileInfo,
    ParsedContent,
    UnsupportedFormatError,
    FileParseError,
    OCRServiceError,
    get_file_parser_service,
)
from app.services.document_classifier_service import (
    DocumentClassifierService,
    ClassificationResult,
    get_document_classifier_service,
)
from app.services.data_extractor_service import (
    DataExtractorService,
    ExtractionResult,
    get_data_extractor_service,
)
from app.services.data_import_service import (
    DataImportService,
    ImportResult,
    get_data_import_service,
)
from app.integrations.lark.client import LarkClient

logger = get_logger(__name__)


class DocumentParseException(ServiceError):
    """文档解析异常."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(code=code, message=message, details=details or {})


@dataclass
class DocumentParseResult:
    """文档解析结果."""

    success: bool                                  # 是否成功
    parse_record_id: Optional[str] = None          # 解析记录ID
    confidence: float = 0.0                        # 置信度
    imported_count: int = 0                        # 入库数量
    requires_confirmation: bool = False            # 是否需要确认
    error: Optional[Exception] = None              # 错误信息

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "success": self.success,
            "parse_record_id": self.parse_record_id,
            "confidence": self.confidence,
            "imported_count": self.imported_count,
            "requires_confirmation": self.requires_confirmation,
            "error": str(self.error) if self.error else None,
        }


class DocumentParseService:
    """
    文档解析核心服务.

    协调文件下载、解析、分类、提取、入库全流程：
    1. 文件下载（飞书API）
    2. 文件解析（FileParserService）
    3. 文档分类（DocumentClassifierService）
    4. 信息提取（DataExtractorService）
    5. 置信度评估
    6. 数据入库（DataImportService）
    7. 结果反馈（飞书卡片）
    """

    # 置信度阈值
    CONFIDENCE_THRESHOLD_AUTO = 0.95      # >=95% 自动入库，发送成功通知
    CONFIDENCE_THRESHOLD_NOTIFY = 0.80    # >=80% 自动入库，发送确认通知
    CONFIDENCE_THRESHOLD_CONFIRM = 0.60   # >=60% 发送待确认卡片
    CONFIDENCE_THRESHOLD_MANUAL = 0.60    # <60% 需人工审核

    def __init__(self, session: AsyncSession) -> None:
        """初始化文档解析服务."""
        self.session = session
        self.file_parser = get_file_parser_service()
        self.classifier = get_document_classifier_service()
        self.extractor = get_data_extractor_service()
        self.lark_client = None  # 将在需要时初始化

    async def process_document(
        self,
        file_key: str,
        file_name: str,
        file_type: str,
        sender_id: str,
        chat_id: str,
        chat_type: str,
        message_id: str,
        file_size: int = 0,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> DocumentParseResult:
        """
        处理文档完整流程.

        Args:
            file_key: 飞书文件Key
            file_name: 文件名
            file_type: 文件类型（file/image）
            sender_id: 发送者飞书ID
            chat_id: 会话ID
            chat_type: 会话类型（p2p/group）
            message_id: 飞书消息ID
            file_size: 文件大小（字节）
            user_context: 用户上下文

        Returns:
            DocumentParseResult: 处理结果
        """
        logger.info(
            f"Processing document: name={file_name}, "
            f"type={file_type}, sender={sender_id}"
        )

        # 创建解析记录
        parse_record = await self._create_parse_record(
            file_key=file_key,
            file_name=file_name,
            file_type=file_type,
            sender_id=sender_id,
            chat_id=chat_id,
            chat_type=chat_type,
            message_id=message_id,
            file_size=file_size,
        )

        start_time = datetime.now(timezone.utc)

        try:
            # Step 1: 文件下载
            await self._update_status(parse_record, DocumentParseStatus.DOWNLOADING.value)
            file_info = await self._download_file(file_key, file_name, file_size)

            # Step 2: 文件解析
            await self._update_status(parse_record, DocumentParseStatus.PARSING.value)
            content = await self.file_parser.parse(file_info)
            await self._update_status(
                parse_record,
                DocumentParseStatus.PARSING.value,
                {"content_length": len(content.text), "tables": len(content.tables)},
            )

            # Step 3: 文档分类
            await self._update_status(parse_record, DocumentParseStatus.CLASSIFYING.value)
            classification = await self.classifier.classify(
                content, file_info, user_context
            )
            await self._update_classification(parse_record, classification)

            # Step 4: 信息提取
            await self._update_status(parse_record, DocumentParseStatus.EXTRACTING.value)
            extraction = await self.extractor.extract(
                content,
                classification.content_category.inferred_entity_types,
                classification.content_category.document_subtype,
            )
            await self._update_extraction(parse_record, extraction)

            # Step 5: 置信度评估
            overall_confidence = self._evaluate_confidence(classification, extraction)

            # Step 6: 数据入库
            project_id = classification.project_match.project_id
            requires_confirmation = overall_confidence < self.CONFIDENCE_THRESHOLD_NOTIFY

            if project_id and overall_confidence >= self.CONFIDENCE_THRESHOLD_CONFIRM:
                await self._update_status(parse_record, DocumentParseStatus.IMPORTING.value)

                if not requires_confirmation:
                    # 自动入库
                    import_result = await self._import_data(
                        extraction, project_id, user_context or {}
                    )
                    await self._update_import_result(parse_record, import_result)
                else:
                    # 需要确认，暂不入库
                    parse_record.requires_confirmation = True
                    parse_record.import_status = DocumentImportStatus.PENDING.value

            else:
                # 无项目关联或置信度过低，需要确认
                parse_record.requires_confirmation = True
                parse_record.import_status = DocumentImportStatus.PENDING.value
                requires_confirmation = True

            # 更新完成状态
            await self._update_status(parse_record, DocumentParseStatus.COMPLETED.value)
            parse_record.extraction_confidence = overall_confidence

            # 计算处理时间
            processing_time = int(
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            )
            parse_record.processing_time_ms = processing_time

            await self.session.commit()

            # 构建结果
            result = DocumentParseResult(
                success=True,
                parse_record_id=str(parse_record.id),
                confidence=overall_confidence,
                imported_count=parse_record.imported_entity_ids
                    and len(json.loads(parse_record.imported_entity_ids))
                    or 0,
                requires_confirmation=requires_confirmation,
            )

            logger.info(
                f"Document processed: record_id={parse_record.id}, "
                f"confidence={overall_confidence}, "
                f"requires_confirmation={requires_confirmation}"
            )

            return result

        except UnsupportedFormatError as e:
            await self._handle_error(parse_record, "unsupported_format", str(e))
            return DocumentParseResult(success=False, error=e)

        except FileParseError as e:
            await self._handle_error(parse_record, "parse_error", str(e))
            return DocumentParseResult(success=False, error=e)

        except OCRServiceError as e:
            await self._handle_error(parse_record, "ocr_error", str(e))
            return DocumentParseResult(success=False, error=e)

        except Exception as e:
            logger.error(f"Document parse failed: {e}")
            await self._handle_error(parse_record, "unknown_error", str(e))
            return DocumentParseResult(success=False, error=e)

        finally:
            # 清理临时文件
            if file_info and file_info.path and os.path.exists(file_info.path):
                try:
                    os.remove(file_info.path)
                except Exception:
                    pass

    async def confirm_parse(
        self,
        parse_id: uuid.UUID,
        action: str,
        edited_data: Optional[Dict[str, Any]] = None,
        project_id: Optional[uuid.UUID] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> DocumentParseResult:
        """
        确认文档解析结果.

        Args:
            parse_id: 解析记录ID
            action: 确认动作（confirm/edit/cancel）
            edited_data: 编辑后的数据
            project_id: 用户选择的项目ID
            user_context: 用户上下文

        Returns:
            DocumentParseResult: 确认结果
        """
        logger.info(f"Confirming parse: id={parse_id}, action={action}")

        # 获取解析记录
        parse_record = await self._get_parse_record(parse_id)
        if not parse_record:
            raise DocumentParseException(
                code="record_not_found",
                message="解析记录不存在",
            )

        if not parse_record.requires_confirmation:
            raise DocumentParseException(
                code="already_confirmed",
                message="该记录已确认或无需确认",
            )

        # 更新确认信息
        parse_record.confirmed_by_id = user_context.get("user_id")
        parse_record.confirmed_by_name = user_context.get("user_name")
        parse_record.confirmed_at = datetime.now(timezone.utc)
        parse_record.confirmation_action = action

        if action == "cancel":
            # 取消处理
            parse_record.parse_status = DocumentParseStatus.CANCELLED.value
            parse_record.import_status = DocumentImportStatus.SKIPPED.value
            await self.session.commit()

            return DocumentParseResult(
                success=True,
                parse_record_id=str(parse_record.id),
                imported_count=0,
            )

        # 确认或编辑
        # 使用编辑数据或原始提取数据
        final_data = edited_data or json.loads(parse_record.extracted_data or "{}")
        final_project_id = project_id or parse_record.confirmed_project_id or parse_record.inferred_project_id

        if not final_project_id:
            return DocumentParseResult(
                success=False,
                error=DocumentParseException(
                    code="project_required",
                    message="请选择关联项目",
                ),
            )

        # 执行入库
        extraction = ExtractionResult(
            entities=[],  # 需要从final_data构建
            overall_confidence=parse_record.extraction_confidence or 0.5,
            missing_required_fields=[],
        )

        # 构建实体列表
        if final_data:
            entities = self._build_entities_from_data(final_data)
            extraction.entities = entities

        import_service = get_data_import_service(self.session)
        import_result = await import_service.import_all(
            entities=extraction.entities,
            project_id=final_project_id,
            user_context=user_context or {},
        )

        # 更新记录
        await self._update_import_result(parse_record, import_result)
        parse_record.confirmed_project_id = final_project_id
        parse_record.parse_status = DocumentParseStatus.COMPLETED.value
        parse_record.requires_confirmation = False

        await self.session.commit()

        return DocumentParseResult(
            success=True,
            parse_record_id=str(parse_record.id),
            confidence=parse_record.extraction_confidence or 0.5,
            imported_count=import_result.imported_count,
        )

    async def get_parse_record(
        self,
        parse_id: uuid.UUID,
    ) -> Optional[DocumentParseRecord]:
        """获取解析记录."""
        return await self._get_parse_record(parse_id)

    async def get_pending_confirmations(
        self,
        user_id: str,
    ) -> List[DocumentParseRecord]:
        """获取用户待确认列表."""
        stmt = select(DocumentParseRecord).where(
            and_(
                DocumentParseRecord.requires_confirmation == True,
                DocumentParseRecord.sender_id == user_id,
                DocumentParseRecord.parse_status == DocumentParseStatus.COMPLETED.value,
            )
        ).order_by(DocumentParseRecord.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_parse_history(
        self,
        project_id: Optional[uuid.UUID] = None,
        sender_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取解析历史."""
        conditions = []

        if project_id:
            conditions.append(DocumentParseRecord.inferred_project_id == project_id)

        if sender_id:
            conditions.append(DocumentParseRecord.sender_id == sender_id)

        if status:
            conditions.append(DocumentParseRecord.parse_status == status)

        if start_date:
            conditions.append(DocumentParseRecord.created_at >= start_date)

        if end_date:
            conditions.append(DocumentParseRecord.created_at <= end_date)

        stmt = select(DocumentParseRecord).where(
            and_(*conditions) if conditions else True
        ).order_by(DocumentParseRecord.created_at.desc())

        # 分页
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.session.execute(stmt)
        records = list(result.scalars().all())

        # 获取总数
        count_stmt = select(DocumentParseRecord).where(
            and_(*conditions) if conditions else True
        )
        count_result = await self.session.execute(count_stmt)
        total = len(list(count_result.scalars().all()))

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "records": records,
        }

    # ==================== 内部方法 ====================

    async def _create_parse_record(
        self,
        file_key: str,
        file_name: str,
        file_type: str,
        sender_id: str,
        chat_id: str,
        chat_type: str,
        message_id: str,
        file_size: int,
    ) -> DocumentParseRecord:
        """创建解析记录."""
        # 提取扩展名
        extension = file_name.rsplit(".", 1)[-1] if "." in file_name else ""

        record = DocumentParseRecord(
            file_key=file_key,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            file_extension=extension,
            sender_id=sender_id,
            chat_id=chat_id,
            chat_type=chat_type,
            message_id=message_id,
            parse_status=DocumentParseStatus.PENDING.value,
            import_status=DocumentImportStatus.PENDING.value,
            parser_version="v1.0.0",
        )

        self.session.add(record)
        await self.session.flush()

        logger.info(f"Created parse record: id={record.id}")
        return record

    async def _update_status(
        self,
        record: DocumentParseRecord,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """更新解析状态."""
        record.parse_status = status
        record.updated_at = datetime.now(timezone.utc)

        await self.session.flush()

        logger.debug(f"Updated parse status: id={record.id}, status={status}")

    async def _update_classification(
        self,
        record: DocumentParseRecord,
        classification: ClassificationResult,
    ) -> None:
        """更新分类结果."""
        record.document_category = classification.content_category.document_category
        record.document_subtype = classification.content_category.document_subtype
        record.project_phase = classification.content_category.project_phase
        record.classification_confidence = classification.content_category.confidence

        if classification.project_match.project_id:
            record.inferred_project_id = uuid.UUID(classification.project_match.project_id)

        record.inferred_project_name = classification.project_match.project_name
        record.project_match_type = classification.project_match.match_type

        record.entity_types = json.dumps(
            classification.content_category.inferred_entity_types
        )

        await self.session.flush()

    async def _update_extraction(
        self,
        record: DocumentParseRecord,
        extraction: ExtractionResult,
    ) -> None:
        """更新提取结果."""
        record.extracted_data = json.dumps(
            [e.data for e in extraction.entities]
        )
        record.extraction_confidence = extraction.overall_confidence
        record.field_confidences = json.dumps(
            {e.entity_type: e.field_confidence for e in extraction.entities}
        )
        record.missing_fields = json.dumps(extraction.missing_required_fields)

        await self.session.flush()

    async def _update_import_result(
        self,
        record: DocumentParseRecord,
        import_result: ImportResult,
    ) -> None:
        """更新入库结果."""
        if import_result.is_success():
            record.import_status = DocumentImportStatus.SUCCESS.value
        elif import_result.is_partial_success():
            record.import_status = DocumentImportStatus.PARTIAL.value
        else:
            record.import_status = DocumentImportStatus.FAILED.value

        record.imported_entity_ids = json.dumps([
            e.entity_id for e in import_result.imported_entities if e.entity_id
        ])

        record.conflict_ids = json.dumps([
            e.conflict_id for e in import_result.conflicts if e.conflict_id
        ])

        await self.session.flush()

    async def _handle_error(
        self,
        record: DocumentParseRecord,
        error_type: str,
        error_message: str,
    ) -> None:
        """处理错误."""
        record.parse_status = DocumentParseStatus.FAILED.value
        record.error_type = error_type
        record.error_message = error_message

        await self.session.commit()

        logger.error(f"Parse error: id={record.id}, type={error_type}, message={error_message}")

    def _evaluate_confidence(
        self,
        classification: ClassificationResult,
        extraction: ExtractionResult,
    ) -> float:
        """评估总体置信度."""
        # 综合分类置信度和提取置信度
        classification_weight = 0.3
        extraction_weight = 0.5
        project_match_weight = 0.2

        confidence = (
            classification.content_category.confidence * classification_weight +
            extraction.overall_confidence * extraction_weight +
            classification.project_match.confidence * project_match_weight
        )

        return min(confidence, 1.0)

    async def _download_file(
        self,
        file_key: str,
        file_name: str,
        file_size: int,
    ) -> FileInfo:
        """Download Lark file."""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="doc_parse_")
        temp_path = os.path.join(temp_dir, file_name)

        try:
            # Import Lark client
            from app.integrations.lark.client import get_lark_client

            lark_client = get_lark_client()

            logger.info(f"Downloading file from Lark: {file_key}")

            # Download file content
            file_content = await lark_client.download_file(file_key)

            # Write to temp file
            with open(temp_path, "wb") as f:
                f.write(file_content)

            # Get actual file size
            actual_size = os.path.getsize(temp_path)

            # Return FileInfo
            extension = file_name.rsplit(".", 1)[-1] if "." in file_name else ""

            logger.info(
                f"File downloaded successfully: {file_name}",
                extra={"size": actual_size, "path": temp_path},
            )

            return FileInfo(
                path=temp_path,
                name=file_name,
                extension=extension,
                size=actual_size,
            )

        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            # Clean up temp dir on error
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass
            raise

    async def _import_data(
        self,
        extraction: ExtractionResult,
        project_id: str,
        user_context: Dict[str, Any],
    ) -> ImportResult:
        """执行数据入库."""
        import_service = get_data_import_service(self.session)

        entities = [
            {
                "entity_type": e.entity_type,
                "data": e.data,
                "field_confidence": e.field_confidence,
            }
            for e in extraction.entities
        ]

        return await import_service.import_all(
            entities=entities,
            project_id=uuid.UUID(project_id),
            user_context=user_context,
        )

    async def _get_parse_record(
        self,
        parse_id: uuid.UUID,
    ) -> Optional[DocumentParseRecord]:
        """获取解析记录."""
        stmt = select(DocumentParseRecord).where(
            DocumentParseRecord.id == parse_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _build_entities_from_data(
        self,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """从数据构建实体列表."""
        entities = []

        if "extracted_entities" in data:
            for item in data["extracted_entities"]:
                entities.append({
                    "entity_type": item.get("entity_type"),
                    "data": item.get("data", {}),
                })
        else:
            # 单一实体
            entity_type = data.get("entity_type", "unknown")
            entities.append({
                "entity_type": entity_type,
                "data": data,
            })

        return entities


# 服务工厂（需要session）
def get_document_parse_service(session: AsyncSession) -> DocumentParseService:
    """获取文档解析服务实例."""
    return DocumentParseService(session)