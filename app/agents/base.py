"""
PM Digital Employee - Agent Base
项目经理数字员工系统 - Agent基类

定义多Agent协作的基础架构。
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentRole(str, Enum):
    """Agent角色."""

    PLANNER = "planner"  # 规划者
    EXECUTOR = "executor"  # 执行者
    VALIDATOR = "validator"  # 校验者
    REPORTER = "reporter"  # 汇报者
    COORDINATOR = "coordinator"  # 协调者


class AgentState(str, Enum):
    """Agent状态."""

    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentContext:
    """
    Agent执行上下文.

    在Agent之间传递的共享状态。
    """

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    project_id: Optional[str] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    final_result: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AgentTask:
    """
    Agent任务.

    分配给Agent执行的具体任务。
    """

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    description: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    status: AgentState = AgentState.IDLE
    assigned_to: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


@dataclass
class AgentResult:
    """
    Agent执行结果.
    """

    success: bool = True
    output: Dict[str, Any] = field(default_factory=dict)
    next_action: Optional[str] = None
    message: str = ""
    needs_human_input: bool = False
    artifacts: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Agent基类.

    所有Agent必须继承此基类。
    """

    agent_name: str = ""
    agent_role: AgentRole = AgentRole.EXECUTOR
    description: str = ""

    def __init__(
        self,
        context: Optional[AgentContext] = None,
    ) -> None:
        """
        初始化Agent.

        Args:
            context: 执行上下文
        """
        self._context = context or AgentContext()
        self._state = AgentState.IDLE
        self._memory: Dict[str, Any] = {}

    @property
    def context(self) -> AgentContext:
        """获取上下文."""
        return self._context

    @property
    def state(self) -> AgentState:
        """获取状态."""
        return self._state

    @property
    def memory(self) -> Dict[str, Any]:
        """获取记忆."""
        return self._memory

    def set_context(self, context: AgentContext) -> None:
        """设置上下文."""
        self._context = context

    def update_memory(self, key: str, value: Any) -> None:
        """更新记忆."""
        self._memory[key] = value

    def get_memory(self, key: str, default: Any = None) -> Any:
        """获取记忆."""
        return self._memory.get(key, default)

    @abstractmethod
    async def execute(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        执行任务.

        Args:
            task: 任务对象

        Returns:
            AgentResult: 执行结果
        """
        pass

    async def run(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        运行Agent（包含状态管理）.

        Args:
            task: 任务对象

        Returns:
            AgentResult: 执行结果
        """
        self._state = AgentState.WORKING

        try:
            result = await self.execute(task)

            if result.success:
                self._state = AgentState.COMPLETED
            else:
                self._state = AgentState.FAILED

            return result

        except Exception as e:
            self._state = AgentState.FAILED

            return AgentResult(
                success=False,
                message=f"Agent执行失败: {str(e)}",
            )

    async def think(self, prompt: str) -> str:
        """
        Agent思考（调用LLM）.

        Args:
            prompt: 思考提示

        Returns:
            str: 思考结果
        """
        from app.ai.llm_gateway import get_llm_gateway

        llm_gateway = get_llm_gateway()

        response = await llm_gateway.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
        )

        return response.content

    def can_handle(self, task: AgentTask) -> bool:
        """
        判断是否能处理该任务.

        Args:
            task: 任务对象

        Returns:
            bool: 是否能处理
        """
        return True  # 默认可以处理所有任务

    def create_sub_task(
        self,
        task_type: str,
        description: str,
        input_data: Dict[str, Any],
    ) -> AgentTask:
        """
        创建子任务.

        Args:
            task_type: 任务类型
            description: 任务描述
            input_data: 输入数据

        Returns:
            AgentTask: 子任务对象
        """
        return AgentTask(
            task_type=task_type,
            description=description,
            input_data=input_data,
        )


class AgentOrchestrator:
    """
    Agent编排器.

    协调多个Agent完成复杂任务。
    """

    def __init__(self) -> None:
        """初始化编排器."""
        self._agents: Dict[str, BaseAgent] = {}
        self._context = AgentContext()

    def register_agent(self, agent: BaseAgent) -> None:
        """注册Agent."""
        self._agents[agent.agent_name] = agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """获取Agent."""
        return self._agents.get(name)

    async def run_workflow(
        self,
        workflow: List[Dict[str, Any]],
        initial_input: Dict[str, Any],
    ) -> AgentResult:
        """
        运行工作流.

        Args:
            workflow: 工作流定义
            initial_input: 初始输入

        Returns:
            AgentResult: 最终结果
        """
        self._context.input_data = initial_input
        current_result: Optional[AgentResult] = None

        for step in workflow:
            agent_name = step.get("agent")
            task_type = step.get("task_type", "")
            input_mapping = step.get("input_mapping", {})

            agent = self.get_agent(agent_name)
            if not agent:
                return AgentResult(
                    success=False,
                    message=f"Agent not found: {agent_name}",
                )

            # 构建任务输入
            task_input = {}
            for target_key, source_path in input_mapping.items():
                value = self._resolve_value(source_path, current_result)
                task_input[target_key] = value

            # 创建并执行任务
            task = AgentTask(
                task_type=task_type,
                input_data=task_input,
            )

            agent.set_context(self._context)
            current_result = await agent.run(task)

            # 存储中间结果
            if current_result and current_result.success:
                self._context.intermediate_results[agent_name] = current_result.output

            # 如果失败，终止工作流
            if not current_result or not current_result.success:
                break

        # 构建最终结果
        if current_result:
            self._context.final_result = current_result.output
            return current_result

        return AgentResult(
            success=False,
            message="Workflow execution failed",
        )

    def _resolve_value(
        self,
        path: str,
        current_result: Optional[AgentResult],
    ) -> Any:
        """解析路径获取值."""
        parts = path.split(".")

        if parts[0] == "input":
            return self._get_nested_value(
                self._context.input_data,
                parts[1:],
            )
        elif parts[0] == "context":
            return self._get_nested_value(
                self._context.intermediate_results,
                parts[1:],
            )
        elif parts[0] == "result" and current_result:
            return self._get_nested_value(
                current_result.output,
                parts[1:],
            )

        return None

    def _get_nested_value(
        self,
        data: Dict[str, Any],
        keys: List[str],
    ) -> Any:
        """获取嵌套值."""
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value


# 全局编排器实例
_agent_orchestrator: Optional[AgentOrchestrator] = None


def get_agent_orchestrator() -> AgentOrchestrator:
    """获取Agent编排器."""
    global _agent_orchestrator
    if _agent_orchestrator is None:
        _agent_orchestrator = AgentOrchestrator()
    return _agent_orchestrator