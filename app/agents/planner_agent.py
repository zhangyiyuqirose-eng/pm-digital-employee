"""
PM Digital Employee - Planner Agent
项目经理数字员工系统 - 规划Agent

负责分析任务、制定执行计划。
"""

from typing import Any, Dict, List

from app.agents.base import (
    AgentContext,
    AgentRole,
    AgentState,
    AgentTask,
    AgentResult,
    BaseAgent,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class PlannerAgent(BaseAgent):
    """
    规划Agent.

    负责分析任务需求，制定执行计划。
    """

    agent_name = "planner"
    agent_role = AgentRole.PLANNER
    description = "负责分析任务需求，制定执行计划和步骤"

    async def execute(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """执行规划任务."""
        task_type = task.task_type
        input_data = task.input_data

        logger.info(
            "Planner agent executing",
            task_type=task_type,
            trace_id=self.context.trace_id,
        )

        # 根据任务类型选择规划策略
        if task_type == "pre_initiation_review":
            return await self._plan_pre_initiation_review(input_data)
        elif task_type == "weekly_report":
            return await self._plan_weekly_report(input_data)
        elif task_type == "compliance_check":
            return await self._plan_compliance_check(input_data)
        else:
            return await self._plan_generic(input_data)

    async def _plan_pre_initiation_review(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """规划预立项材料审查."""
        document_content = input_data.get("document_content", "")

        # 分析文档内容，制定审查计划
        plan_prompt = f"""作为项目经理，请分析以下预立项材料，制定审查计划：

材料内容摘要：
{document_content[:1000]}

请制定一个包含以下步骤的审查计划：
1. 完整性检查 - 检查材料是否齐全
2. 合规性检查 - 检查是否符合公司规范
3. 可行性分析 - 评估项目可行性
4. 风险识别 - 识别潜在风险

请输出JSON格式的审查计划。
"""

        plan_result = await self.think(plan_prompt)

        return AgentResult(
            success=True,
            output={
                "plan_type": "pre_initiation_review",
                "steps": [
                    {
                        "step": 1,
                        "name": "completeness_check",
                        "description": "完整性检查",
                        "agent": "validator",
                    },
                    {
                        "step": 2,
                        "name": "compliance_check",
                        "description": "合规性检查",
                        "agent": "validator",
                    },
                    {
                        "step": 3,
                        "name": "feasibility_analysis",
                        "description": "可行性分析",
                        "agent": "executor",
                    },
                    {
                        "step": 4,
                        "name": "risk_identification",
                        "description": "风险识别",
                        "agent": "executor",
                    },
                ],
                "plan_detail": plan_result,
            },
            next_action="execute_plan",
        )

    async def _plan_weekly_report(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """规划周报生成."""
        return AgentResult(
            success=True,
            output={
                "plan_type": "weekly_report",
                "steps": [
                    {
                        "step": 1,
                        "name": "collect_data",
                        "description": "收集项目数据",
                        "agent": "executor",
                    },
                    {
                        "step": 2,
                        "name": "generate_report",
                        "description": "生成报告内容",
                        "agent": "executor",
                    },
                    {
                        "step": 3,
                        "name": "validate_report",
                        "description": "校验报告内容",
                        "agent": "validator",
                    },
                ],
            },
            next_action="execute_plan",
        )

    async def _plan_compliance_check(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """规划合规检查."""
        return AgentResult(
            success=True,
            output={
                "plan_type": "compliance_check",
                "steps": [
                    {
                        "step": 1,
                        "name": "extract_requirements",
                        "description": "提取合规要求",
                        "agent": "executor",
                    },
                    {
                        "step": 2,
                        "name": "check_compliance",
                        "description": "检查合规项",
                        "agent": "validator",
                    },
                    {
                        "step": 3,
                        "name": "generate_report",
                        "description": "生成检查报告",
                        "agent": "reporter",
                    },
                ],
            },
            next_action="execute_plan",
        )

    async def _plan_generic(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """通用规划."""
        # 使用LLM生成计划
        plan_prompt = f"""请为以下任务制定执行计划：

任务类型：{input_data.get('task_type', '未知')}
任务描述：{input_data.get('description', '无')}

请制定一个分步骤的执行计划，以JSON格式输出。
"""

        plan_result = await self.think(plan_prompt)

        return AgentResult(
            success=True,
            output={
                "plan_type": "generic",
                "plan_detail": plan_result,
            },
            next_action="execute_plan",
        )


class ExecutorAgent(BaseAgent):
    """
    执行Agent.

    负责执行具体的业务操作。
    """

    agent_name = "executor"
    agent_role = AgentRole.EXECUTOR
    description = "负责执行具体的业务操作和数据处理"

    async def execute(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """执行任务."""
        task_type = task.task_type
        input_data = task.input_data

        logger.info(
            "Executor agent executing",
            task_type=task_type,
            trace_id=self.context.trace_id,
        )

        if task_type == "feasibility_analysis":
            return await self._analyze_feasibility(input_data)
        elif task_type == "risk_identification":
            return await self._identify_risks(input_data)
        elif task_type == "collect_data":
            return await self._collect_data(input_data)
        elif task_type == "generate_report":
            return await self._generate_report(input_data)
        else:
            return await self._execute_generic(input_data)

    async def _analyze_feasibility(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """分析可行性."""
        analysis_prompt = f"""请分析以下项目的可行性：

项目信息：{input_data.get('project_info', '')}

从以下维度分析：
1. 技术可行性
2. 资源可行性
3. 时间可行性
4. 经济可行性

请输出分析结果。
"""

        result = await self.think(analysis_prompt)

        return AgentResult(
            success=True,
            output={
                "feasibility_analysis": result,
                "is_feasible": True,  # 简化处理
            },
        )

    async def _identify_risks(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """识别风险."""
        risk_prompt = f"""请识别以下项目的潜在风险：

项目信息：{input_data.get('project_info', '')}

请列出主要风险项，包括风险描述、影响程度、发生概率。
"""

        result = await self.think(risk_prompt)

        return AgentResult(
            success=True,
            output={
                "risks": result,
            },
        )

    async def _collect_data(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """收集数据."""
        # TODO: 实际的数据收集逻辑
        return AgentResult(
            success=True,
            output={
                "collected_data": {
                    "tasks": [],
                    "milestones": [],
                    "risks": [],
                },
            },
        )

    async def _generate_report(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """生成报告."""
        report_prompt = f"""请根据以下数据生成报告：

数据：{input_data.get('data', '')}

请生成一份结构化的报告。
"""

        result = await self.think(report_prompt)

        return AgentResult(
            success=True,
            output={
                "report_content": result,
            },
        )

    async def _execute_generic(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """通用执行."""
        return AgentResult(
            success=True,
            output={"result": "executed"},
        )


class ValidatorAgent(BaseAgent):
    """
    校验Agent.

    负责校验数据、结果、合规性。
    """

    agent_name = "validator"
    agent_role = AgentRole.VALIDATOR
    description = "负责校验数据完整性、结果准确性、合规性"

    async def execute(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """执行校验任务."""
        task_type = task.task_type
        input_data = task.input_data

        logger.info(
            "Validator agent executing",
            task_type=task_type,
            trace_id=self.context.trace_id,
        )

        if task_type == "completeness_check":
            return await self._check_completeness(input_data)
        elif task_type == "compliance_check":
            return await self._check_compliance(input_data)
        elif task_type == "validate_report":
            return await self._validate_report(input_data)
        else:
            return await self._validate_generic(input_data)

    async def _check_completeness(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """检查完整性."""
        document = input_data.get("document", {})

        # 检查必填字段
        required_fields = input_data.get("required_fields", [])
        missing_fields = []

        for field in required_fields:
            if field not in document or not document[field]:
                missing_fields.append(field)

        is_complete = len(missing_fields) == 0

        return AgentResult(
            success=True,
            output={
                "is_complete": is_complete,
                "missing_fields": missing_fields,
                "completeness_score": 1 - len(missing_fields) / max(len(required_fields), 1),
            },
        )

    async def _check_compliance(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """检查合规性."""
        document = input_data.get("document", {})
        rules = input_data.get("compliance_rules", [])

        violations = []

        # TODO: 实际的合规检查逻辑
        # 这里使用LLM进行智能检查
        check_prompt = f"""请检查以下内容是否符合合规要求：

内容：{document}
合规要求：{rules}

请输出检查结果，包括是否符合以及不符合的具体项。
"""

        check_result = await self.think(check_prompt)

        return AgentResult(
            success=True,
            output={
                "is_compliant": len(violations) == 0,
                "violations": violations,
                "check_result": check_result,
            },
        )

    async def _validate_report(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """校验报告."""
        report = input_data.get("report", "")

        validation_prompt = f"""请校验以下报告的准确性和完整性：

{report}

请检查：
1. 数据是否准确
2. 内容是否完整
3. 逻辑是否连贯

请输出校验结果。
"""

        result = await self.think(validation_prompt)

        return AgentResult(
            success=True,
            output={
                "is_valid": True,
                "validation_result": result,
            },
        )

    async def _validate_generic(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """通用校验."""
        return AgentResult(
            success=True,
            output={"is_valid": True},
        )


class ReporterAgent(BaseAgent):
    """
    汇报Agent.

    负责生成最终报告和通知。
    """

    agent_name = "reporter"
    agent_role = AgentRole.REPORTER
    description = "负责生成最终报告和发送通知"

    async def execute(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """执行汇报任务."""
        task_type = task.task_type
        input_data = task.input_data

        logger.info(
            "Reporter agent executing",
            task_type=task_type,
            trace_id=self.context.trace_id,
        )

        if task_type == "generate_final_report":
            return await self._generate_final_report(input_data)
        elif task_type == "send_notification":
            return await self._send_notification(input_data)
        else:
            return await self._report_generic(input_data)

    async def _generate_final_report(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """生成最终报告."""
        intermediate_results = input_data.get("intermediate_results", {})

        report_prompt = f"""请根据以下中间结果生成最终报告：

{intermediate_results}

请生成一份完整、结构化的报告。
"""

        report = await self.think(report_prompt)

        return AgentResult(
            success=True,
            output={
                "final_report": report,
            },
            artifacts={
                "report_type": "final",
                "generated_at": str(self.context.updated_at),
            },
        )

    async def _send_notification(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """发送通知."""
        message = input_data.get("message", "")
        recipients = input_data.get("recipients", [])

        # TODO: 实际的通知发送逻辑
        logger.info(
            "Sending notification",
            message=message[:100],
            recipients=recipients,
        )

        return AgentResult(
            success=True,
            output={
                "notification_sent": True,
                "recipients": recipients,
            },
        )

    async def _report_generic(
        self,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """通用汇报."""
        return AgentResult(
            success=True,
            output={"reported": True},
        )