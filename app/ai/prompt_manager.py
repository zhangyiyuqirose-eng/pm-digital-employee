"""
PM Digital Employee - Prompt Manager
项目经理数字员工系统 - Prompt模板管理

管理Prompt模板的加载、渲染、版本控制。
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.ai.schemas import PromptTemplate
from app.core.config import settings
from app.core.exceptions import ErrorCode, PromptError
from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptManager:
    """
    Prompt模板管理器.

    管理Prompt模板的加载、渲染、版本控制。
    支持从文件系统加载和动态注册。
    """

    def __init__(
        self,
        template_dir: Optional[Path] = None,
    ) -> None:
        """
        初始化Prompt管理器.

        Args:
            template_dir: 模板目录路径
        """
        self._template_dir = template_dir or Path(settings.app.base_dir) / "prompts"
        self._templates: Dict[str, PromptTemplate] = {}
        self._default_templates = self._create_default_templates()

        # 加载默认模板
        self._templates.update(self._default_templates)

        # 从文件系统加载模板
        if self._template_dir.exists():
            self._load_templates_from_dir()

    def _create_default_templates(self) -> Dict[str, PromptTemplate]:
        """
        创建默认模板.

        Returns:
            Dict: 默认模板映射
        """
        return {
            # 意图识别模板
            "intent_recognition": PromptTemplate(
                name="intent_recognition",
                description="意图识别Prompt模板",
                template="""你是一个项目经理数字员工的意图识别助手。

## 任务
分析用户的输入，判断用户想要执行什么操作，并匹配到对应的Skill。

## 可用Skill列表
{skill_descriptions}

## 用户上下文
- 用户角色: {user_role}
- 当前项目: {project_name}
- 会话类型: {chat_type}

## 用户输入
{user_message}

## 对话历史
{conversation_history}

## 输出要求
请以JSON格式输出分析结果。
""",
                input_variables=[
                    "skill_descriptions",
                    "user_role",
                    "project_name",
                    "chat_type",
                    "user_message",
                    "conversation_history",
                ],
                version="1.0.0",
            ),

            # 周报生成模板
            "weekly_report": PromptTemplate(
                name="weekly_report",
                description="项目周报生成Prompt模板",
                template="""你是一个项目管理助手，负责生成项目周报。

## 项目信息
- 项目名称: {project_name}
- 项目状态: {project_status}
- 整体进度: {progress}%

## 本周任务完成情况
{completed_tasks}

## 进行中任务
{in_progress_tasks}

## 风险状态
{risks}

## 下周计划
{next_week_plan}

## 输出要求
请生成一份结构清晰的项目周报，包含：
1. 本周工作总结
2. 进度分析
3. 风险提示
4. 下周工作计划

周报应该专业、简洁，便于领导快速了解项目状态。
""",
                input_variables=[
                    "project_name",
                    "project_status",
                    "progress",
                    "completed_tasks",
                    "in_progress_tasks",
                    "risks",
                    "next_week_plan",
                ],
                version="1.0.0",
            ),

            # WBS生成模板
            "wbs_generation": PromptTemplate(
                name="wbs_generation",
                description="WBS工作分解结构生成Prompt模板",
                template="""你是一个项目管理专家，负责生成WBS工作分解结构。

## 项目信息
- 项目名称: {project_name}
- 项目类型: {project_type}
- 项目周期: {duration}天
- 项目规模: {scale}

## 项目需求
{requirements}

## 输出要求
请生成一份详细的WBS，包含：
1. 任务分解（层级结构，最多3层）
2. 每个任务的预估工期
3. 任务之间的依赖关系
4. 关键里程碑

输出格式为JSON：
```json
{
  "wbs": [
    {
      "id": "1",
      "name": "任务名称",
      "duration": "预估天数",
      "dependencies": ["依赖任务ID"],
      "children": [...]
    }
  ]
}
```
""",
                input_variables=[
                    "project_name",
                    "project_type",
                    "duration",
                    "scale",
                    "requirements",
                ],
                version="1.0.0",
            ),

            # 风险分析模板
            "risk_analysis": PromptTemplate(
                name="risk_analysis",
                description="风险分析Prompt模板",
                template="""你是一个项目风险管理专家。

