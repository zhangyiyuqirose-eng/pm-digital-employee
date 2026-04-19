"""
PM Digital Employee - Document Classifier Service
项目经理数字员工系统 - 文档分类服务

v1.3.0新增：多级分类策略实现
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from app.core.logging import get_logger
from app.core.exceptions import ServiceError
from app.domain.enums import DocumentCategory, ProjectPhase, DocumentSubtype
from app.services.file_parser_service import ParsedContent, FileInfo

logger = get_logger(__name__)


class ClassificationError(ServiceError):
    """分类错误."""

    def __init__(self, message: str):
        super().__init__(
            code="classification_error",
            message=message,
        )


@dataclass
class ContentCategory:
    """内容分类结果."""

    document_category: str          # 文档大类
    project_phase: str              # 项目阶段
    document_subtype: str           # 文档子类型
    confidence: float               # 置信度
    inferred_entity_types: List[str]  # 推断的可提取实体类型
    classification_reason: str      # 分类依据说明
    keywords_matched: List[str] = field(default_factory=list)  # 匹配的关键词


@dataclass
class ProjectMatch:
    """项目匹配结果."""

    project_id: Optional[str]       # 项目ID
    project_name: Optional[str]     # 项目名称
    match_type: str                 # 匹配类型（group_binding/content_match/user_context/unknown）
    confidence: float               # 置信度
    keywords: List[str] = field(default_factory=list)  # 匹配的关键词


@dataclass
class ClassificationResult:
    """完整分类结果."""

    content_category: ContentCategory
    project_match: ProjectMatch
    combined_confidence: float      # 综合置信度


class DocumentClassifierService:
    """
    文档分类服务.

    实现多级分类策略：
    1. 扩展名快速分类
    2. 文件名关键词匹配
    3. 内容深度分析（LLM）
    4. 项目关联推断
    5. 综合判定
    """

    # 文件名关键词映射
    FILENAME_KEYWORDS: Dict[str, tuple] = {
        # 执行阶段文档
        "周报": ("weekly_report", "execution", ["WeeklyReport"]),
        "会议纪要": ("meeting_minutes", "execution", ["MeetingMinutes", "Task"]),
        "会议记录": ("meeting_minutes", "execution", ["MeetingMinutes", "Task"]),
        "纪要": ("meeting_minutes", "execution", ["MeetingMinutes"]),
        "进度报告": ("progress_report", "execution", ["Task", "Milestone"]),
        "任务清单": ("task_report", "execution", ["Task"]),
        "任务报告": ("task_report", "execution", ["Task"]),
        # 全周期文档
        "WBS": ("wbs", "full_cycle", ["WBSVersion", "Task"]),
        "工作分解": ("wbs", "full_cycle", ["WBSVersion", "Task"]),
        "风险": ("risk_register", "full_cycle", ["Risk"]),
        "风险登记": ("risk_register", "full_cycle", ["Risk"]),
        "里程碑": ("milestone_plan", "full_cycle", ["Milestone"]),
        "成本": ("cost_report", "full_cycle", ["Cost"]),
        # 立项阶段文档
        "立项": ("initiation_doc", "initiation", ["Project"]),
        "项目章程": ("project_charter", "initiation", ["Project"]),
        "审批表": ("initiation_doc", "initiation", ["Project"]),
        # 预立项阶段文档
        "可行性": ("feasibility_report", "pre_initiation", ["Project"]),
        "建议书": ("project_proposal", "pre_initiation", ["Project"]),
        "立项申请": ("initiation_approval", "pre_initiation", ["Project"]),
        # 收尾阶段文档
        "验收": ("acceptance_report", "closing", ["Project"]),
        "总结": ("summary_report", "closing", []),
        "复盘": ("review_doc", "closing", []),
        "结项": ("summary_report", "closing", ["Project"]),
        # 管理文档
        "制度": ("policy_doc", "none", []),
        "规范": ("standard_doc", "none", []),
        "流程": ("process_doc", "none", []),
        # 外部文档
        "合同": ("contract", "none", []),
        "供应商": ("supplier_doc", "none", []),
    }

    # 扩展名分类映射
    EXTENSION_CATEGORIES: Dict[str, str] = {
        # 表格类文档通常包含结构化数据
        "xlsx": "project_doc",
        "xls": "project_doc",
        "csv": "project_doc",
        # 文本类文档
        "docx": "project_doc",
        "doc": "project_doc",
        "pdf": "project_doc",
        "txt": "other",
        "md": "other",
        # 演示类文档
        "pptx": "management_doc",
        "ppt": "management_doc",
        # 图片类文档
        "jpg": "project_doc",
        "jpeg": "project_doc",
        "png": "project_doc",
        "bmp": "project_doc",
    }

    # 内容关键词映射（用于深度分析）
    CONTENT_KEYWORDS: Dict[str, List[str]] = {
        "weekly_report": ["本周", "下周", "工作总结", "工作计划", "完成情况"],
        "meeting_minutes": ["会议时间", "参会人员", "决议", "待办", "会议主题"],
        "wbs": ["工作分解", "任务层级", "前置任务", "工期", "WBS编码"],
        "risk_register": ["风险描述", "风险等级", "应对措施", "发生概率", "影响程度"],
        "milestone_plan": ["里程碑", "关键节点", "交付物", "计划日期"],
        "cost_report": ["成本", "预算", "支出", "费用"],
        "initiation_doc": ["立项申请", "审批", "项目背景", "目标"],
        "project_charter": ["项目章程", "授权", "项目经理", "目标"],
        "acceptance_report": ["验收", "验收标准", "验收结论", "交付物"],
    }

    def __init__(self) -> None:
        """初始化分类服务."""
        self._llm_gateway = None  # 将在首次使用时初始化

    async def classify(
        self,
        content: ParsedContent,
        file_info: FileInfo,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> ClassificationResult:
        """
        执行文档分类.

        Args:
            content: 解析后的文档内容
            file_info: 文件信息
            user_context: 用户上下文（包含chat_type, project_id等）

        Returns:
            ClassificationResult: 分类结果
        """
        logger.info(f"Classifying document: {file_info.name}")

        # Step 1: 扩展名快速分类
        ext_category = self._classify_by_extension(file_info.extension)

        # Step 2: 文件名关键词匹配
        name_category = self._classify_by_filename(file_info.name)

        # Step 3: 内容关键词分析（轻量级）
        content_category_light = self._classify_by_keywords(content)

        # Step 4: 内容深度分析（LLM）- 如果轻量分析置信度不够
        content_category = await self._classify_by_content_llm(
            content, file_info, content_category_light
        )

        # Step 5: 项目关联推断
        project_match = await self._infer_project(
            content, file_info, user_context
        )

        # 综合判定
        result = self._merge_classification(
            ext_category, name_category, content_category, project_match
        )

        logger.info(
            f"Classification result: category={result.content_category.document_category}, "
            f"subtype={result.content_category.document_subtype}, "
            f"confidence={result.combined_confidence}"
        )

        return result

    def _classify_by_extension(self, extension: str) -> Dict[str, Any]:
        """根据扩展名分类."""
        ext = extension.lower()
        category = self.EXTENSION_CATEGORIES.get(ext, "other")
        return {
            "document_category": category,
            "confidence": 0.5,
            "source": "extension",
        }

    def _classify_by_filename(self, filename: str) -> Dict[str, Any]:
        """根据文件名关键词分类."""
        # 提取文件名（去除扩展名）
        name = filename.rsplit(".", 1)[0] if "." in filename else filename

        matched_result = None
        matched_keywords = []

        for keyword, (subtype, phase, entities) in self.FILENAME_KEYWORDS.items():
            if keyword in name:
                matched_result = {
                    "document_subtype": subtype,
                    "project_phase": phase,
                    "entity_types": entities,
                    "confidence": 0.85,
                    "source": "filename",
                }
                matched_keywords.append(keyword)
                break  # 找到第一个匹配就停止

        return {
            "matched": matched_result,
            "keywords": matched_keywords,
            "confidence": 0.85 if matched_result else 0.0,
        }

    def _classify_by_keywords(self, content: ParsedContent) -> Dict[str, Any]:
        """根据内容关键词分类（轻量级分析）."""
        text = content.text.lower()
        scores: Dict[str, float] = {}

        for subtype, keywords in self.CONTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            if score > 0:
                scores[subtype] = score / len(keywords)

        if scores:
            best_subtype = max(scores.keys(), key=lambda k: scores[k])
            best_score = scores[best_subtype]
            return {
                "document_subtype": best_subtype,
                "confidence": min(0.7, best_score),  # 最高0.7置信度
                "source": "keywords",
                "scores": scores,
            }

        return {
            "document_subtype": "unknown",
            "confidence": 0.0,
            "source": "keywords",
        }

    async def _classify_by_content_llm(
        self,
        content: ParsedContent,
        file_info: FileInfo,
        light_result: Dict[str, Any],
    ) -> ContentCategory:
        """使用LLM进行内容深度分类."""
        # 如果轻量分析置信度已经很高，直接使用
        if light_result.get("confidence", 0) >= 0.7:
            return ContentCategory(
                document_category="project_doc",
                project_phase="execution",
                document_subtype=light_result["document_subtype"],
                confidence=light_result["confidence"],
                inferred_entity_types=self._get_entity_types(light_result["document_subtype"]),
                classification_reason="基于内容关键词匹配",
            )

        # 调用LLM进行深度分析
        try:
            llm_result = await self._call_llm_classification(content, file_info)
            return llm_result
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}, using fallback")
            # 使用轻量分析结果作为fallback
            return ContentCategory(
                document_category="project_doc",
                project_phase="execution",
                document_subtype=light_result["document_subtype"],
                confidence=light_result["confidence"] * 0.8,
                inferred_entity_types=self._get_entity_types(light_result["document_subtype"]),
                classification_reason="LLM调用失败，使用关键词匹配fallback",
            )

    async def _call_llm_classification(
        self,
        content: ParsedContent,
        file_info: FileInfo,
    ) -> ContentCategory:
        """调用LLM进行分类."""
        # TODO: 对接实际的LLM Gateway
        # 当前使用模拟实现
        prompt = self._build_classification_prompt(content, file_info)

        # 模拟LLM响应
        # 实际实现应调用: await self._llm_gateway.generate(prompt)
        mock_response = self._mock_llm_response(content, file_info)

        return ContentCategory(
            document_category=mock_response["document_category"],
            project_phase=mock_response["project_phase"],
            document_subtype=mock_response["document_subtype"],
            confidence=mock_response["confidence"],
            inferred_entity_types=mock_response["inferred_entity_types"],
            classification_reason=mock_response["classification_reason"],
        )

    def _build_classification_prompt(
        self,
        content: ParsedContent,
        file_info: FileInfo,
    ) -> str:
        """构建分类Prompt."""
        text_summary = content.get_text_summary(1500)
        key_content = content.get_key_content()

        return f"""你是一个项目管理文档分类专家。

