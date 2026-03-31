"""
PM Digital Employee - Output Parser
项目经理数字员工系统 - LLM结构化输出解析

解析LLM生成的结构化输出，支持JSON、Markdown表格等格式。
"""

import json
import re
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, ValidationError

from app.ai.schemas import OutputValidationResult, StructuredOutputSchema
from app.core.exceptions import ErrorCode, OutputParseError
from app.core.logging import get_logger

logger = get_logger(__name__)


class StructuredOutputParser:
    """
    结构化输出解析器.

    解析LLM生成的结构化输出，支持：
    - JSON格式
    - Markdown代码块
    - Markdown表格
    - 自定义格式
    """

    def __init__(self) -> None:
        """初始化解析器."""
        self._json_pattern = re.compile(
            r"```(?:json)?\s*\n?(.*?)\n?```",
            re.DOTALL,
        )
        self._markdown_table_pattern = re.compile(
            r"\|(.+)\|\n\|[-\s|:]+\|\n((?:\|.+\|\n?)+)",
            re.MULTILINE,
        )

    def parse_json(
        self,
        content: str,
        schema: Optional[Dict[str, Any]] = None,
    ) -> OutputValidationResult:
        """
        解析JSON输出.

        Args:
            content: LLM输出内容
            schema: JSON Schema（可选）

        Returns:
            OutputValidationResult: 解析结果
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 提取JSON
        json_str = self.extract_json(content)

        if json_str is None:
            # 尝试直接解析
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as e:
                errors.append(f"JSON解析失败: {str(e)}")
                return OutputValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                )
        else:
            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError as e:
                errors.append(f"JSON解析失败: {str(e)}")
                return OutputValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                )

        # Schema校验
        if schema:
            validation_errors = self._validate_against_schema(parsed, schema)
            errors.extend(validation_errors)

        return OutputValidationResult(
            is_valid=len(errors) == 0,
            parsed_output=parsed,
            errors=errors,
            warnings=warnings,
        )

    def extract_json(
        self,
        content: str,
    ) -> Optional[str]:
        """
        从内容中提取JSON字符串.

        Args:
            content: 内容

        Returns:
            Optional[str]: JSON字符串或None
        """
        # 尝试匹配代码块中的JSON
        match = self._json_pattern.search(content)
        if match:
            return match.group(1).strip()

        # 尝试找到JSON对象
        start_idx = content.find("{")
        if start_idx != -1:
            # 找到匹配的结束括号
            bracket_count = 0
            for i in range(start_idx, len(content)):
                if content[i] == "{":
                    bracket_count += 1
                elif content[i] == "}":
                    bracket_count -= 1
                    if bracket_count == 0:
                        return content[start_idx:i + 1]

        # 尝试找到JSON数组
        start_idx = content.find("[")
        if start_idx != -1:
            bracket_count = 0
            for i in range(start_idx, len(content)):
                if content[i] == "[":
                    bracket_count += 1
                elif content[i] == "]":
                    bracket_count -= 1
                    if bracket_count == 0:
                        return content[start_idx:i + 1]

        return None

    def parse_markdown_table(
        self,
        content: str,
    ) -> OutputValidationResult:
        """
        解析Markdown表格.

        Args:
            content: LLM输出内容

        Returns:
            OutputValidationResult: 解析结果
        """
        errors: List[str] = []
        warnings: List[str] = []

        match = self._markdown_table_pattern.search(content)
        if not match:
            errors.append("未找到Markdown表格")
            return OutputValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
            )

        try:
            # 解析表头
            header_line = match.group(1)
            headers = [h.strip() for h in header_line.split("|") if h.strip()]

            # 解析数据行
            data_lines = match.group(2).strip().split("\n")
            rows = []
            for line in data_lines:
                cells = [c.strip() for c in line.split("|") if c.strip()]
                if cells:
                    rows.append(dict(zip(headers, cells)))

            return OutputValidationResult(
                is_valid=True,
                parsed_output={
                    "headers": headers,
                    "rows": rows,
                },
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            errors.append(f"表格解析失败: {str(e)}")
            return OutputValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
            )

    def parse_pydantic(
        self,
        content: str,
        model: Type[BaseModel],
    ) -> OutputValidationResult:
        """
        解析为Pydantic模型.

        Args:
            content: LLM输出内容
            model: Pydantic模型类

        Returns:
            OutputValidationResult: 解析结果
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 先解析JSON
        json_result = self.parse_json(content)

        if not json_result.is_valid:
            return json_result

        try:
            # 转换为Pydantic模型
            instance = model.model_validate(json_result.parsed_output)

            return OutputValidationResult(
                is_valid=True,
                parsed_output=instance.model_dump(),
                errors=errors,
                warnings=warnings,
            )

        except ValidationError as e:
            for error in e.errors():
                errors.append(f"{error['loc']}: {error['msg']}")

            return OutputValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
            )

    def parse_list(
        self,
        content: str,
    ) -> OutputValidationResult:
        """
        解析列表输出.

        Args:
            content: LLM输出内容

        Returns:
            OutputValidationResult: 解析结果
        """
        errors: List[str] = []
        warnings: List[str] = []
        items: List[str] = []

        # 匹配编号列表
        numbered_pattern = re.compile(r"^\s*\d+[.、)]\s*(.+)$", re.MULTILINE)
        numbered_matches = numbered_pattern.findall(content)
        if numbered_matches:
            items.extend(numbered_matches)

        # 匹配符号列表
        bullet_pattern = re.compile(r"^\s*[-*•]\s*(.+)$", re.MULTILINE)
        bullet_matches = bullet_pattern.findall(content)
        if bullet_matches:
            items.extend(bullet_matches)

        if not items:
            # 尝试按行分割
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            items = lines

        return OutputValidationResult(
            is_valid=len(items) > 0,
            parsed_output={"items": items},
            errors=errors,
            warnings=warnings,
        )

    def parse_key_value(
        self,
        content: str,
        delimiter: str = ":",
    ) -> OutputValidationResult:
        """
        解析键值对输出.

        Args:
            content: LLM输出内容
            delimiter: 分隔符

        Returns:
            OutputValidationResult: 解析结果
        """
        errors: List[str] = []
        warnings: List[str] = []
        result: Dict[str, str] = {}

        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if delimiter in line:
                parts = line.split(delimiter, 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    result[key] = value

        return OutputValidationResult(
            is_valid=len(result) > 0,
            parsed_output=result,
            errors=errors,
            warnings=warnings,
        )

    def _validate_against_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> List[str]:
        """
        根据Schema校验数据.

        Args:
            data: 数据
            schema: JSON Schema

        Returns:
            List[str]: 错误列表
        """
        errors: List[str] = []

        # 检查必填字段
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        for field in required:
            if field not in data:
                errors.append(f"缺少必填字段: {field}")

        # 检查字段类型
        for field, value in data.items():
            if field in properties:
                field_schema = properties[field]
                field_type = field_schema.get("type", "string")

                if not self._check_type(value, field_type):
                    errors.append(f"字段 '{field}' 类型错误，期望 {field_type}")

        return errors

    def _check_type(
        self,
        value: Any,
        expected_type: str,
    ) -> bool:
        """
        检查值类型.

        Args:
            value: 值
            expected_type: 期望类型

        Returns:
            bool: 是否匹配
        """
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected = type_mapping.get(expected_type)
        if expected is None:
            return True

        return isinstance(value, expected)


class IntentOutputParser(StructuredOutputParser):
    """
    意图识别输出解析器.

    专门解析意图识别的LLM输出。
    """

    def parse_intent_output(
        self,
        content: str,
    ) -> Dict[str, Any]:
        """
        解析意图识别输出.

        Args:
            content: LLM输出

        Returns:
            Dict: 解析后的意图结果
        """
        result = self.parse_json(content)

        if result.is_valid and result.parsed_output:
            return result.parsed_output

        # 尝试从文本中提取
        return self._extract_intent_from_text(content)

    def _extract_intent_from_text(
        self,
        content: str,
    ) -> Dict[str, Any]:
        """
        从文本中提取意图信息.

        Args:
            content: 文本内容

        Returns:
            Dict: 提取的意图信息
        """
        result = {
            "intent_type": "unknown",
            "matched_skill": None,
            "confidence": 0.0,
            "extracted_params": {},
        }

        # 尝试匹配意图类型
        intent_patterns = {
            "skill_execution": r"意图[类型]?[:：]\s*skill_execution|执行技能|执行功能",
            "clarification": r"意图[类型]?[:：]\s*clarification|需要澄清",
            "unknown": r"意图[类型]?[:：]\s*unknown|未知意图",
            "rejection": r"意图[类型]?[:：]\s*rejection|拒绝",
        }

        for intent_type, pattern in intent_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                result["intent_type"] = intent_type
                break

        # 尝试匹配Skill名称
        skill_match = re.search(
            r"(?:matched_skill|skill|技能)[:：]\s*(\w+)",
            content,
            re.IGNORECASE,
        )
        if skill_match:
            result["matched_skill"] = skill_match.group(1)

        # 尝试匹配置信度
        confidence_match = re.search(
            r"(?:confidence|置信度)[:：]\s*([\d.]+)",
            content,
            re.IGNORECASE,
        )
        if confidence_match:
            try:
                result["confidence"] = float(confidence_match.group(1))
            except ValueError:
                pass

        return result


class RiskOutputParser(StructuredOutputParser):
    """
    风险分析输出解析器.
    """

    def parse_risk_output(
        self,
        content: str,
    ) -> Dict[str, Any]:
        """
        解析风险分析输出.

        Args:
            content: LLM输出

        Returns:
            Dict: 解析后的风险数据
        """
        result = self.parse_json(content)

        if result.is_valid and result.parsed_output:
            return result.parsed_output

        # 尝试从文本提取
        return self._extract_risks_from_text(content)

    def _extract_risks_from_text(
        self,
        content: str,
    ) -> Dict[str, Any]:
        """从文本提取风险信息."""
        risks = []

        # 匹配风险项
        risk_pattern = re.compile(
            r"[-*•]\s*(.+?)(?:\n|$)",
            re.MULTILINE,
        )

        matches = risk_pattern.findall(content)
        for match in matches:
            risk_item = {
                "description": match.strip(),
                "level": self._detect_risk_level(match),
            }
            risks.append(risk_item)

        return {
            "risks": risks,
            "total_count": len(risks),
        }

    def _detect_risk_level(
        self,
        text: str,
    ) -> str:
        """检测风险等级."""
        if re.search(r"高|严重|紧急|critical|high", text, re.IGNORECASE):
            return "high"
        if re.search(r"中|一般|medium", text, re.IGNORECASE):
            return "medium"
        return "low"


# 全局解析器实例
_output_parser: Optional[StructuredOutputParser] = None
_intent_parser: Optional[IntentOutputParser] = None
_risk_parser: Optional[RiskOutputParser] = None


def get_output_parser() -> StructuredOutputParser:
    """获取输出解析器实例."""
    global _output_parser
    if _output_parser is None:
        _output_parser = StructuredOutputParser()
    return _output_parser


def get_intent_parser() -> IntentOutputParser:
    """获取意图解析器实例."""
    global _intent_parser
    if _intent_parser is None:
        _intent_parser = IntentOutputParser()
    return _intent_parser


def get_risk_parser() -> RiskOutputParser:
    """获取风险解析器实例."""
    global _risk_parser
    if _risk_parser is None:
        _risk_parser = RiskOutputParser()
    return _risk_parser