"""
PM Digital Employee - Data Extractor Service
项目经理数字员工系统 - 数据提取服务

v1.3.0新增：使用LLM从文档内容提取结构化数据
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.core.exceptions import ServiceError
from app.domain.enums import TaskStatus, TaskPriority, RiskLevel, RiskStatus, ProjectStatus
from app.services.file_parser_service import ParsedContent

logger = get_logger(__name__)


class ExtractionError(ServiceError):
    """提取错误."""

    def __init__(self, message: str):
        super().__init__(
            code="extraction_error",
            message=message,
        )


@dataclass
class ExtractedEntity:
    """提取的实体."""

    entity_type: str                          # 实体类型
    data: Dict[str, Any]                      # 实体数据
    field_confidence: Dict[str, float]        # 字段置信度
    source_location: Optional[str] = None     # 来源位置
    raw_text: Optional[str] = None            # 原始文本片段


@dataclass
class ExtractionResult:
    """提取结果."""

    entities: List[ExtractedEntity]           # 提取的实体列表
    overall_confidence: float                 # 总体置信度
    missing_required_fields: List[str]        # 缺失的必填字段
    warnings: List[str] = field(default_factory=list)  # 警告信息

    def get_entities_by_type(self, entity_type: str) -> List[ExtractedEntity]:
        """按类型获取实体."""
        return [e for e in self.entities if e.entity_type == entity_type]


class DataExtractorService:
    """
    数据提取服务.

    使用LLM从文档内容提取结构化数据，支持多种实体类型。
    """

    # 实体Schema定义
    ENTITY_SCHEMAS: Dict[str, Dict[str, Any]] = {
        "Project": {
            "name": {"type": "string", "required": True, "description": "项目名称"},
            "code": {"type": "string", "required": False, "description": "项目编号"},
            "status": {"type": "enum", "values": ["draft", "pre_initiation", "initiated", "in_progress", "suspended", "completed", "closed", "archived"], "required": False},
            "start_date": {"type": "date", "required": False, "description": "开始日期"},
            "end_date": {"type": "date", "required": False, "description": "结束日期"},
            "total_budget": {"type": "float", "required": False, "description": "总预算（元）"},
            "pm_name": {"type": "string", "required": False, "description": "项目经理姓名"},
        },
        "Task": {
            "name": {"type": "string", "required": True, "description": "任务名称"},
            "status": {"type": "enum", "values": ["pending", "in_progress", "completed", "delayed", "cancelled", "blocked"], "required": False},
            "priority": {"type": "enum", "values": ["low", "medium", "high", "critical"], "required": False},
            "start_date": {"type": "date", "required": False, "description": "开始日期"},
            "end_date": {"type": "date", "required": False, "description": "结束日期"},
            "assignee_name": {"type": "string", "required": False, "description": "负责人姓名"},
            "progress": {"type": "int", "range": [0, 100], "required": False, "description": "进度百分比"},
        },
        "Milestone": {
            "name": {"type": "string", "required": True, "description": "里程碑名称"},
            "status": {"type": "enum", "values": ["planned", "in_progress", "achieved", "delayed", "cancelled"], "required": False},
            "planned_date": {"type": "date", "required": False, "description": "计划日期"},
            "actual_date": {"type": "date", "required": False, "description": "实际日期"},
            "is_key_milestone": {"type": "bool", "required": False, "description": "是否关键里程碑"},
        },
        "Risk": {
            "title": {"type": "string", "required": True, "description": "风险标题"},
            "category": {"type": "enum", "values": ["schedule", "cost", "resource", "quality", "technical", "compliance", "external"], "required": False},
            "level": {"type": "enum", "values": ["low", "medium", "high", "critical"], "required": False},
            "probability": {"type": "int", "range": [1, 5], "required": False, "description": "发生概率（1-5）"},
            "impact": {"type": "int", "range": [1, 5], "required": False, "description": "影响程度（1-5）"},
            "owner_name": {"type": "string", "required": False, "description": "负责人姓名"},
            "mitigation_plan": {"type": "string", "required": False, "description": "应对措施"},
        },
        "Cost": {
            "category": {"type": "enum", "values": ["labor", "equipment", "software", "outsourcing", "training", "travel", "other"], "required": True},
            "amount": {"type": "float", "min": 0, "required": True, "description": "金额（元）"},
            "expense_date": {"type": "date", "required": False, "description": "支出日期"},
            "description": {"type": "string", "required": False, "description": "描述"},
        },
        "WeeklyReport": {
            "report_date": {"type": "date", "required": True, "description": "周报日期"},
            "week_start": {"type": "date", "required": True, "description": "周开始日期"},
            "week_end": {"type": "date", "required": True, "description": "周结束日期"},
            "summary": {"type": "string", "required": False, "description": "本周工作总结"},
            "completed_tasks": {"type": "array", "required": False, "description": "已完成任务列表"},
            "in_progress_tasks": {"type": "array", "required": False, "description": "进行中任务列表"},
            "next_week_plan": {"type": "string", "required": False, "description": "下周计划"},
            "risks_and_issues": {"type": "string", "required": False, "description": "风险和问题"},
        },
        "MeetingMinutes": {
            "meeting_title": {"type": "string", "required": True, "description": "会议标题"},
            "meeting_date": {"type": "date", "required": True, "description": "会议日期"},
            "meeting_time": {"type": "string", "required": False, "description": "会议时间"},
            "meeting_location": {"type": "string", "required": False, "description": "会议地点"},
            "attendees": {"type": "array", "required": False, "description": "参会人员列表"},
            "content": {"type": "string", "required": True, "description": "会议内容"},
            "decisions": {"type": "array", "required": False, "description": "决议事项"},
            "action_items": {"type": "array", "required": True, "description": "待办事项"},
        },
        "WBSVersion": {
            "wbs_data": {"type": "json", "required": True, "description": "WBS树形结构数据"},
            "version_name": {"type": "string", "required": False, "description": "版本名称"},
            "description": {"type": "string", "required": False, "description": "版本说明"},
        },
    }

    # 中文状态映射
    STATUS_MAPPING: Dict[str, Dict[str, str]] = {
        "project": {
            "草稿": "draft",
            "预立项": "pre_initiation",
            "立项": "initiated",
            "进行中": "in_progress",
            "暂停": "suspended",
            "完成": "completed",
            "关闭": "closed",
            "归档": "archived",
        },
        "task": {
            "待开始": "pending",
            "待处理": "pending",
            "进行中": "in_progress",
            "已完成": "completed",
            "完成": "completed",
            "延期": "delayed",
            "取消": "cancelled",
            "阻塞": "blocked",
        },
        "milestone": {
            "计划": "planned",
            "计划中": "planned",
            "进行中": "in_progress",
            "达成": "achieved",
            "已完成": "achieved",
            "延期": "delayed",
            "取消": "cancelled",
        },
        "risk": {
            "已识别": "identified",
            "分析中": "analyzing",
            "处理中": "mitigating",
            "已解决": "resolved",
            "已接受": "accepted",
            "已关闭": "closed",
        },
        "risk_level": {
            "低": "low",
            "中": "medium",
            "高": "high",
            "严重": "critical",
        },
        "priority": {
            "低": "low",
            "中": "medium",
            "高": "high",
            "紧急": "critical",
        },
    }

    def __init__(self) -> None:
        """初始化提取服务."""
        self._llm_gateway = None  # 将在首次使用时初始化

    async def extract(
        self,
        content: ParsedContent,
        entity_types: List[str],
        document_subtype: str,
    ) -> ExtractionResult:
        """
        执行数据提取.

        Args:
            content: 解析后的文档内容
            entity_types: 目标实体类型列表
            document_subtype: 文档子类型

        Returns:
            ExtractionResult: 提取结果
        """
        logger.info(
            f"Extracting data: document_subtype={document_subtype}, "
            f"entity_types={entity_types}"
        )

        # 选择专用Prompt
        if document_subtype == "weekly_report":
            extraction_data = await self._extract_weekly_report(content)
        elif document_subtype == "meeting_minutes":
            extraction_data = await self._extract_meeting_minutes(content)
        elif document_subtype == "wbs":
            extraction_data = await self._extract_wbs(content)
        elif document_subtype == "risk_register":
            extraction_data = await self._extract_risks(content)
        else:
            extraction_data = await self._extract_generic(content, entity_types)

        # 构建提取结果
        entities = self._build_entities(extraction_data, entity_types)

        # 计算置信度
        overall_confidence = self._calculate_overall_confidence(entities)

        # 检查缺失字段
        missing_fields = self._check_missing_fields(entities, entity_types)

        result = ExtractionResult(
            entities=entities,
            overall_confidence=overall_confidence,
            missing_required_fields=missing_fields,
        )

        logger.info(
            f"Extraction completed: entities={len(entities)}, "
            f"confidence={overall_confidence}, "
            f"missing_fields={len(missing_fields)}"
        )

        return result

    async def _extract_weekly_report(self, content: ParsedContent) -> Dict[str, Any]:
        """提取周报数据."""
        # 调用专用Prompt
        prompt = self._build_weekly_report_prompt(content)

        # TODO: 调用实际LLM Gateway
        # 当前使用模拟实现
        return self._mock_weekly_report_extraction(content)

    async def _extract_meeting_minutes(self, content: ParsedContent) -> Dict[str, Any]:
        """提取会议纪要数据."""
        prompt = self._build_meeting_minutes_prompt(content)
        return self._mock_meeting_minutes_extraction(content)

    async def _extract_wbs(self, content: ParsedContent) -> Dict[str, Any]:
        """提取WBS数据."""
        # 从表格中提取WBS结构
        if content.tables:
            return self._extract_wbs_from_tables(content.tables)
        return {"wbs_data": [], "confidence": 0.3}

    async def _extract_risks(self, content: ParsedContent) -> Dict[str, Any]:
        """提取风险数据."""
        # 从表格中提取风险登记表
        if content.tables:
            return self._extract_risks_from_tables(content.tables)
        return self._mock_risk_extraction(content)

    async def _extract_generic(
        self,
        content: ParsedContent,
        entity_types: List[str],
    ) -> Dict[str, Any]:
        """通用数据提取."""
        prompt = self._build_generic_prompt(content, entity_types)
        return self._mock_generic_extraction(content, entity_types)

    # ==================== Prompt构建 ====================

    def _build_weekly_report_prompt(self, content: ParsedContent) -> str:
        """构建周报提取Prompt."""
        return f"""你是一个项目周报数据提取专家。