## 项目信息
- 项目名称: {project_name}
- 项目阶段: {project_phase}
- 进度偏差: {schedule_variance}%
- 成本偏差: {cost_variance}%

## 已识别风险
{existing_risks}

## 项目问题
{issues}

## 输出要求
请分析项目风险状况，输出：
1. 新识别的风险（包括风险描述、等级、影响范围）
2. 风险应对建议
3. 需要重点关注的风险领域

输出格式为JSON。
""",
                input_variables=[
                    "project_name",
                    "project_phase",
                    "schedule_variance",
                    "cost_variance",
                    "existing_risks",
                    "issues",
                ],
                version="1.0.0",
            ),

            # 会议纪要生成模板
            "meeting_minutes": PromptTemplate(
                name="meeting_minutes",
                description="会议纪要生成Prompt模板",
                template="""你是一个会议纪要助手，负责整理会议内容。

## 会议信息
- 会议标题: {meeting_title}
- 会议时间: {meeting_time}
- 参会人员: {participants}

## 会议内容
{meeting_content}

## 输出要求
请生成结构化的会议纪要，包含：
1. 会议议题
2. 讨论要点
3. 决议事项
4. 待办事项（包括负责人和截止日期）

输出格式为JSON。
""",
                input_variables=[
                    "meeting_title",
                    "meeting_time",
                    "participants",
                    "meeting_content",
                ],
                version="1.0.0",
            ),

            # 合规初审模板
            "compliance_review": PromptTemplate(
                name="compliance_review",
                description="材料合规初审Prompt模板",
                template="""你是一个项目管理合规审核专家。

## 审核类型
- 文档类型: {document_type}
- 项目名称: {project_name}

## 文档内容
{document_content}

## 合规检查清单
{checklist}

## 输出要求
请对文档进行合规初审，输出：
1. 合规状态（通过/不通过）
2. 各检查项的检查结果
3. 缺失或不合规项
4. 改进建议

输出格式为JSON。
""",
                input_variables=[
                    "document_type",
                    "project_name",
                    "document_content",
                    "checklist",
                ],
                version="1.0.0",
            ),

            # 制度问答模板
            "policy_qa": PromptTemplate(
                name="policy_qa",
                description="制度规范问答Prompt模板",
                template="""你是一个项目管理规章制度咨询助手。

## 用户问题
{question}

## 相关制度内容
{context}

## 输出要求
请根据制度内容回答用户问题：
1. 回答要准确、专业
2. 必须引用具体的制度来源
3. 如果制度中没有相关内容，明确告知
4. 回答要简洁明了

回答格式：
【回答】
{回答内容}

【依据】
{引用的制度条款}
""",
                input_variables=[
                    "question",
                    "context",
                ],
                version="1.0.0",
            ),

            # 项目咨询模板
            "project_query": PromptTemplate(
                name="project_query",
                description="项目情况咨询Prompt模板",
                template="""你是一个项目管理助手，负责回答项目相关问题。

## 用户问题
{question}

## 项目数据
{project_data}

## 输出要求
请根据项目数据回答用户问题：
1. 回答要准确、基于数据
2. 必要时提供数据来源
3. 如果数据不足，明确告知

请直接回答用户问题。
""",
                input_variables=[
                    "question",
                    "project_data",
                ],
                version="1.0.0",
            ),

            # v1.3.0新增：文档解析相关模板

            # 文档分类模板
            "document_classification": PromptTemplate(
                name="document_classification",
                description="文档智能分类Prompt模板",
                template="""你是一个项目管理文档分类专家。

## 任务
分析文档内容，判断文档类型和关联的业务场景。

## 文档信息
- 文件名：{file_name}
- 文件类型：{file_type}
- 内容摘要：{content_summary}

