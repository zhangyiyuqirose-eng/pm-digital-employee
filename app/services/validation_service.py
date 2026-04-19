"""
PM Digital Employee - Validation Service
项目经理数字员工系统 - 统一数据校验服务

提供统一的数据校验入口，支持三种录入方式共用：
1. 飞书卡片录入
2. Excel模板导入
3. 飞书在线表格同步

使用Pydantic进行数据校验。
"""

import os
import re
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ValidationError, Field

from app.core.validation_config import (
    ModuleValidationConfig,
    FieldValidationConfig,
    BusinessRuleConfig,
    get_module_config,
    get_all_module_names,
)
from app.core.exceptions import ParameterValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ValidationResult(BaseModel):
    """校验结果模型."""

    is_valid: bool                            # 是否校验通过
    errors: List[Dict[str, Any]] = []         # 错误列表
    warnings: List[Dict[str, Any]] = []       # 警告列表
    validated_data: Optional[Dict[str, Any]] = None  # 校验后的数据


class FieldError(BaseModel):
    """字段错误详情."""

    field_name: str                           # 字段名称
    display_name: str                         # 字段显示名称
    error_type: str                           # 错误类型：required, type, range, enum, pattern, business
    message: str                              # 错误消息
    value: Optional[Any] = None               # 错误值


class TemplateFormatResult(BaseModel):
    """模板格式校验结果."""

    is_valid: bool                            # 是否校验通过
    missing_columns: List[str] = []           # 缺失的列
    extra_columns: List[str] = []             # 多余的列
    column_order_match: bool = True           # 列顺序是否匹配