## 任务
从周报文档中提取结构化数据。

## 周报字段定义
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| report_date | date | 是 | 周报日期（周结束日期） |
| week_start | date | 是 | 周开始日期 |
| week_end | date | 是 | 周结束日期 |
| summary | string | 否 | 本周工作总结 |
| completed_tasks | array | 否 | 已完成任务列表 |
| in_progress_tasks | array | 否 | 进行中任务列表 |
| next_week_plan | string | 否 | 下周计划 |
| risks_and_issues | string | 否 | 风险和问题 |

## 文档内容
{content.get_text_summary(3000)}

## 提取规则
1. 周报日期通常为文档标题或日期标识
2. 已完成任务需提取任务名称和完成状态
3. 进行中任务需提取任务名称和当前进度
4. 日期格式：YYYY-MM-DD

## 输出要求（JSON格式）
```json
{
  "report_date": "2024-01-19",
  "week_start": "2024-01-15",
  "week_end": "2024-01-19",
  "summary": "...",
  "completed_tasks": [{"name": "...", "status": "completed"}],
  "in_progress_tasks": [{"name": "...", "progress": 60}],
  "next_week_plan": "...",
  "risks_and_issues": "...",
  "confidence": 0.90
}
```

请直接输出JSON。"""

    def _build_meeting_minutes_prompt(self, content: ParsedContent) -> str:
        """构建会议纪要提取Prompt."""
        return f"""你是一个会议纪要数据提取专家。