## 输出要求
请以JSON格式输出分类结果：
```json
{
  "document_category": "文档大类",
  "project_phase": "项目阶段",
  "document_subtype": "文档子类型",
  "confidence": 0.85,
  "inferred_entity_types": []
}
```

请直接输出JSON。
""",
                input_variables=[
                    "file_name",
                    "file_type",
                    "content_summary",
                ],
                version="1.0.0",
            ),

            # 周报提取模板
            "weekly_report_extraction": PromptTemplate(
                name="weekly_report_extraction",
                description="周报数据提取Prompt模板",
                template="""你是一个项目周报数据提取专家。

## 任务
从周报文档中提取结构化数据。

## 文档内容
{document_content}

## 输出要求
请以JSON格式输出提取结果：
```json
{
  "report_date": "2024-01-19",
  "week_start": "2024-01-15",
  "week_end": "2024-01-19",
  "summary": "本周工作总结",
  "completed_tasks": [],
  "in_progress_tasks": [],
  "next_week_plan": "下周计划",
  "confidence": 0.90
}
```

请直接输出JSON。
""",
                input_variables=["document_content"],
                version="1.0.0",
            ),

            # 会议纪要提取模板
            "meeting_minutes_extraction": PromptTemplate(
                name="meeting_minutes_extraction",
                description="会议纪要数据提取Prompt模板",
                template="""你是一个会议纪要数据提取专家。

## 任务
从会议纪要文档中提取结构化数据，并识别待办事项。

## 文档内容
{document_content}

## 输出要求
请以JSON格式输出提取结果：
```json
{
  "meeting_title": "会议标题",
  "meeting_date": "2024-01-18",
  "attendees": ["张三", "李四"],
  "content": "会议内容",
  "action_items": [
    {"task_name": "任务名称", "assignee_name": "负责人", "priority": "high"}
  ],
  "confidence": 0.88
}
```

请直接输出JSON。
""",
                input_variables=["document_content"],
                version="1.0.0",
            ),

            # 通用数据提取模板
            "document_extraction": PromptTemplate(
                name="document_extraction",
                description="通用项目数据提取Prompt模板",
                template="""你是一个项目数据提取专家。

## 任务
从文档内容中提取结构化数据。

## 目标实体类型
{entity_types}

## 实体字段定义
{entity_schema}

## 文档内容
{document_content}

## 输出要求
请以JSON格式输出提取结果：
```json
{
  "extracted_entities": [
    {"entity_type": "Task", "data": {...}}
  ],
  "confidence": 0.85
}
```

请直接输出JSON。
""",
                input_variables=[
                    "entity_types",
                    "entity_schema",
                    "document_content",
                ],
                version="1.0.0",
            ),

            # WBS提取模板
            "wbs_extraction": PromptTemplate(
                name="wbs_extraction",
                description="WBS数据提取Prompt模板",
                template="""你是一个WBS数据提取专家。

## 任务
从WBS文档中提取任务分解结构数据。

## 文档内容
{document_content}

## 输出要求
请以JSON格式输出WBS结构，包含层级关系。
```json
{
  "wbs_data": [
    {"id": "1", "name": "任务名称", "level": 1, "children": []}
  ],
  "confidence": 0.85
}
```

请直接输出JSON。
""",
                input_variables=["document_content"],
                version="1.0.0",
            ),

            # 风险提取模板
            "risk_extraction": PromptTemplate(
                name="risk_extraction",
                description="风险登记表数据提取Prompt模板",
                template="""你是一个项目风险数据提取专家。

## 任务
从风险登记表文档中提取风险数据。

## 文档内容
{document_content}

## 输出要求
请以JSON格式输出风险列表：
```json
{
  "risks": [
    {"title": "风险描述", "level": "high", "probability": 3, "impact": 4}
  ],
  "confidence": 0.85
}
```

