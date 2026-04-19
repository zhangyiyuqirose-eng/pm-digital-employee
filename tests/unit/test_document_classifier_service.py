"""
PM Digital Employee - Document Classifier Service Tests
项目经理数字员工系统 - 文档分类服务单元测试

v1.3.0新增：测试文档分类服务的核心功能
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.document_classifier_service import (
    DocumentClassifierService,
    ContentCategory,
    ProjectMatch,
    ClassificationResult,
    get_document_classifier_service,
)
from app.services.file_parser_service import ParsedContent, FileInfo


class TestContentCategory:
    """ContentCategory测试类."""

    def test_content_category_creation(self):
        """测试ContentCategory创建."""
        category = ContentCategory(
            document_category="project_doc",
            project_phase="execution",
            document_subtype="weekly_report",
            confidence=0.85,
            inferred_entity_types=["WeeklyReport", "Task"],
            classification_reason="文件名匹配关键词",
            keywords_matched=["周报"],
        )

        assert category.document_category == "project_doc"
        assert category.project_phase == "execution"
        assert category.document_subtype == "weekly_report"
        assert category.confidence == 0.85


class TestProjectMatch:
    """ProjectMatch测试类."""

    def test_project_match_with_project(self):
        """测试ProjectMatch有项目."""
        match = ProjectMatch(
            project_id="proj-001",
            project_name="测试项目",
            match_type="content_match",
            confidence=0.85,
            keywords=["测试项目"],
        )

        assert match.project_id == "proj-001"
        assert match.match_type == "content_match"

    def test_project_match_unknown(self):
        """测试ProjectMatch无项目."""
        match = ProjectMatch(
            project_id=None,
            project_name=None,
            match_type="unknown",
            confidence=0.0,
        )

        assert match.project_id is None
        assert match.match_type == "unknown"


class TestClassificationResult:
    """ClassificationResult测试类."""

    def test_classification_result_creation(self):
        """测试ClassificationResult创建."""
        result = ClassificationResult(
            content_category=ContentCategory(
                document_category="project_doc",
                project_phase="execution",
                document_subtype="weekly_report",
                confidence=0.85,
                inferred_entity_types=["WeeklyReport"],
                classification_reason="文件名匹配",
            ),
            project_match=ProjectMatch(
                project_id="proj-001",
                project_name="测试项目",
                match_type="content_match",
                confidence=0.85,
            ),
            combined_confidence=0.80,
        )

        assert result.combined_confidence == 0.80
        assert result.content_category.document_subtype == "weekly_report"


class TestDocumentClassifierService:
    """DocumentClassifierService测试类."""

    @pytest.fixture
    def service(self) -> DocumentClassifierService:
        """创建DocumentClassifierService实例."""
        return DocumentClassifierService()

    def test_service_init(self, service: DocumentClassifierService):
        """测试服务初始化."""
        assert len(service.FILENAME_KEYWORDS) > 0
        assert len(service.EXTENSION_CATEGORIES) > 0
        assert len(service.CONTENT_KEYWORDS) > 0

    def test_filename_keywords_mapping(self, service: DocumentClassifierService):
        """测试文件名关键词映射."""
        # 周报关键词
        assert "周报" in service.FILENAME_KEYWORDS
        subtype, phase, entities = service.FILENAME_KEYWORDS["周报"]
        assert subtype == "weekly_report"
        assert phase == "execution"

        # 会议纪要关键词
        assert "会议纪要" in service.FILENAME_KEYWORDS
        subtype, phase, entities = service.FILENAME_KEYWORDS["会议纪要"]
        assert subtype == "meeting_minutes"

        # WBS关键词
        assert "WBS" in service.FILENAME_KEYWORDS

    def test_extension_categories(self, service: DocumentClassifierService):
        """测试扩展名分类."""
        assert service.EXTENSION_CATEGORIES["docx"] == "project_doc"
        assert service.EXTENSION_CATEGORIES["xlsx"] == "project_doc"
        assert service.EXTENSION_CATEGORIES["pptx"] == "management_doc"

    def test_classify_by_extension(self, service: DocumentClassifierService):
        """测试扩展名分类."""
        result = service._classify_by_extension("docx")

        assert result["document_category"] == "project_doc"
        assert result["confidence"] == 0.5

    def test_classify_by_filename_weekly_report(self, service: DocumentClassifierService):
        """测试文件名分类周报."""
        result = service._classify_by_filename("项目周报-2024-01.docx")

        assert result["matched"] is not None
        assert result["matched"]["document_subtype"] == "weekly_report"
        assert result["confidence"] == 0.85

    def test_classify_by_filename_meeting_minutes(self, service: DocumentClassifierService):
        """测试文件名分类会议纪要."""
        result = service._classify_by_filename("会议纪要-项目周会.docx")

        assert result["matched"] is not None
        assert result["matched"]["document_subtype"] == "meeting_minutes"

    def test_classify_by_filename_wbs(self, service: DocumentClassifierService):
        """测试文件名分类WBS."""
        result = service._classify_by_filename("WBS分解结构.xlsx")

        assert result["matched"] is not None
        assert result["matched"]["document_subtype"] == "wbs"

    def test_classify_by_filename_no_match(self, service: DocumentClassifierService):
        """测试文件名无匹配."""
        result = service._classify_by_filename("项目文档.docx")

        assert result["matched"] is None
        assert result["confidence"] == 0.0

    def test_classify_by_keywords(self, service: DocumentClassifierService):
        """测试内容关键词分类."""
        content = ParsedContent(
            text="本周工作总结：完成了需求评审和系统设计。下周计划：继续开发工作。",
        )

        result = service._classify_by_keywords(content)

        # 应该识别为周报相关
        assert result["document_subtype"] in ["weekly_report", "unknown"]

    def test_extract_project_keywords(self, service: DocumentClassifierService):
        """测试项目关键词提取."""
        text = "项目名称：数字化转型项目\n项目编号：PRJ-2024-001"

        keywords = service._extract_project_keywords(text)

        assert len(keywords) > 0
        assert any("项目" in kw or "PRJ" in kw for kw in keywords)

    def test_get_entity_types(self, service: DocumentClassifierService):
        """测试获取实体类型."""
        entities = service._get_entity_types("weekly_report")

        assert "WeeklyReport" in entities

        entities = service._get_entity_types("meeting_minutes")

        assert "MeetingMinutes" in entities

        entities = service._get_entity_types("unknown")

        assert entities == []


class TestDocumentClassifierServiceFactory:
    """服务工厂测试."""

    def test_get_document_classifier_service(self):
        """测试获取服务实例."""
        service1 = get_document_classifier_service()
        service2 = get_document_classifier_service()

        # 应该返回同一个实例（单例）
        assert service1 is service2


class TestDocumentClassifierIntegration:
    """分类服务集成测试."""

    @pytest.fixture
    def service(self) -> DocumentClassifierService:
        """创建DocumentClassifierService实例."""
        return DocumentClassifierService()

    @pytest.mark.asyncio
    async def test_classify_weekly_report_document(self, service: DocumentClassifierService):
        """测试分类周报文档."""
        content = ParsedContent(
            text="本周工作总结：完成了需求评审。下周计划：继续开发。",
            tables=[],
        )

        file_info = FileInfo(
            path="/tmp/test.docx",
            name="项目周报-2024-01.docx",
            extension="docx",
            size=1024,
        )

        user_context = {
            "chat_type": "p2p",
            "user_id": "user-001",
        }

        result = await service.classify(content, file_info, user_context)

        assert result.content_category.document_subtype == "weekly_report"
        assert result.content_category.document_category == "project_doc"
        assert result.combined_confidence > 0.5

    @pytest.mark.asyncio
    async def test_classify_meeting_minutes_document(self, service: DocumentClassifierService):
        """测试分类会议纪要文档."""
        content = ParsedContent(
            text="会议时间：2024-01-15\n参会人员：张三、李四\n会议内容：讨论项目进度",
        )

        file_info = FileInfo(
            path="/tmp/test.docx",
            name="会议纪要-项目周会.docx",
            extension="docx",
            size=1024,
        )

        result = await service.classify(content, file_info)

        assert result.content_category.document_subtype == "meeting_minutes"

    @pytest.mark.asyncio
    async def test_classify_wbs_document(self, service: DocumentClassifierService):
        """测试分类WBS文档."""
        content = ParsedContent(
            text="WBS分解结构",
            tables=[
                MagicMock(headers=["任务名称", "工期", "前置任务"]),
            ],
        )

        file_info = FileInfo(
            path="/tmp/test.xlsx",
            name="WBS分解.xlsx",
            extension="xlsx",
            size=2048,
        )

        result = await service.classify(content, file_info)

        assert result.content_category.document_subtype == "wbs"