## 任务
从会议纪要文档中提取结构化数据，并识别待办事项。

## 会议纪要字段定义
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| meeting_title | string | 是 | 会议标题 |
| meeting_date | date | 是 | 会议日期 |
| meeting_time | string | 否 | 会议时间 |
| meeting_location | string | 否 | 会议地点 |
| attendees | array | 否 | 参会人员列表 |
| content | string | 是 | 会议内容 |
| decisions | array | 否 | 决议事项 |
| action_items | array | 是 | 待办事项（将创建任务） |

## 待办事项字段
| 字段名 | 类型 | 说明 |
|--------|------|------|
| task_name | string | 任务名称 |
| assignee_name | string | 负责人姓名 |
| due_date | date | 截止日期 |
| priority | string | 优先级 |

## 文档内容
{content.get_text_summary(3000)}

## 输出要求（JSON格式）
```json
{
  "meeting_title": "...",
  "meeting_date": "2024-01-18",
  "meeting_time": "14:00-15:30",
  "attendees": ["张三", "李四"],
  "content": "...",
  "action_items": [{"task_name": "...", "assignee_name": "...", "due_date": "...", "priority": "high"}],
  "confidence": 0.88
}
```

请直接输出JSON。"""

    def _build_generic_prompt(
        self,
        content: ParsedContent,
        entity_types: List[str],
    ) -> str:
        """构建通用提取Prompt."""
        schema_desc = self._build_schema_description(entity_types)

        return f"""你是一个项目数据提取专家。

