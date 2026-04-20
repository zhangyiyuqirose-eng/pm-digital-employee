"""
PM Digital Employee - Validation Service Tests
项目经理数字员工系统 - 校验服务测试

测试覆盖：
1. 模板格式校验
2. 必填字段校验
3. 数据类型校验
4. 范围校验
5. 枚举值校验
6. 批量校验
7. 业务规则校验
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import date, datetime
import os

from app.services.validation_service import (
    ValidationService,
    ValidationResult,
    FieldError,
    TemplateFormatResult,
)


# ==================== Fixture ====================

@pytest.fixture
def validation_service() -> ValidationService:
    """创建校验服务实例."""
    return ValidationService()


@pytest.fixture
def mock_module_config() -> MagicMock:
    """Mock模块校验配置."""
    config = MagicMock()
    config.display_name = "项目"
    config.fields = []

    # 添加模拟字段配置
    field1 = MagicMock()
    field1.field_name = "name"
    field1.display_name = "项目名称"
    field1.field_type = "str"
    field1.required = True
    field1.min_length = 2
    field1.max_length = 100
    field1.enum_values = None
    field1.min_value = None
    field1.max_value = None

    field2 = MagicMock()
    field2.field_name = "progress"
    field2.display_name = "进度"
    field2.field_type = "int"
    field2.required = False
    field2.enum_values = None
    field2.min_value = 0
    field2.max_value = 100

    field3 = MagicMock()
    field3.field_name = "status"
    field3.display_name = "状态"
    field3.field_type = "enum"
    field3.required = True
    field3.enum_values = ["进行中", "已完成", "暂停"]

    field4 = MagicMock()
    field4.field_name = "start_date"
    field4.display_name = "开始日期"
    field4.field_type = "date"
    field4.required = True

    config.fields = [field1, field2, field3, field4]
    return config


# ==================== Template Format Validation Tests ====================

class TestTemplateFormatValidation:
    """模板格式校验测试."""

    def test_validate_template_file_not_found(
        self,
        validation_service: ValidationService,
    ) -> None:
        """测试文件不存在时返回失败结果."""
        result = validation_service.validate_template_format(
            file_path="/nonexistent/file.xlsx",
            module="project",
        )

        assert result.is_valid is False
        assert result.column_order_match is False

    @patch("os.path.exists", return_value=True)
    @patch("pandas.read_excel")
    def test_validate_template_format_valid(
        self,
        mock_read_excel: MagicMock,
        mock_exists: MagicMock,
        validation_service: ValidationService,
    ) -> None:
        """测试模板格式校验成功."""
        # Mock pandas返回预期列名
        mock_df = MagicMock()
        mock_df.columns = ["项目名称", "进度", "状态", "开始日期"]
        mock_read_excel.return_value = mock_df

        # Mock模块配置
        with patch.object(
            validation_service,
            "_module_configs",
            {"project": mock_module_config()},
        ):
            result = validation_service.validate_template_format(
                file_path="/test/template.xlsx",
                module="project",
            )

            # 验证结果
            assert result.is_valid is True
            assert len(result.missing_columns) == 0
            assert len(result.extra_columns) == 0

    @patch("os.path.exists", return_value=True)
    @patch("pandas.read_excel")
    def test_validate_template_format_missing_columns(
        self,
        mock_read_excel: MagicMock,
        mock_exists: MagicMock,
        validation_service: ValidationService,
    ) -> None:
        """测试模板缺少必填列."""
        # Mock pandas返回缺少列名
        mock_df = MagicMock()
        mock_df.columns = ["项目名称", "进度"]  # 缺少状态、开始日期
        mock_read_excel.return_value = mock_df

        mock_config = mock_module_config()
        mock_config.display_name = "项目"

        with patch.object(
            validation_service,
            "_module_configs",
            {"project": mock_config},
        ):
            result = validation_service.validate_template_format(
                file_path="/test/template.xlsx",
                module="project",
            )

            assert result.is_valid is False
            assert "状态" in result.missing_columns
            assert "开始日期" in result.missing_columns


# ==================== Required Field Validation Tests ====================

class TestRequiredFieldValidation:
    """必填字段校验测试."""

    def test_validate_required_fields_all_present(
        self,
        validation_service: ValidationService,
        mock_module_config: MagicMock,
    ) -> None:
        """测试所有必填字段都存在."""
        data = {
            "name": "测试项目",
            "status": "进行中",
            "start_date": "2026-01-01",
            "progress": 50,
        }

        errors = validation_service.validate_required_fields(
            data=data,
            module_config=mock_module_config,
        )

        assert len(errors) == 0

    def test_validate_required_fields_missing(
        self,
        validation_service: ValidationService,
        mock_module_config: MagicMock,
    ) -> None:
        """测试缺少必填字段."""
        data = {
            "progress": 50,  # 非必填
            # 缺少 name, status, start_date
        }

        errors = validation_service.validate_required_fields(
            data=data,
            module_config=mock_module_config,
        )

        assert len(errors) == 3

        # 验证错误类型
        error_types = [e.error_type for e in errors]
        assert all(et == "required" for et in error_types)

        # 验证缺失字段名
        field_names = [e.field_name for e in errors]
        assert "name" in field_names
        assert "status" in field_names
        assert "start_date" in field_names

    def test_validate_required_fields_empty_value(
        self,
        validation_service: ValidationService,
        mock_module_config: MagicMock,
    ) -> None:
        """测试必填字段值为空."""
        data = {
            "name": "",  # 空字符串
            "status": "进行中",
            "start_date": None,  # None值
            "progress": 50,
        }

        errors = validation_service.validate_required_fields(
            data=data,
            module_config=mock_module_config,
        )

        assert len(errors) == 2

        # 验证空值错误
        empty_fields = [e.field_name for e in errors]
        assert "name" in empty_fields
        assert "start_date" in empty_fields

    def test_is_empty_detection(
        self,
        validation_service: ValidationService,
    ) -> None:
        """测试空值检测逻辑."""
        # None为空
        assert validation_service._is_empty(None) is True

        # 空字符串为空
        assert validation_service._is_empty("") is True
        assert validation_service._is_empty("   ") is True

        # 有值不为空
        assert validation_service._is_empty("test") is False
        assert validation_service._is_empty(0) is False
        assert validation_service._is_empty(False) is False


# ==================== Data Type Validation Tests ====================

class TestDataTypeValidation:
    """数据类型校验测试."""

    def test_validate_string_type(
        self,
        validation_service: ValidationService,
        mock_module_config: MagicMock,
    ) -> None:
        """测试字符串类型校验."""
        data = {"name": "测试项目"}

        errors = validation_service.validate_data_types(
            data=data,
            field_configs=mock_module_config.fields[:1],  # 只校验name字段
        )

        assert len(errors) == 0
        assert isinstance(data["name"], str)

    def test_validate_int_type_conversion(
        self,
        validation_service: ValidationService,
    ) -> None:
        """测试整数类型转换."""
        field_config = MagicMock()
        field_config.field_name = "progress"
        field_config.display_name = "进度"
        field_config.field_type = "int"
        field_config.required = False
        field_config.enum_values = None
        field_config.min_value = 0
        field_config.max_value = 100

        # 测试字符串转整数
        data = {"progress": "50"}
        errors = validation_service.validate_data_types(
            data=data,
            field_configs=[field_config],
        )

        assert len(errors) == 0
        assert data["progress"] == 50
        assert isinstance(data["progress"], int)

    def test_validate_float_type_conversion(
        self,
        validation_service: ValidationService,
    ) -> None:
        """测试浮点数类型转换."""
        field_config = MagicMock()
        field_config.field_name = "amount"
        field_config.display_name = "金额"
        field_config.field_type = "float"
        field_config.required = False
        field_config.enum_values = None
        field_config.min_value = None
        field_config.max_value = None

        data = {"amount": "1000.50"}
        errors = validation_service.validate_data_types(
            data=data,
            field_configs=[field_config],
        )

        assert len(errors) == 0
        assert data["amount"] == 1000.50
        assert isinstance(data["amount"], float)

    def test_validate_date_type_conversion(
        self,
        validation_service: ValidationService,
    ) -> None:
        """测试日期类型转换."""
        field_config = MagicMock()
        field_config.field_name = "start_date"
        field_config.display_name = "开始日期"
        field_config.field_type = "date"
        field_config.required = False
        field_config.enum_values = None
        field_config.min_value = None
        field_config.max_value = None

        # 测试YYYY-MM-DD格式
        data = {"start_date": "2026-01-15"}
        errors = validation_service.validate_data_types(
            data=data,
            field_configs=[field_config],
        )

        assert len(errors) == 0
        assert isinstance(data["start_date"], date)
        assert data["start_date"] == date(2026, 1, 15)

    def test_validate_bool_type_conversion(
        self,
        validation_service: ValidationService,
    ) -> None:
        """测试布尔类型转换."""
        field_config = MagicMock()
        field_config.field_name = "is_active"
        field_config.display_name = "是否激活"
        field_config.field_type = "bool"
        field_config.required = False
        field_config.enum_values = None
        field_config.min_value = None
        field_config.max_value = None

        # 测试字符串"是"转True
        data = {"is_active": "是"}
        errors = validation_service.validate_data_types(
            data=data,
            field_configs=[field_config],
        )

        assert len(errors) == 0
        assert data["is_active"] is True

        # 测试字符串"否"转False
        data2 = {"is_active": "否"}
        errors2 = validation_service.validate_data_types(
            data=data2,
            field_configs=[field_config],
        )

        assert len(errors2) == 0
        assert data2["is_active"] is False

    def test_validate_invalid_type(
        self,
        validation_service: ValidationService,
    ) -> None:
        """测试无效类型."""
        field_config = MagicMock()
        field_config.field_name = "progress"
        field_config.display_name = "进度"
        field_config.field_type = "int"
        field_config.required = False
        field_config.enum_values = None
        field_config.min_value = 0
        field_config.max_value = 100

        # 测试无效整数
        data = {"progress": "not_a_number"}
        errors = validation_service.validate_data_types(
            data=data,
            field_configs=[field_config],
        )

        assert len(errors) == 1
        assert errors[0].error_type == "type"
        assert "进度" in errors[0].message


# ==================== Range Validation Tests ====================

class TestRangeValidation:
    """范围校验测试."""

    def test_validate_int_range_valid(
        self,
        validation_service: ValidationService,
    ) -> None:
        """测试整数范围校验成功."""
        field_config = MagicMock()
        field_config.field_name = "progress"
        field_config.display_name = "进度"
        field_config.field_type = "int"
        field_config.min_value = 0
        field_config.max_value = 100
        field_config.enum_values = None

        data = {"progress": 50}

        errors = validation_service.validate_data_types(
            data=data,
            field_configs=[field_config],
        )

        assert len(errors) == 0

    def test_validate_int_range_exceed_max(
        self,
        validation_service: ValidationService,
    ) -> None:
        """测试整数超出最大值."""
        field_config = MagicMock()
        field_config.field_name = "progress"
        field_config.display_name = "进度"
        field_config.field_type = "int"
        field_config.min_value = 0
        field_config.max_value = 100
        field_config.enum_values = None

        data = {"progress": 150}

        errors = validation_service.validate_data_types(
            data=data,
            field_configs=[field_config],
        )

        assert len(errors) == 1
        assert errors[0].error_type == "range"

    def test_validate_int_range_below_min(
        self,
        validation_service: ValidationService,
    ) -> None:
        """测试整数低于最小值."""
        field_config = MagicMock()
        field_config.field_name = "progress"
        field_config.display_name = "进度"
        field_config.field_type = "int"
        field_config.min_value = 0
        field_config.max_value = 100
        field_config.enum_values = None

        data = {"progress": -10}

        errors = validation_service.validate_data_types(
            data=data,
            field_configs=[field_config],
        )

        assert len(errors) == 1
        assert errors[0].error_type == "range"


# ==================== Enum Validation Tests ====================

class TestEnumValidation:
    """枚举值校验测试."""

    def test_validate_enum_valid(
        self,
        validation_service: ValidationService,
        mock_module_config: MagicMock,
    ) -> None:
        """测试枚举值校验成功."""
        data = {"status": "进行中"}

        # 只校验status字段
        status_field = mock_module_config.fields[2]
        errors = validation_service.validate_data_types(
            data=data,
            field_configs=[status_field],
        )

        assert len(errors) == 0

    def test_validate_enum_invalid(
        self,
        validation_service: ValidationService,
        mock_module_config: MagicMock,
    ) -> None:
        """测试枚举值无效."""
        data = {"status": "未知状态"}

        status_field = mock_module_config.fields[2]
        errors = validation_service.validate_data_types(
            data=data,
            field_configs=[status_field],
        )

        assert len(errors) == 1
        assert errors[0].error_type == "enum"


# ==================== Batch Validation Tests ====================

class TestBatchValidation:
    """批量校验测试."""

    @patch.object(ValidationService, "validate_single")
    def test_validate_batch(
        self,
        mock_validate_single: MagicMock,
        validation_service: ValidationService,
    ) -> None:
        """测试批量校验."""
        # Mock单个校验结果
        mock_validate_single.return_value = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            validated_data={"name": "测试"},
        )

        data_list = [
            {"name": "项目1"},
            {"name": "项目2"},
            {"name": "项目3"},
        ]

        results = validation_service.validate_batch(
            data_list=data_list,
            module="project",
        )

        assert len(results) == 3
        assert mock_validate_single.call_count == 3


# ==================== Edge Cases Tests ====================

class TestEdgeCases:
    """边界情况测试."""

    def test_validate_empty_data(
        self,
        validation_service: ValidationService,
        mock_module_config: MagicMock,
    ) -> None:
        """测试空数据校验."""
        data = {}

        errors = validation_service.validate_required_fields(
            data=data,
            module_config=mock_module_config,
        )

        # 必填字段缺失
        assert len(errors) >= 3

    def test_validate_extra_fields(
        self,
        validation_service: ValidationService,
        mock_module_config: MagicMock,
    ) -> None:
        """测试额外字段不影响校验."""
        data = {
            "name": "测试项目",
            "status": "进行中",
            "start_date": "2026-01-01",
            "extra_field": "额外数据",  # 不在配置中
        }

        errors = validation_service.validate_required_fields(
            data=data,
            module_config=mock_module_config,
        )

        # 额外字段不影响必填校验
        assert len(errors) == 0

    def test_validate_whitespace_value(
        self,
        validation_service: ValidationService,
    ) -> None:
        """测试空白字符值."""
        field_config = MagicMock()
        field_config.field_name = "name"
        field_config.display_name = "名称"
        field_config.field_type = "str"
        field_config.required = False
        field_config.min_length = 2
        field_config.max_length = 100
        field_config.enum_values = None
        field_config.min_value = None
        field_config.max_value = None

        data = {"name": "   测试项目   "}

        errors = validation_service.validate_data_types(
            data=data,
            field_configs=[field_config],
        )

        # 字符串校验成功
        assert len(errors) == 0


# ==================== Integration Tests ====================

class TestValidationIntegration:
    """集成测试."""

    @patch("app.core.validation_config.get_module_config")
    def test_full_validation_flow(
        self,
        mock_get_config: MagicMock,
        validation_service: ValidationService,
    ) -> None:
        """测试完整校验流程."""
        # Mock模块配置
        mock_config = mock_module_config()
        mock_get_config.return_value = mock_config

        # 测试数据
        data = {
            "name": "测试项目",
            "status": "进行中",
            "start_date": "2026-01-01",
            "progress": 50,
        }

        # 执行完整校验（假设有validate_single方法）
        with patch.object(
            validation_service,
            "_module_configs",
            {"project": mock_config},
        ):
            # 必填校验
            required_errors = validation_service.validate_required_fields(
                data=data,
                module_config=mock_config,
            )

            # 类型校验
            type_errors = validation_service.validate_data_types(
                data=data,
                field_configs=mock_config.fields,
            )

            # 综合判断
            all_errors = required_errors + type_errors
            assert len(all_errors) == 0