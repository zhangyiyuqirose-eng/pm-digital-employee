"""
Token管理与成本控制工具
用于LLM调用的Token统计、成本计算和用量监控
"""

import tiktoken
import json
from typing import Dict, List, Optional
from datetime import datetime


class TokenCounter:
    """Token计数器"""

    def __init__(self, model_name: str = "gpt-4"):
        try:
            self.encoder = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """计算文本Token数量"""
        return len(self.encoder.encode(text))

    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """计算消息列表的Token数量"""
        total = 0
        for msg in messages:
            total += self.count_tokens(msg.get("content", ""))
            total += self.count_tokens(msg.get("role", ""))  # role也需要计数
        return total


class CostCalculator:
    """成本计算器"""

    # 模型定价表 (单位：元/1K tokens)
    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "glm-4": {"input": 0.005, "output": 0.01},
        "qwen-max": {"input": 0.005, "output": 0.01},
        "custom-model": {"input": 0.01, "output": 0.02}
    }

    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """计算调用成本"""
        pricing = cls.PRICING.get(model.lower())
        if not pricing:
            # 默认定价
            pricing = {"input": 0.01, "output": 0.02}

        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost


class PromptTemplate:
    """Prompt模板定义"""

    def __init__(self, system_prompt: str, user_template: str, output_format: Dict[str, Any],
                 constraints: List[str], examples: Optional[List[Dict[str, str]]] = None):
        self.system_prompt = system_prompt
        self.user_template = user_template
        self.output_format = output_format
        self.constraints = constraints
        self.examples = examples or []


class PromptBuilder:
    """结构化Prompt构建器"""

    def __init__(self):
        self.templates = self._init_templates()

    def _init_templates(self) -> Dict[str, PromptTemplate]:
        """初始化内置模板"""
        return {
            "project_query": PromptTemplate(
                system_prompt=(
                    "你是一个专业的项目管理助手。你的任务是理解和回答关于项目管理的问题。\n"
                    "重要约束：\n"
                    "- 只能基于提供的信息进行回答\n"
                    "- 不能虚构信息\n"
                    "- 保持回答简洁准确\n"
                    "- 对于敏感信息需要脱敏处理"
                ),
                user_template=(
                    "当前项目信息：\n{project_info}\n\n"
                    "用户问题：{user_question}\n\n"
                    "请按照以下格式回答：\n"
                    "{{\n"
                    '  "summary": "问题摘要",\n'
                    '  "answer": "详细回答",\n'
                    '  "suggestions": ["建议1", "建议2"]\n'
                    "}}"
                ),
                output_format={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "answer": {"type": "string"},
                        "suggestions": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["summary", "answer"]
                },
                constraints=[
                    "回答必须基于已有信息",
                    "不得泄露敏感数据",
                    "答案要简洁明了"
                ]
            ),
            "task_analysis": PromptTemplate(
                system_prompt=(
                    "你是一个专业的任务分析助手。你的任务是分析任务的完成情况和进度。\n"
                    "重要约束：\n"
                    "- 只能基于提供的任务信息进行分析\n"
                    "- 不能虚构数据\n"
                    "- 保持分析客观准确\n"
                    "- 对于敏感信息需要脱敏处理"
                ),
                user_template=(
                    "当前任务信息：\n{task_info}\n\n"
                    "分析要求：{analysis_requirement}\n\n"
                    "请按照以下格式返回分析结果：\n"
                    "{{\n"
                    '  "progress": "进度百分比",\n'
                    '  "status": "状态",\n'
                    '  "issues": ["问题1", "问题2"],\n'
                    '  "recommendations": ["建议1", "建议2"]\n'
                    "}}"
                ),
                output_format={
                    "type": "object",
                    "properties": {
                        "progress": {"type": "number"},
                        "status": {"type": "string"},
                        "issues": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "recommendations": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["progress", "status"]
                },
                constraints=[
                    "分析必须基于实际任务数据",
                    "不得泄露敏感信息",
                    "分析结果要客观准确"
                ]
            )
        }

    def build_prompt(
        self,
        template_name: str,
        **kwargs
    ) -> str:
        """构建结构化Prompt"""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template {template_name} not found")

        # 格式化用户模板
        user_prompt = template.user_template.format(**kwargs)

        # 组合完整prompt
        full_prompt = f"{template.system_prompt}\n\n{user_prompt}"

        # 添加约束说明
        if template.constraints:
            constraints_str = "\n".join([f"- {constraint}" for constraint in template.constraints])
            full_prompt += f"\n\n约束条件：\n{constraints_str}"

        # 添加输出格式说明
        if template.output_format:
            full_prompt += f"\n\n输出格式要求：\n请严格按照JSON格式输出：{json.dumps(template.output_format, ensure_ascii=False, indent=2)}"

        # 添加示例（如果有）
        if template.examples:
            examples_str = "\n".join([
                f"示例：\n输入：{ex['input']}\n输出：{ex['output']}"
                for ex in template.examples
            ])
            full_prompt += f"\n\n{examples_str}"

        return full_prompt


# 全局实例
token_counter = TokenCounter()
cost_calculator = CostCalculator()
prompt_builder = PromptBuilder()