## 任务
从文档内容中提取结构化数据。

## 目标实体类型
{entity_types}

## 实体字段定义
{schema_desc}

## 文档内容
{content.get_text_summary(3000)}

## 提取规则
1. 日期字段：转换为YYYY-MM-DD格式
2. 金额字段：提取数字，单位默认为元
3. 状态字段：使用英文枚举值
4. 人员字段：提取姓名

## 输出要求（JSON格式）
```json
{
  "extracted_entities": [
    {
      "entity_type": "Task",
      "data": {...},
      "confidence": 0.85
    }
  ]
}
```

请直接输出JSON。"""

    def _build_schema_description(self, entity_types: List[str]) -> str:
        """构建Schema描述."""
        descriptions = []
        for entity_type in entity_types:
            if entity_type in self.ENTITY_SCHEMAS:
                schema = self.ENTITY_SCHEMAS[entity_type]
                desc = f"### {entity_type}\n"
                for field_name, field_def in schema.items():
                    required = "必填" if field_def.get("required") else "可选"
                    desc += f"- {field_name}: {field_def.get('description', '')} ({required})\n"
                descriptions.append(desc)
        return "\n".join(descriptions)

    # ==================== 模拟提取（测试用） ====================

    def _mock_weekly_report_extraction(self, content: ParsedContent) -> Dict[str, Any]:
        """模拟周报提取."""
        text = content.text

        # 尝试从文本中提取日期
        dates = self._extract_dates(text)

        return {
            "report_date": dates[0] if dates else None,
            "week_start": dates[0] if dates else None,
            "week_end": dates[1] if len(dates) > 1 else dates[0] if dates else None,
            "summary": text[:500] if text else "",
            "completed_tasks": [],
            "in_progress_tasks": [],
            "next_week_plan": "",
            "risks_and_issues": "",
            "confidence": 0.75,
        }

    def _mock_meeting_minutes_extraction(self, content: ParsedContent) -> Dict[str, Any]:
        """模拟会议纪要提取."""
        text = content.text
        dates = self._extract_dates(text)

        return {
            "meeting_title": "会议纪要",
            "meeting_date": dates[0] if dates else None,
            "meeting_time": "",
            "attendees": self._extract_names(text),
            "content": text[:1000] if text else "",
            "action_items": [],
            "confidence": 0.70,
        }

    def _extract_wbs_from_tables(self, tables: List[Any]) -> Dict[str, Any]:
        """从表格提取WBS."""
        wbs_items = []

        for table in tables:
            if not table.headers:
                continue

            # 寻找WBS特征列
            wbs_columns = ["任务名称", "任务编号", "WBS编号", "层级", "前置任务", "工期"]
            matched_columns = [h for h in table.headers if h in wbs_columns]

            if matched_columns:
                for row in table.rows:
                    wbs_item = {}
                    for i, header in enumerate(table.headers):
                        if i < len(row):
                            wbs_item[header] = row[i]
                    wbs_items.append(wbs_item)

        return {
            "wbs_data": wbs_items,
            "confidence": 0.85 if wbs_items else 0.3,
        }

    def _extract_risks_from_tables(self, tables: List[Any]) -> Dict[str, Any]:
        """从表格提取风险."""
        risks = []

        for table in tables:
            if not table.headers:
                continue

            # 寻找风险登记表特征列
            risk_columns = ["风险描述", "风险等级", "应对措施", "负责人"]
            matched_columns = [h for h in table.headers if any(rc in h for rc in risk_columns)]

            if matched_columns:
                for row in table.rows:
                    risk = {}
                    for i, header in enumerate(table.headers):
                        if i < len(row):
                            risk[header] = row[i]
                    risks.append(risk)

        return {
            "risks": risks,
            "confidence": 0.85 if risks else 0.3,
        }

    def _mock_risk_extraction(self, content: ParsedContent) -> Dict[str, Any]:
        """模拟风险提取."""
        return {
            "risks": [],
            "confidence": 0.5,
        }

    def _mock_generic_extraction(
        self,
        content: ParsedContent,
        entity_types: List[str],
    ) -> Dict[str, Any]:
        """模拟通用提取."""
        entities = []

        # 从表格中尝试提取
        for table in content.tables:
            for entity_type in entity_types:
                if entity_type in ["Task", "Risk", "Cost"]:
                    for row in table.rows[:5]:  # 最多5行
                        entity = {
                            "entity_type": entity_type,
                            "data": {},
                            "confidence": 0.6,
                        }
                        for i, header in enumerate(table.headers):
                            if i < len(row):
                                entity["data"][header] = row[i]
                        entities.append(entity)

        return {
            "extracted_entities": entities,
            "confidence": 0.6 if entities else 0.3,
        }

    # ==================== 辅助方法 ====================

    def _extract_dates(self, text: str) -> List[str]:
        """从文本提取日期."""
        patterns = [
            r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?",
            r"\d{1,2}[-/]\d{1,2}[-/]\d{4}",
        ]

        dates = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # 标准化日期格式
                standardized = self._standardize_date(match)
                if standardized:
                    dates.append(standardized)

        return dates[:10]  # 最多10个日期

    def _standardize_date(self, date_str: str) -> Optional[str]:
        """标准化日期格式."""
        try:
            # 处理中文日期格式
            if "年" in date_str:
                date_str = date_str.replace("年", "-").replace("月", "-").replace("日", "")

            # 处理斜杠格式
            if "/" in date_str:
                parts = date_str.split("/")
                if len(parts[0]) == 4:
                    date_str = f"{parts[0]}-{parts[1]}-{parts[2]}"
                else:
                    date_str = f"{parts[2]}-{parts[0]}-{parts[1]}"

            # 验证格式
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            return None

    def _extract_names(self, text: str) -> List[str]:
        """从文本提取姓名."""
        # 简单的姓名提取模式
        pattern = r"[张王李刘陈杨赵黄周吴徐朱马胡郭林何高梁郑罗谢宋唐许韩冯邓曹彭曾萧田董潘袁蔡蒋余于杜叶程魏苏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃洪]\w{1,2}"
        matches = re.findall(pattern, text)
        return matches[:10]

    def _build_entities(
        self,
        extraction_data: Dict[str, Any],
        entity_types: List[str],
    ) -> List[ExtractedEntity]:
        """构建实体列表."""
        entities = []

        # 处理周报
        if "WeeklyReport" in entity_types and "report_date" in extraction_data:
            entity = ExtractedEntity(
                entity_type="WeeklyReport",
                data=self._convert_entity_data(extraction_data, "WeeklyReport"),
                field_confidence=self._calculate_field_confidence(extraction_data, "WeeklyReport"),
            )
            entities.append(entity)

        # 处理会议纪要
        if "MeetingMinutes" in entity_types and "meeting_title" in extraction_data:
            entity = ExtractedEntity(
                entity_type="MeetingMinutes",
                data=self._convert_entity_data(extraction_data, "MeetingMinutes"),
                field_confidence=self._calculate_field_confidence(extraction_data, "MeetingMinutes"),
            )
            entities.append(entity)

        # 处理通用实体
        if "extracted_entities" in extraction_data:
            for item in extraction_data["extracted_entities"]:
                entity = ExtractedEntity(
                    entity_type=item.get("entity_type", "unknown"),
                    data=self._convert_entity_data(item.get("data", {}), item.get("entity_type")),
                    field_confidence=item.get("field_confidence", {}),
                )
                entities.append(entity)

        return entities

    def _convert_entity_data(
        self,
        data: Dict[str, Any],
        entity_type: str,
    ) -> Dict[str, Any]:
        """转换实体数据格式."""
        converted = {}

        for field, value in data.items():
            if value is None:
                continue

            # 状态转换
            if field in ["status", "level", "priority", "category"]:
                converted[field] = self._convert_status(value, entity_type, field)

            # 日期转换
            elif field.endswith("_date") or field in ["date"]:
                converted[field] = self._standardize_date(str(value)) if value else None

            # 数字转换
            elif field in ["progress", "probability", "impact", "total_budget", "amount"]:
                converted[field] = self._convert_number(value)

            else:
                converted[field] = value

        return converted

    def _convert_status(
        self,
        value: str,
        entity_type: str,
        field: str,
    ) -> Optional[str]:
        """转换状态值."""
        if not value:
            return None

        value_str = str(value).strip()

        # 查找映射
        mapping_key = entity_type.lower() if field == "status" else f"{entity_type.lower()}_{field}"
        if field == "level":
            mapping_key = "risk_level"
        elif field == "priority":
            mapping_key = "priority"

        mapping = self.STATUS_MAPPING.get(mapping_key, {})
        return mapping.get(value_str, value_str.lower())

    def _convert_number(self, value: Any) -> Optional[float]:
        """转换数字."""
        if value is None:
            return None

        try:
            # 去除百分号等符号
            value_str = str(value).replace("%", "").replace(",", "")
            return float(value_str)
        except ValueError:
            return None

    def _calculate_field_confidence(
        self,
        data: Dict[str, Any],
        entity_type: str,
    ) -> Dict[str, float]:
        """计算字段置信度."""
        confidence = {}
        schema = self.ENTITY_SCHEMAS.get(entity_type, {})

        for field, value in data.items():
            if field not in schema:
                continue

            if value is None:
                confidence[field] = 0.0
            elif self._is_valid_format(field, value, schema[field]):
                confidence[field] = 0.90
            else:
                confidence[field] = 0.70

        return confidence

    def _is_valid_format(
        self,
        field: str,
        value: Any,
        field_def: Dict[str, Any],
    ) -> bool:
        """检查值格式是否有效."""
        field_type = field_def.get("type", "string")

        if field_type == "date":
            try:
                datetime.strptime(str(value), "%Y-%m-%d")
                return True
            except ValueError:
                return False

        if field_type in ["int", "float"]:
            try:
                float(str(value).replace("%", ""))
                return True
            except ValueError:
                return False

        if field_type == "enum":
            valid_values = field_def.get("values", [])
            return str(value).lower() in valid_values

        return True

    def _calculate_overall_confidence(self, entities: List[ExtractedEntity]) -> float:
        """计算总体置信度."""
        if not entities:
            return 0.0

        total_confidence = 0.0
        total_fields = 0

        for entity in entities:
            for field, conf in entity.field_confidence.items():
                total_confidence += conf
                total_fields += 1

        return total_confidence / total_fields if total_fields > 0 else 0.5

    def _check_missing_fields(
        self,
        entities: List[ExtractedEntity],
        entity_types: List[str],
    ) -> List[str]:
        """检查缺失的必填字段."""
        missing = []

        for entity in entities:
            schema = self.ENTITY_SCHEMAS.get(entity.entity_type, {})
            for field, field_def in schema.items():
                if field_def.get("required"):
                    if field not in entity.data or entity.data[field] is None:
                        missing.append(f"{entity.entity_type}.{field}")

        return missing


# 服务工厂
_data_extractor_service: Optional[DataExtractorService] = None


def get_data_extractor_service() -> DataExtractorService:
    """获取数据提取服务实例."""
    global _data_extractor_service
    if _data_extractor_service is None:
        _data_extractor_service = DataExtractorService()
    return _data_extractor_service