class ValidationService:
    """
    统一数据校验服务.

    提供模板格式校验、必填字段校验、数据类型校验、业务规则校验等能力。
    三种录入方式共用，确保数据一致性。
    """

    def __init__(self) -> None:
        """
        初始化校验服务.

        加载各模块的校验配置。
        """
        self._module_configs: Dict[str, ModuleValidationConfig] = {}
        self._load_configs()

    def _load_configs(self) -> None:
        """
        加载所有模块的校验配置.
        """
        for module_name in get_all_module_names():
            config = get_module_config(module_name)
            if config:
                self._module_configs[module_name] = config
                logger.debug(f"Loaded validation config for module: {module_name}")

    def validate_template_format(
        self,
        file_path: str,
        module: str,
    ) -> TemplateFormatResult:
        """
        校验模板格式.

        检查Excel模板文件的列名、列顺序是否符合预期。

        Args:
            file_path: 模板文件路径
            module: 模块名称（project/task/milestone/risk/cost）

        Returns:
            TemplateFormatResult: 模板格式校验结果
        """
        if not os.path.exists(file_path):
            logger.error(f"Template file not found: {file_path}")
            return TemplateFormatResult(
                is_valid=False,
                missing_columns=[],
                extra_columns=[],
                column_order_match=False,
            )

        config = self._module_configs.get(module)
        if not config:
            logger.warning(f"No validation config for module: {module}")
            return TemplateFormatResult(
                is_valid=True,
                missing_columns=[],
                extra_columns=[],
                column_order_match=True,
            )

        # 获取预期的列名列表（中文显示名）
        expected_columns = [f.display_name for f in config.fields]

        try:
            # 根据文件类型读取列名
            actual_columns = self._extract_columns_from_file(file_path)

            # 比较列名
            missing = [col for col in expected_columns if col not in actual_columns]
            extra = [col for col in actual_columns if col not in expected_columns]

            # 检查列顺序
            order_match = True
            if not missing and not extra:
                # 完全匹配时检查顺序
                filtered_expected = [col for col in expected_columns if col in actual_columns]
                filtered_actual = [col for col in actual_columns if col in expected_columns]
                order_match = filtered_expected == filtered_actual

            result = TemplateFormatResult(
                is_valid=len(missing) == 0,
                missing_columns=missing,
                extra_columns=extra,
                column_order_match=order_match,
            )

            logger.info(
                f"Template format validation: module={module}, valid={result.is_valid}, "
                f"missing={len(missing)}, extra={len(extra)}"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to validate template format: {e}")
            return TemplateFormatResult(
                is_valid=False,
                missing_columns=[],
                extra_columns=[],
                column_order_match=False,
            )

    def _extract_columns_from_file(self, file_path: str) -> List[str]:
        """
        从文件中提取列名.

        根据文件类型（Excel/CSV）读取第一行作为列名。

        Args:
            file_path: 文件路径

        Returns:
            List[str]: 列名列表
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext in [".xlsx", ".xls"]:
            # Excel文件处理
            try:
                import pandas as pd
                df = pd.read_excel(file_path, nrows=0)
                return list(df.columns)
            except ImportError:
                logger.warning("pandas not installed, cannot parse Excel columns")
                return []
        elif ext in [".csv"]:
            # CSV文件处理
            try:
                import pandas as pd
                df = pd.read_csv(file_path, nrows=0)
                return list(df.columns)
            except ImportError:
                # 简单CSV解析
                with open(file_path, "r", encoding="utf-8") as f:
                    first_line = f.readline()
                    return first_line.strip().split(",") if first_line else []
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return []

    def validate_required_fields(
        self,
        data: Dict[str, Any],
        module_config: ModuleValidationConfig,
    ) -> List[FieldError]:
        """
        校验必填字段.

        检查数据中是否包含所有必填字段，且值不为空。

        Args:
            data: 待校验的数据字典
            module_config: 模块校验配置

        Returns:
            List[FieldError]: 必填字段错误列表
        """
        errors: List[FieldError] = []

        for field_config in module_config.fields:
            if field_config.required:
                field_name = field_config.field_name
                display_name = field_config.display_name

                # 检查字段是否存在
                if field_name not in data:
                    errors.append(FieldError(
                        field_name=field_name,
                        display_name=display_name,
                        error_type="required",
                        message=f"必填字段 '{display_name}' 缺失",
                    ))
                    continue

                # 检查值是否为空
                value = data[field_name]
                if self._is_empty(value):
                    errors.append(FieldError(
                        field_name=field_name,
                        display_name=display_name,
                        error_type="required",
                        message=f"必填字段 '{display_name}' 值为空",
                        value=value,
                    ))

        return errors

    def _is_empty(self, value: Any) -> bool:
        """
        检查值是否为空.

        Args:
            value: 待检查的值

        Returns:
            bool: 是否为空
        """
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        return False

    def validate_data_types(
        self,
        data: Dict[str, Any],
        field_configs: List[FieldValidationConfig],
    ) -> List[FieldError]:
        """
        校验数据类型.

        检查各字段的数据类型是否符合预期。

        Args:
            data: 待校验的数据字典
            field_configs: 字段校验配置列表

        Returns:
            List[FieldError]: 数据类型错误列表
        """
        errors: List[FieldError] = []

        for field_config in field_configs:
            field_name = field_config.field_name
            display_name = field_config.display_name
            expected_type = field_config.field_type

            # 跳过不存在或为空的字段（非必填）
            if field_name not in data or self._is_empty(data[field_name]):
                continue

            value = data[field_name]

            # 类型校验
            type_valid, converted_value = self._check_and_convert_type(
                value, expected_type, field_name
            )

            if not type_valid:
                errors.append(FieldError(
                    field_name=field_name,
                    display_name=display_name,
                    error_type="type",
                    message=f"字段 '{display_name}' 类型错误，期望 {expected_type}，实际为 {type(value).__name__}",
                    value=value,
                ))
            else:
                # 类型正确，更新数据中的值（转换为正确类型）
                data[field_name] = converted_value

            # 范围校验
            range_errors = self._validate_field_range(
                value=converted_value if type_valid else value,
                field_config=field_config,
                field_name=field_name,
                display_name=display_name,
            )
            errors.extend(range_errors)

            # 枚举校验
            if field_config.enum_values:
                enum_error = self._validate_enum_value(
                    value=converted_value if type_valid else value,
                    enum_values=field_config.enum_values,
                    field_name=field_name,
                    display_name=display_name,
                )
                if enum_error:
                    errors.append(enum_error)

        return errors

    def _check_and_convert_type(
        self,
        value: Any,
        expected_type: str,
        field_name: str,
    ) -> Tuple[bool, Any]:
        """
        检查并转换数据类型.

        Args:
            value: 待检查的值
            expected_type: 期望的类型
            field_name: 字段名称

        Returns:
            Tuple[bool, Any]: (是否类型正确, 转换后的值)
        """
        try:
            if expected_type == "str":
                return True, str(value)

            elif expected_type == "int":
                if isinstance(value, bool):
                    return False, value
                return True, int(float(value))

            elif expected_type == "float":
                return True, float(value)

            elif expected_type == "date":
                if isinstance(value, date):
                    return True, value
                if isinstance(value, str):
                    # 支持多种日期格式
                    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"]:
                        try:
                            return True, datetime.strptime(value, fmt).date()
                        except ValueError:
                            continue
                    return False, value
                return False, value

            elif expected_type == "datetime":
                if isinstance(value, datetime):
                    return True, value
                if isinstance(value, str):
                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
                        try:
                            return True, datetime.strptime(value, fmt)
                        except ValueError:
                            continue
                    return False, value
                return False, value

            elif expected_type == "bool":
                if isinstance(value, bool):
                    return True, value
                if isinstance(value, str):
                    if value.lower() in ["true", "是", "yes", "1"]:
                        return True, True
                    if value.lower() in ["false", "否", "no", "0"]:
                        return True, False
                if isinstance(value, (int, float)):
                    return True, bool(value)
                return False, value

            elif expected_type == "enum":
                # 枚举类型本质是字符串
                return True, str(value)

            else:
                logger.warning(f"Unknown type: {expected_type}")
                return True, value

        except (ValueError, TypeError) as e:
            logger.debug(f"Type conversion failed for {field_name}: {e}")
            return False, value

    def _validate_field_range(
        self,
        value: Any,
        field_config: FieldValidationConfig,
        field_name: str,
        display_name: str,
    ) -> List[FieldError]:
        """
        校验字段范围约束.

        Args:
            value: 待校验的值
            field_config: 字段校验配置
            field_name: 字段名称
            display_name: 字段显示名称

        Returns:
            List[FieldError]: 范围错误列表
        """
        errors: List[FieldError] = []

        # 数值范围校验
        if field_config.field_type in ["int", "float"]:
            if field_config.min_value is not None:
                try:
                    num_value = float(value)
                    if num_value < field_config.min_value:
                        errors.append(FieldError(
                            field_name=field_name,
                            display_name=display_name,
                            error_type="range",
                            message=f"字段 '{display_name}' 值 {num_value} 小于最小值 {field_config.min_value}",
                            value=value,
                        ))
                except (ValueError, TypeError):
                    pass

            if field_config.max_value is not None:
                try:
                    num_value = float(value)
                    if num_value > field_config.max_value:
                        errors.append(FieldError(
                            field_name=field_name,
                            display_name=display_name,
                            error_type="range",
                            message=f"字段 '{display_name}' 值 {num_value} 大于最大值 {field_config.max_value}",
                            value=value,
                        ))
                except (ValueError, TypeError):
                    pass

        # 字符串长度校验
        elif field_config.field_type == "str":
            str_value = str(value)
            if field_config.min_length is not None:
                if len(str_value) < field_config.min_length:
                    errors.append(FieldError(
                        field_name=field_name,
                        display_name=display_name,
                        error_type="range",
                        message=f"字段 '{display_name}' 长度 {len(str_value)} 小于最小长度 {field_config.min_length}",
                        value=value,
                    ))

            if field_config.max_length is not None:
                if len(str_value) > field_config.max_length:
                    errors.append(FieldError(
                        field_name=field_name,
                        display_name=display_name,
                        error_type="range",
                        message=f"字段 '{display_name}' 长度 {len(str_value)} 大于最大长度 {field_config.max_length}",
                        value=value,
                    ))

        return errors

    def _validate_enum_value(
        self,
        value: Any,
        enum_values: List[str],
        field_name: str,
        display_name: str,
    ) -> Optional[FieldError]:
        """
        校验枚举值.

        Args:
            value: 待校验的值
            enum_values: 允许的枚举值列表
            field_name: 字段名称
            display_name: 字段显示名称

        Returns:
            Optional[FieldError]: 枚举错误，如果校验通过则返回None
        """
        str_value = str(value).lower()
        lower_enum_values = [v.lower() for v in enum_values]

        if str_value not in lower_enum_values:
            # 中文显示名匹配尝试
            if value not in enum_values and str_value not in lower_enum_values:
                return FieldError(
                    field_name=field_name,
                    display_name=display_name,
                    error_type="enum",
                    message=f"字段 '{display_name}' 值 '{value}' 不在允许的枚举值中: {enum_values}",
                    value=value,
                )

        return None

    def validate_business_rules(
        self,
        data: Dict[str, Any],
        module: str,
    ) -> List[FieldError]:
        """
        校验业务规则.

        检查数据是否符合业务规则约束。

        Args:
            data: 待校验的数据字典
            module: 模块名称

        Returns:
            List[FieldError]: 业务规则错误列表
        """
        errors: List[FieldError] = []

        config = self._module_configs.get(module)
        if not config:
            logger.warning(f"No validation config for module: {module}")
            return errors

        for rule in config.business_rules:
            rule_errors = self._apply_business_rule(data, rule)
            errors.extend(rule_errors)

        return errors

    def _apply_business_rule(
        self,
        data: Dict[str, Any],
        rule: BusinessRuleConfig,
    ) -> List[FieldError]:
        """
        应用单个业务规则.

        Args:
            data: 待校验的数据字典
            rule: 业务规则配置

        Returns:
            List[FieldError]: 规则错误列表
        """
        errors: List[FieldError] = []

        if rule.rule_type == "compare":
            # 字段比较规则（如：结束日期 >= 开始日期）
            errors.extend(self._apply_compare_rule(data, rule))

        elif rule.rule_type == "range":
            # 范围规则（如：金额 >= 0）
            errors.extend(self._apply_range_rule(data, rule))

        elif rule.rule_type == "custom":
            # 自定义规则（预留扩展）
            logger.debug(f"Custom rule {rule.rule_name} skipped")

        return errors

    def _apply_compare_rule(
        self,
        data: Dict[str, Any],
        rule: BusinessRuleConfig,
    ) -> List[FieldError]:
        """
        应用字段比较规则.

        Args:
            data: 待校验的数据字典
            rule: 业务规则配置

        Returns:
            List[FieldError]: 比较规则错误列表
        """
        errors: List[FieldError] = []

        if len(rule.fields) < 2:
            return errors

        field1_name = rule.fields[0]
        field2_name = rule.fields[1]

        # 跳过不存在或为空的字段
        if field1_name not in data or field2_name not in data:
            return errors

        value1 = data[field1_name]
        value2 = data[field2_name]

        if self._is_empty(value1) or self._is_empty(value2):
            return errors

        operator = rule.params.get("operator", ">=") if rule.params else ">="
        allow_equal = rule.params.get("allow_equal", True) if rule.params else True

        try:
            # 尝试比较
            if isinstance(value1, (date, datetime)) and isinstance(value2, (date, datetime)):
                if operator == ">=":
                    if not (value2 >= value1):
                        errors.append(FieldError(
                            field_name=field2_name,
                            display_name=rule.description,
                            error_type="business",
                            message=rule.description,
                            value=value2,
                        ))
                elif operator == ">":
                    if not (value2 > value1):
                        errors.append(FieldError(
                            field_name=field2_name,
                            display_name=rule.description,
                            error_type="business",
                            message=rule.description,
                            value=value2,
                        ))
            else:
                # 数值比较
                num1 = float(value1)
                num2 = float(value2)

                if operator == ">=":
                    if not (num2 >= num1):
                        errors.append(FieldError(
                            field_name=field2_name,
                            display_name=rule.description,
                            error_type="business",
                            message=rule.description,
                            value=num2,
                        ))
                elif operator == ">":
                    if not (num2 > num1):
                        errors.append(FieldError(
                            field_name=field2_name,
                            display_name=rule.description,
                            error_type="business",
                            message=rule.description,
                            value=num2,
                        ))

        except (ValueError, TypeError) as e:
            logger.debug(f"Compare rule failed: {e}")

        return errors

    def _apply_range_rule(
        self,
        data: Dict[str, Any],
        rule: BusinessRuleConfig,
    ) -> List[FieldError]:
        """
        应用范围规则.

        Args:
            data: 待校验的数据字典
            rule: 业务规则配置

        Returns:
            List[FieldError]: 范围规则错误列表
        """
        errors: List[FieldError] = []

        params = rule.params or {}
        min_val = params.get("min")
        max_val = params.get("max")

        for field_name in rule.fields:
            if field_name not in data:
                continue

            value = data[field_name]
            if self._is_empty(value):
                continue

            try:
                num_value = float(value)

                if min_val is not None and num_value < min_val:
                    errors.append(FieldError(
                        field_name=field_name,
                        display_name=rule.description,
                        error_type="business",
                        message=rule.description,
                        value=num_value,
                    ))

                if max_val is not None and num_value > max_val:
                    errors.append(FieldError(
                        field_name=field_name,
                        display_name=rule.description,
                        error_type="business",
                        message=rule.description,
                        value=num_value,
                    ))

            except (ValueError, TypeError) as e:
                logger.debug(f"Range rule failed for {field_name}: {e}")

        return errors

    def validate_all(
        self,
        data: Dict[str, Any],
        module: str,
    ) -> ValidationResult:
        """
        统一校验入口.

        执行完整的校验流程：必填字段、数据类型、业务规则。

        Args:
            data: 待校验的数据字典
            module: 模块名称（project/task/milestone/risk/cost）

        Returns:
            ValidationResult: 校验结果
        """
        # 复制数据以避免修改原始数据
        validated_data = data.copy()

        # 获取模块配置
        config = self._module_configs.get(module)
        if not config:
            logger.warning(f"No validation config for module: {module}")
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[{
                    "field_name": "module",
                    "message": f"模块 '{module}' 无校验配置，跳过校验",
                }],
                validated_data=validated_data,
            )

        # 执行各阶段校验
        all_errors: List[Dict[str, Any]] = []

        # 1. 必填字段校验
        required_errors = self.validate_required_fields(validated_data, config)
        all_errors.extend([e.dict() for e in required_errors])

        # 2. 数据类型校验（会更新validated_data中的值）
        type_errors = self.validate_data_types(validated_data, config.fields)
        all_errors.extend([e.dict() for e in type_errors])

        # 3. 业务规则校验
        if len(all_errors) == 0:  # 只有基础校验通过才执行业务规则校验
            business_errors = self.validate_business_rules(validated_data, module)
            all_errors.extend([e.dict() for e in business_errors])

        # 构建结果
        result = ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=[],
            validated_data=validated_data if len(all_errors) == 0 else None,
        )

        logger.info(
            f"Validation completed: module={module}, valid={result.is_valid}, "
            f"errors={len(result.errors)}"
        )

        return result

    def validate_batch(
        self,
        data_list: List[Dict[str, Any]],
        module: str,
    ) -> List[ValidationResult]:
        """
        批量校验数据.

        对多条数据进行统一校验。

        Args:
            data_list: 待校验的数据列表
            module: 模块名称

        Returns:
            List[ValidationResult]: 校验结果列表
        """
        results: List[ValidationResult] = []

        for idx, data in enumerate(data_list):
            result = self.validate_all(data, module)

            # 如果有错误，添加行号信息
            if not result.is_valid:
                for error in result.errors:
                    error["row_index"] = idx + 1

            results.append(result)

        # 统计结果
        valid_count = sum(1 for r in results if r.is_valid)
        logger.info(
            f"Batch validation completed: module={module}, "
            f"total={len(data_list)}, valid={valid_count}, invalid={len(data_list) - valid_count}"
        )

        return results

    def get_validation_summary(
        self,
        results: List[ValidationResult],
    ) -> Dict[str, Any]:
        """
        获取校验结果摘要.

        Args:
            results: 校验结果列表

        Returns:
            Dict: 校验摘要信息
        """
        total = len(results)
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = total - valid_count

        # 错误类型统计
        error_type_counts: Dict[str, int] = {}
        error_field_counts: Dict[str, int] = {}

        for result in results:
            if not result.is_valid:
                for error in result.errors:
                    error_type = error.get("error_type", "unknown")
                    error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1

                    field_name = error.get("field_name", "unknown")
                    error_field_counts[field_name] = error_field_counts.get(field_name, 0) + 1

        return {
            "total": total,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "success_rate": valid_count / total if total > 0 else 0,
            "error_type_counts": error_type_counts,
            "error_field_counts": error_field_counts,
        }