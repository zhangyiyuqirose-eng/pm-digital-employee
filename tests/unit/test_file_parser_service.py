"""
PM Digital Employee - File Parser Service Tests
项目经理数字员工系统 - 文件解析服务单元测试

v1.3.0新增：测试文件解析服务的核心功能
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch

from app.services.file_parser_service import (
    FileParserService,
    FileInfo,
    ParsedContent,
    TableData,
    UnsupportedFormatError,
    FileParseError,
    OCRServiceError,
    get_file_parser_service,
)


class TestFileInfo:
    """FileInfo测试类."""

    def test_file_info_creation(self):
        """测试FileInfo创建."""
        file_info = FileInfo(
            path="/tmp/test.docx",
            name="test.docx",
            extension="docx",
            size=1024,
        )

        assert file_info.path == "/tmp/test.docx"
        assert file_info.name == "test.docx"
        assert file_info.extension == "docx"
        assert file_info.size == 1024

    def test_file_info_with_content_type(self):
        """测试FileInfo带content_type."""
        file_info = FileInfo(
            path="/tmp/test.pdf",
            name="test.pdf",
            extension="pdf",
            size=2048,
            content_type="application/pdf",
        )

        assert file_info.content_type == "application/pdf"


class TestParsedContent:
    """ParsedContent测试类."""

    def test_parsed_content_creation(self):
        """测试ParsedContent创建."""
        content = ParsedContent(
            text="这是测试文本",
            tables=[],
            structure={"type": "text"},
        )

        assert content.text == "这是测试文本"
        assert len(content.tables) == 0

    def test_parsed_content_to_dict(self):
        """测试ParsedContent转字典."""
        content = ParsedContent(
            text="测试",
            tables=[TableData(headers=["A", "B"], rows=[["1", "2"]])],
            structure={"type": "docx"},
        )

        result = content.to_dict()

        assert result["text"] == "测试"
        assert len(result["tables"]) == 1
        assert result["tables"][0]["headers"] == ["A", "B"]

    def test_parsed_content_get_text_summary(self):
        """测试文本摘要."""
        long_text = "A" * 3000
        content = ParsedContent(text=long_text)

        summary = content.get_text_summary(100)

        assert len(summary) <= 103  # 100 + "..."

    def test_parsed_content_get_key_content(self):
        """测试关键内容提取."""
        content = ParsedContent(
            text="测试文本",
            tables=[
                TableData(headers=["任务", "状态"], rows=[["任务A", "进行中"]]),
            ],
        )

        key_content = content.get_key_content()

        assert "测试文本" in key_content
        assert "任务" in key_content


class TestTableData:
    """TableData测试类."""

    def test_table_data_creation(self):
        """测试TableData创建."""
        table = TableData(
            headers=["列1", "列2", "列3"],
            rows=[
                ["值1", "值2", "值3"],
                ["值4", "值5", "值6"],
            ],
            title="测试表格",
        )

        assert table.headers == ["列1", "列2", "列3"]
        assert len(table.rows) == 2
        assert table.title == "测试表格"


class TestFileParserService:
    """FileParserService测试类."""

    @pytest.fixture
    def service(self) -> FileParserService:
        """创建FileParserService实例."""
        return FileParserService()

    def test_service_init(self, service: FileParserService):
        """测试服务初始化."""
        assert len(service.SUPPORTED_EXTENSIONS) > 0
        assert "docx" in service.SUPPORTED_EXTENSIONS
        assert "pdf" in service.SUPPORTED_EXTENSIONS
        assert "xlsx" in service.SUPPORTED_EXTENSIONS

    def test_is_supported(self, service: FileParserService):
        """测试格式支持检查."""
        assert service.is_supported("docx") == True
        assert service.is_supported("pdf") == True
        assert service.is_supported("xlsx") == True
        assert service.is_supported("xyz") == False  # 不支持的格式

    def test_is_image(self, service: FileParserService):
        """测试图片检查."""
        assert service.is_image("jpg") == True
        assert service.is_image("png") == True
        assert service.is_image("docx") == False

    def test_unsupported_format_error(self, service: FileParserService):
        """测试不支持的格式."""
        file_info = FileInfo(
            path="/tmp/test.xyz",
            name="test.xyz",
            extension="xyz",
            size=100,
        )

        # 应该抛出UnsupportedFormatError
        with pytest.raises(UnsupportedFormatError):
            import asyncio
            asyncio.run(service.parse(file_info))

    def test_file_size_limit(self, service: FileParserService):
        """测试文件大小限制."""
        large_size = 100 * 1024 * 1024  # 100MB
        file_info = FileInfo(
            path="/tmp/test.docx",
            name="test.docx",
            extension="docx",
            size=large_size,
        )

        # 应该抛出FileParseError
        with pytest.raises(FileParseError):
            import asyncio
            asyncio.run(service.parse(file_info))

    @pytest.mark.asyncio
    async def test_parse_text_file(self, service: FileParserService):
        """测试解析文本文件."""
        # 创建临时文本文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("这是测试文本内容")
            temp_path = f.name

        try:
            file_info = FileInfo(
                path=temp_path,
                name="test.txt",
                extension="txt",
                size=os.path.getsize(temp_path),
            )

            content = await service.parse(file_info)

            assert content.text == "这是测试文本内容"
            assert content.structure["type"] == "text"

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_parse_markdown_file(self, service: FileParserService):
        """测试解析Markdown文件."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# 标题\n\n这是内容")
            temp_path = f.name

        try:
            file_info = FileInfo(
                path=temp_path,
                name="test.md",
                extension="md",
                size=os.path.getsize(temp_path),
            )

            content = await service.parse(file_info)

            assert "# 标题" in content.text

        finally:
            os.unlink(temp_path)


class TestFileParserServiceFactory:
    """服务工厂测试."""

    def test_get_file_parser_service(self):
        """测试获取服务实例."""
        service1 = get_file_parser_service()
        service2 = get_file_parser_service()

        # 应该返回同一个实例（单例）
        assert service1 is service2


class TestUnsupportedFormatError:
    """UnsupportedFormatError测试."""

    def test_error_creation(self):
        """测试错误创建."""
        error = UnsupportedFormatError("xyz")

        assert error.code == "unsupported_format"
        assert "xyz" in error.message
        assert error.details["extension"] == "xyz"


class TestFileParseError:
    """FileParseError测试."""

    def test_error_creation(self):
        """测试错误创建."""
        error = FileParseError(
            message="解析失败",
            details={"file": "test.docx"},
        )

        assert error.code == "file_parse_error"
        assert error.message == "解析失败"


class TestOCRServiceError:
    """OCRServiceError测试."""

    def test_error_creation(self):
        """测试错误创建."""
        error = OCRServiceError("OCR识别失败")

        assert error.code == "ocr_service_error"
        assert "OCR" in error.message