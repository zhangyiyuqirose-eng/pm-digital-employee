"""
PM Digital Employee - Validation Service Tests
项目经理数字员工系统 - 统一数据校验服务单元测试

测试覆盖：必填字段校验、类型转换、业务规则校验、批量校验
"""

import pytest
from datetime import date, datetime
from unittest.mock import MagicMock

from app.services.validation_service import (
    ValidationService,
    ValidationResult,
    FieldError,
)


class TestValidationService:
    """ValidationService测试类."""

    @pytest.fixture
    def service(self) -> ValidationService:
        """创建ValidationService实例."""
        return ValidationService()

    # ==================== 必填字段校验测试 ====================

    def test_validate_required_fields_missing(self, service: ValidationService):
        """测试必填字段缺失."""
        data = {"name": ""}  # name为空
        result = service.validate_all(data, "project")

        assert result.is_valid == False
        assert any(e["error_type"] == "required" for e in result.errors)

    def test_validate_required_fields_present(self, service: ValidationService):
        """测试必填字段存在."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
        }
        result = service.validate_all(data, "project")

        # 必填字段校验应通过
        assert not any(e["error_type"] == "required" for e in result.errors)

    def test_validate_optional_fields_missing(self, service: ValidationService):
        """测试可选字段缺失不影响校验."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
            # code 可选，不提供
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == True

    # ==================== 数据类型转换测试 ====================

    def test_validate_data_type_string(self, service: ValidationService):
        """测试字符串类型校验."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == True
        assert isinstance(result.validated_data.get("name"), str)

    def test_validate_data_type_float_conversion(self, service: ValidationService):
        """测试字符串转float."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
            "total_budget": "10000.50",  # 字符串转float
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == True
        assert result.validated_data["total_budget"] == 10000.50

    def test_validate_data_type_int_conversion(self, service: ValidationService):
        """测试字符串转int."""
        data = {
            "name": "测试任务",
            "project_id": "test-project-id",
            "progress": "50",  # 字符串转int
        }
        result = service.validate_all(data, "task")

        assert result.is_valid == True
        assert result.validated_data["progress"] == 50

    def test_validate_data_type_date_conversion(self, service: ValidationService):
        """测试日期类型转换."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
            "start_date": "2026-04-20",
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == True
        assert isinstance(result.validated_data["start_date"], date)

    def test_validate_data_type_date_multiple_formats(self, service: ValidationService):
        """测试多种日期格式."""
        # YYYY-MM-DD格式
        data1 = {
            "name": "测试项目",
            "project_type": "研发项目",
            "start_date": "2026/04/20",
        }
        result1 = service.validate_all(data1, "project")
        assert result1.is_valid == True

    def test_validate_data_type_invalid_float(self, service: ValidationService):
        """测试无效的float值."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
            "total_budget": "not_a_number",
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == False
        assert any(e["error_type"] == "type" for e in result.errors)

    # ==================== 枚举校验测试 ====================

    def test_validate_enum_valid_value(self, service: ValidationService):
        """测试有效的枚举值."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
            "status": "in_progress",
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == True

    def test_validate_enum_invalid_value(self, service: ValidationService):
        """测试无效的枚举值."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
            "status": "invalid_status",
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == False
        assert any(e["error_type"] == "enum" for e in result.errors)

    def test_validate_enum_required_missing(self, service: ValidationService):
        """测试必填枚举缺失."""
        data = {
            "name": "测试项目",
            # project_type 是必填枚举，缺失
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == False
        assert any(e["error_type"] == "required" for e in result.errors)

    # ==================== 范围校验测试 ====================

    def test_validate_range_within_bounds(self, service: ValidationService):
        """测试范围校验在边界内."""
        data = {
            "name": "测试任务",
            "project_id": "test-project-id",
            "progress": 50,  # 0-100范围内
        }
        result = service.validate_all(data, "task")

        assert result.is_valid == True

    def test_validate_range_below_min(self, service: ValidationService):
        """测试值低于最小范围."""
        data = {
            "name": "测试任务",
            "project_id": "test-project-id",
            "progress": -10,  # 低于0
        }
        result = service.validate_all(data, "task")

        assert result.is_valid == False
        assert any(e["error_type"] == "range" for e in result.errors)

    def test_validate_range_above_max(self, service: ValidationService):
        """测试值高于最大范围."""
        data = {
            "name": "测试任务",
            "project_id": "test-project-id",
            "progress": 150,  # 高于100
        }
        result = service.validate_all(data, "task")

        assert result.is_valid == False
        assert any(e["error_type"] == "range" for e in result.errors)

    def test_validate_budget_positive(self, service: ValidationService):
        """测试预算必须大于等于0."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
            "total_budget": -1000,  # 负数
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == False

    # ==================== 业务规则校验测试 ====================

    def test_validate_business_rule_date_compare_success(self, service: ValidationService):
        """测试业务规则日期比较（结束日期>=开始日期）."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
            "start_date": "2026-04-10",
            "end_date": "2026-04-20",  # 结束日期晚于开始日期
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == True

    def test_validate_business_rule_date_compare_failure(self, service: ValidationService):
        """测试业务规则日期比较失败（结束日期早于开始日期）."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
            "start_date": "2026-04-20",
            "end_date": "2026-04-10",  # 结束日期早于开始日期
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == False
        assert any(e["error_type"] == "business" for e in result.errors)

    def test_validate_business_rule_same_date(self, service: ValidationService):
        """测试开始日期和结束日期相同（允许相等）."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
            "start_date": "2026-04-20",
            "end_date": "2026-04-20",  # 相同日期
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == True

    # ==================== 字段长度校验测试 ====================

    def test_validate_string_length_within_bounds(self, service: ValidationService):
        """测试字符串长度在范围内."""
        data = {
            "name": "测试项目名称",  # 长度合理
            "project_type": "研发项目",
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == True

    def test_validate_string_length_exceeds_max(self, service: ValidationService):
        """测试字符串长度超出最大限制."""
        long_name = "A" * 300  # 超过200字符限制
        data = {
            "name": long_name,
            "project_type": "研发项目",
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == False
        # 长度校验的error_type是"range"而不是"length"
        assert any(e["error_type"] == "range" for e in result.errors)

    # ==================== 批量校验测试 ====================

    def test_validate_batch_all_valid(self, service: ValidationService):
        """测试批量校验全部有效."""
        data_list = [
            {"name": "项目1", "project_type": "研发项目"},
            {"name": "项目2", "project_type": "运维项目"},
        ]
        results = service.validate_batch(data_list, "project")

        assert len(results) == 2
        assert all(r.is_valid for r in results)

    def test_validate_batch_some_invalid(self, service: ValidationService):
        """测试批量校验部分无效."""
        data_list = [
            {"name": "项目1", "project_type": "研发项目"},
            {"name": "", "project_type": "研发项目"},  # name为空，无效
        ]
        results = service.validate_batch(data_list, "project")

        assert len(results) == 2
        assert results[0].is_valid == True
        assert results[1].is_valid == False

    def test_validate_batch_row_index_in_errors(self, service: ValidationService):
        """测试批量校验错误包含行索引."""
        data_list = [
            {"name": "项目1", "project_type": "研发项目"},
            {"name": "", "project_type": "研发项目"},  # 第2行
        ]
        results = service.validate_batch(data_list, "project")

        # 无效行的错误应包含row_index
        assert results[1].is_valid == False
        for error in results[1].errors:
            assert error.get("row_index") == 2

    def test_validate_batch_empty_list(self, service: ValidationService):
        """测试批量校验空列表."""
        results = service.validate_batch([], "project")

        assert len(results) == 0

    # ==================== 模块不存在测试 ====================

    def test_validate_unknown_module(self, service: ValidationService):
        """测试不存在的模块."""
        data = {"name": "测试"}
        result = service.validate_all(data, "unknown_module")

        # 未知模块跳过校验，返回warning而不是error
        assert result.is_valid == True
        assert len(result.warnings) > 0
        assert any("模块" in w.get("message", "") for w in result.warnings)

    # ==================== 不同模块校验测试 ====================

    def test_validate_task_module(self, service: ValidationService):
        """测试任务模块校验."""
        data = {
            "name": "测试任务",
            "project_id": "test-project-id",
            "priority": "high",
            "status": "pending",
        }
        result = service.validate_all(data, "task")

        assert result.is_valid == True

    def test_validate_milestone_module(self, service: ValidationService):
        """测试里程碑模块校验."""
        data = {
            "name": "测试里程碑",
            "project_id": "test-project-id",
            "planned_date": "2026-06-01",
        }
        result = service.validate_all(data, "milestone")

        assert result.is_valid == True

    def test_validate_risk_module(self, service: ValidationService):
        """测试风险模块校验."""
        data = {
            "title": "测试风险",
            "project_id": "test-project-id",
            "level": "high",
        }
        result = service.validate_all(data, "risk")

        assert result.is_valid == True

    def test_validate_risk_level_invalid(self, service: ValidationService):
        """测试风险等级无效值."""
        data = {
            "title": "测试风险",
            "project_id": "test-project-id",
            "level": "super_high",  # 无效值
        }
        result = service.validate_all(data, "risk")

        assert result.is_valid == False

    def test_validate_cost_module(self, service: ValidationService):
        """测试成本模块校验."""
        data = {
            "project_id": "test-project-id",
            "category": "labor",
            "amount": 10000.00,
        }
        result = service.validate_all(data, "cost")

        assert result.is_valid == True

    def test_validate_cost_amount_negative(self, service: ValidationService):
        """测试成本金额为负数."""
        data = {
            "project_id": "test-project-id",
            "category": "labor",
            "amount": -1000.00,
        }
        result = service.validate_all(data, "cost")

        assert result.is_valid == False

    # ==================== 校验摘要测试 ====================

    def test_get_validation_summary(self, service: ValidationService):
        """测试校验摘要生成."""
        data_list = [
            {"name": "项目1", "project_type": "研发项目"},
            {"name": "", "project_type": "研发项目"},
            {"name": "项目3", "project_type": "运维项目"},
        ]
        results = service.validate_batch(data_list, "project")
        summary = service.get_validation_summary(results)

        assert summary["total"] == 3
        assert summary["valid_count"] == 2
        assert summary["invalid_count"] == 1
        assert summary["success_rate"] == 2/3

    def test_get_validation_summary_all_valid(self, service: ValidationService):
        """测试全部有效时的摘要."""
        data_list = [
            {"name": "项目1", "project_type": "研发项目"},
            {"name": "项目2", "project_type": "运维项目"},
        ]
        results = service.validate_batch(data_list, "project")
        summary = service.get_validation_summary(results)

        assert summary["success_rate"] == 1.0
        assert summary["invalid_count"] == 0

    # ==================== ValidationResult测试 ====================

    def test_validation_result_success(self):
        """测试ValidationResult成功状态."""
        result = ValidationResult(
            is_valid=True,
            validated_data={"name": "测试"},
        )

        assert result.is_valid == True
        assert result.errors == []
        assert result.warnings == []

    def test_validation_result_failure(self):
        """测试ValidationResult失败状态."""
        errors = [{"field": "name", "error_type": "required", "message": "必填"}]
        result = ValidationResult(
            is_valid=False,
            errors=errors,
        )

        assert result.is_valid == False
        assert len(result.errors) == 1


class TestFieldError:
    """FieldError测试类."""

    def test_field_error_creation(self):
        """测试FieldError创建."""
        error = FieldError(
            field_name="name",
            display_name="项目名称",
            error_type="required",
            message="必填字段不能为空",
        )

        assert error.field_name == "name"
        assert error.error_type == "required"


class TestValidationServiceEdgeCases:
    """ValidationService边界情况测试."""

    @pytest.fixture
    def service(self) -> ValidationService:
        """创建ValidationService实例."""
        return ValidationService()

    def test_validate_null_value_for_optional_field(self, service: ValidationService):
        """测试可选字段为None."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
            "code": None,  # 可选字段为None
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == True

    def test_validate_empty_string_for_optional_field(self, service: ValidationService):
        """测试可选字段为空字符串."""
        data = {
            "name": "测试项目",
            "project_type": "研发项目",
            "code": "",  # 可选字段为空
        }
        result = service.validate_all(data, "project")

        assert result.is_valid == True

    def test_validate_whitespace_only_string(self, service: ValidationService):
        """测试仅包含空格的字符串."""
        data = {
            "name": "   ",  # 仅空格
            "project_type": "研发项目",
        }
        result = service.validate_all(data, "project")

        # name是必填字段，仅空格应被视为无效
        assert result.is_valid == False

    def test_validate_risk_probability_range(self, service: ValidationService):
        """测试风险发生概率范围（1-5）."""
        data = {
            "title": "测试风险",
            "project_id": "test-project-id",
            "level": "medium",
            "probability": 3,  # 有效范围
        }
        result = service.validate_all(data, "risk")

        assert result.is_valid == True

    def test_validate_risk_probability_out_of_range(self, service: ValidationService):
        """测试风险发生概率超出范围."""
        data = {
            "title": "测试风险",
            "project_id": "test-project-id",
            "level": "medium",
            "probability": 6,  # 超出1-5范围
        }
        result = service.validate_all(data, "risk")

        assert result.is_valid == False