## 任务
分析文档内容，判断文档类型和关联的业务场景。

## 文档信息
- 文件名：{file_info.name}
- 文件类型：{file_info.extension}
- 内容摘要：{text_summary}
- 关键内容：{key_content}

## 分类选项
1. **文档大类**: project_doc（项目文档）/ management_doc（管理文档）/ external_doc（外部文档）/ other（其他）
2. **项目阶段**: pre_initiation（预立项）/ initiation（立项）/ execution（执行）/ closing（收尾）/ full_cycle（全周期）/ none
3. **文档子类型**: weekly_report, meeting_minutes, wbs, risk_register, milestone_plan, cost_report, initiation_doc, acceptance_report, summary_report, policy_doc, contract, unknown等

## 输出要求（JSON格式）
```json
{
  "document_category": "...",
  "project_phase": "...",
  "document_subtype": "...",
  "confidence": 0.85,
  "inferred_entity_types": ["Task", "Risk"],
  "classification_reason": "..."
}
```

请直接输出JSON。"""

    def _mock_llm_response(
        self,
        content: ParsedContent,
        file_info: FileInfo,
    ) -> Dict[str, Any]:
        """模拟LLM响应（用于测试）。"""
        # 基于文件名和内容的简单模拟
        name_result = self._classify_by_filename(file_info.name)

        if name_result["matched"]:
            matched = name_result["matched"]
            return {
                "document_category": "project_doc",
                "project_phase": matched["project_phase"],
                "document_subtype": matched["document_subtype"],
                "confidence": 0.88,
                "inferred_entity_types": matched["entity_types"],
                "classification_reason": f"文件名包含关键词: {name_result['keywords']}",
            }

        return {
            "document_category": "project_doc",
            "project_phase": "execution",
            "document_subtype": "unknown",
            "confidence": 0.5,
            "inferred_entity_types": [],
            "classification_reason": "无法明确分类，默认为项目文档",
        }

    async def _infer_project(
        self,
        content: ParsedContent,
        file_info: FileInfo,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> ProjectMatch:
        """推断关联项目."""
        user_context = user_context or {}

        # 群聊场景：优先使用群绑定项目
        if user_context.get("chat_type") == "group":
            group_project_id = user_context.get("group_binding_project_id")
            if group_project_id:
                return ProjectMatch(
                    project_id=group_project_id,
                    project_name=user_context.get("group_binding_project_name"),
                    match_type="group_binding",
                    confidence=1.0,
                )

        # 文档内容匹配项目关键词
        project_keywords = self._extract_project_keywords(content.text)
        if project_keywords:
            # TODO: 查询数据库匹配项目
            return ProjectMatch(
                project_id=None,
                project_name=project_keywords[0] if project_keywords else None,
                match_type="content_match",
                confidence=0.85,
                keywords=project_keywords,
            )

        # 用户上下文项目
        user_project_id = user_context.get("project_id")
        if user_project_id:
            return ProjectMatch(
                project_id=user_project_id,
                project_name=user_context.get("project_name"),
                match_type="user_context",
                confidence=0.7,
            )

        # 无法推断
        return ProjectMatch(
            project_id=None,
            project_name=None,
            match_type="unknown",
            confidence=0.0,
        )

    def _extract_project_keywords(self, text: str) -> List[str]:
        """提取项目关键词."""
        # 常见项目名称模式
        patterns = [
            r"项目[名称编号][:：]\s*([^\n\r]+)",
            r"《([^》]+)》项目",
            r"([^，。\s]{3,20})项目",
        ]

        keywords = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            keywords.extend(matches)

        return keywords[:3]  # 最多返回3个关键词

    def _merge_classification(
        self,
        ext_category: Dict[str, Any],
        name_category: Dict[str, Any],
        content_category: ContentCategory,
        project_match: ProjectMatch,
    ) -> ClassificationResult:
        """合并分类结果."""
        # 文件名匹配优先级最高
        if name_category["matched"]:
            matched = name_category["matched"]
            final_subtype = matched["document_subtype"]
            final_phase = matched["project_phase"]
            final_entities = matched["entity_types"]
            final_confidence = 0.90  # 文件名匹配置信度
        else:
            final_subtype = content_category.document_subtype
            final_phase = content_category.project_phase
            final_entities = content_category.inferred_entity_types
            final_confidence = content_category.confidence

        # 确定文档大类
        if final_subtype in ["policy_doc", "standard_doc", "process_doc"]:
            final_category = "management_doc"
        elif final_subtype in ["contract", "supplier_doc", "external_report"]:
            final_category = "external_doc"
        elif final_subtype == "unknown":
            final_category = ext_category["document_category"]
        else:
            final_category = "project_doc"

        # 项目匹配置信度影响综合置信度
        if project_match.match_type == "group_binding":
            combined_confidence = final_confidence * 1.0
        elif project_match.match_type == "content_match":
            combined_confidence = final_confidence * 0.9
        elif project_match.match_type == "unknown":
            combined_confidence = final_confidence * 0.6
        else:
            combined_confidence = final_confidence

        return ClassificationResult(
            content_category=ContentCategory(
                document_category=final_category,
                project_phase=final_phase,
                document_subtype=final_subtype,
                confidence=final_confidence,
                inferred_entity_types=final_entities,
                classification_reason=content_category.classification_reason,
            ),
            project_match=project_match,
            combined_confidence=min(combined_confidence, 1.0),
        )

    def _get_entity_types(self, document_subtype: str) -> List[str]:
        """根据文档子类型获取可提取实体类型."""
        subtype_entity_map = {
            "weekly_report": ["WeeklyReport", "Task"],
            "meeting_minutes": ["MeetingMinutes", "Task"],
            "wbs": ["WBSVersion", "Task"],
            "risk_register": ["Risk"],
            "milestone_plan": ["Milestone"],
            "cost_report": ["Cost"],
            "initiation_doc": ["Project"],
            "project_charter": ["Project"],
            "acceptance_report": ["Project", "Milestone"],
            "task_report": ["Task"],
            "progress_report": ["Task", "Milestone"],
        }
        return subtype_entity_map.get(document_subtype, [])


# 服务工厂
_document_classifier_service: Optional[DocumentClassifierService] = None


def get_document_classifier_service() -> DocumentClassifierService:
    """获取文档分类服务实例."""
    global _document_classifier_service
    if _document_classifier_service is None:
        _document_classifier_service = DocumentClassifierService()
    return _document_classifier_service