请直接输出JSON。
""",
                input_variables=["document_content"],
                version="1.0.0",
            ),
        }

    def _load_templates_from_dir(self) -> None:
        """从目录加载模板文件."""
        for file_path in self._template_dir.glob("**/*.md"):
            try:
                self._load_template_from_file(file_path)
            except Exception as e:
                logger.warning(
                    "Failed to load template file",
                    file_path=str(file_path),
                    error=str(e),
                )

    def _load_template_from_file(self, file_path: Path) -> None:
        """
        从文件加载模板.

        Args:
            file_path: 文件路径
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析模板（简单实现：使用文件名作为模板名）
        template_name = file_path.stem

        # 尝试解析frontmatter
        template_content = content
        input_variables = []

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                import yaml
                try:
                    frontmatter = yaml.safe_load(parts[1])
                    template_content = parts[2].strip()
                    input_variables = frontmatter.get("variables", [])
                except yaml.YAMLError:
                    pass

        self._templates[template_name] = PromptTemplate(
            name=template_name,
            description=f"从文件 {file_path.name} 加载的模板",
            template=template_content,
            input_variables=input_variables,
        )

        logger.debug(
            "Template loaded from file",
            template_name=template_name,
            file_path=str(file_path),
        )

    def register_template(
        self,
        template: PromptTemplate,
    ) -> None:
        """
        注册模板.

        Args:
            template: Prompt模板
        """
        self._templates[template.name] = template

        logger.info(
            "Template registered",
            template_name=template.name,
            version=template.version,
        )

    def get_template(
        self,
        name: str,
    ) -> PromptTemplate:
        """
        获取模板.

        Args:
            name: 模板名称

        Returns:
            PromptTemplate: 模板对象

        Raises:
            PromptError: 模板不存在
        """
        template = self._templates.get(name)
        if template is None:
            raise PromptError(
                error_code=ErrorCode.PROMPT_ERROR,
                message=f"模板 '{name}' 不存在",
            )
        return template

    def render(
        self,
        name: str,
        **kwargs,
    ) -> str:
        """
        渲染模板.

        Args:
            name: 模板名称
            **kwargs: 模板变量

        Returns:
            str: 渲染后的内容

        Raises:
            PromptError: 渲染失败
        """
        template = self.get_template(name)

        try:
            # 使用Python字符串格式化
            # 提取模板中的变量
            content = template.template

            # 构建变量字典
            variables = {}
            for var in template.input_variables:
                if var in kwargs:
                    variables[var] = kwargs[var]
                else:
                    variables[var] = ""

            # 格式化
            rendered = content.format(**variables)

            return rendered

        except KeyError as e:
            raise PromptError(
                error_code=ErrorCode.PROMPT_ERROR,
                message=f"模板变量缺失: {e}",
            )
        except Exception as e:
            raise PromptError(
                error_code=ErrorCode.PROMPT_ERROR,
                message=f"模板渲染失败: {str(e)}",
            )

    def list_templates(self) -> List[str]:
        """
        列出所有模板名称.

        Returns:
            List[str]: 模板名称列表
        """
        return list(self._templates.keys())

    def get_template_info(self, name: str) -> Dict[str, Any]:
        """
        获取模板信息.

        Args:
            name: 模板名称

        Returns:
            Dict: 模板信息
        """
        template = self.get_template(name)
        return {
            "name": template.name,
            "description": template.description,
            "input_variables": template.input_variables,
            "version": template.version,
            "created_at": template.created_at.isoformat(),
        }

    def reload_templates(self) -> None:
        """重新加载模板."""
        self._templates.clear()
        self._templates.update(self._default_templates)

        if self._template_dir.exists():
            self._load_templates_from_dir()

        logger.info("Templates reloaded", template_count=len(self._templates))


# 全局Prompt管理器实例
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """获取Prompt管理器实例."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


def render_prompt(name: str, **kwargs) -> str:
    """
    便捷函数：渲染Prompt.

    Args:
        name: 模板名称
        **kwargs: 模板变量

    Returns:
        str: 渲染后的内容
    """
    manager = get_prompt_manager()
    return manager.render(name, **kwargs)