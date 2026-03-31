# 项目经理数字员工系统 - Skill开发指南

## 一、Skill概述

Skill是项目经理数字员工系统的核心业务能力单元，每个Skill代表一个独立的功能模块。系统采用插件化架构，所有业务能力通过Skill实现。

### Skill设计原则
1. **单一职责**：每个Skill只负责一个业务功能
2. **统一规范**：所有Skill必须继承BaseSkill并提供Manifest
3. **权限感知**：Skill必须声明所需权限，执行时校验权限
4. **项目隔离**：Skill执行时强制携带project_id

## 二、Skill基类设计

### 1. BaseSkill抽象类

```python
class BaseSkill:
    """Skill基类."""
    
    skill_name: str           # Skill唯一标识
    display_name: str         # 显示名称
    description: str          # 功能描述（用于意图识别）
    
    @property
    def manifest(self) -> dict:
        """获取Skill Manifest."""
        pass
    
    def validate_input(self, input_data: dict) -> Tuple[bool, List[str]]:
        """校验输入数据."""
        pass
    
    async def execute(self, context: SkillExecutionContext) -> dict:
        """执行Skill."""
        pass
    
    async def run(self, context: SkillExecutionContext) -> dict:
        """运行Skill（包含校验和执行）."""
        pass
```

### 2. SkillExecutionContext

```python
class SkillExecutionContext:
    """Skill执行上下文."""
    
    user_id: str              # 用户ID
    project_id: str           # 项目ID（必填）
    session_id: str           # 会话ID
    input_data: dict          # 输入数据
    intermediate_results: dict # 中间结果
    trace_id: str             # 追踪ID
```

## 三、Skill Manifest规范

### 1. Manifest字段说明

```json
{
    "skill_name": "唯一标识_英文下划线",
    "display_name": "显示名称_中文",
    "description": "功能详细描述_用于意图识别",
    "version": "语义化版本号",
    "domain": "所属业务域",
    "input_schema": {
        "type": "object",
        "properties": {...},
        "required": [...]
    },
    "output_schema": {
        "type": "object",
        "properties": {...}
    },
    "allowed_roles": ["project_manager", "pm", "tech_lead", "member"],
    "required_permissions": [
        {"resource": "project", "action": "read"}
    ],
    "enabled_by_default": true,
    "supports_async": false,
    "supports_confirmation": false,
    "dependencies": []
}
```

### 2. Manifest字段详解

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skill_name | string | 是 | Skill唯一标识，英文下划线格式 |
| display_name | string | 是 | 显示名称，中文 |
| description | string | 是 | 功能描述，用于意图识别 |
| version | string | 是 | 版本号，如"1.0.0" |
| domain | string | 否 | 业务域，如"project"、"task"、"risk" |
| input_schema | object | 是 | 输入数据Schema |
| output_schema | object | 是 | 输出数据Schema |
| allowed_roles | array | 是 | 允许使用的角色列表 |
| required_permissions | array | 是 | 所需权限列表 |
| enabled_by_default | boolean | 否 | 默认是否启用 |
| supports_async | boolean | 否 | 是否支持异步执行 |
| supports_confirmation | boolean | 否 | 是否需要用户确认 |
| dependencies | array | 否 | 依赖的其他Skill |

## 四、Skill开发示例

### 1. 创建新的Skill

```python
from app.skills.base import BaseSkill, SkillManifestBuilder
from app.orchestrator.schemas import SkillExecutionContext

class MyCustomSkill(BaseSkill):
    """自定义Skill示例."""
    
    skill_name = "my_custom_skill"
    display_name = "自定义技能"
    description = "这是一个自定义技能，用于演示Skill开发"
    
    def __init__(self):
        super().__init__()
        self._manifest = self._build_manifest()
    
    def _build_manifest(self) -> dict:
        builder = SkillManifestBuilder(
            skill_name=self.skill_name,
            display_name=self.display_name,
            description=self.description,
        )
        
        # 添加输入字段
        builder.add_input_field(
            name="input_param",
            type="string",
            description="输入参数",
            required=True,
        )
        
        # 添加输出字段
        builder.add_output_field(
            name="output_result",
            type="string",
            description="输出结果",
        )
        
        # 添加权限要求
        builder.add_permission(resource="project", action="read")
        
        # 设置允许的角色
        builder.allowed_roles = ["project_manager", "pm", "tech_lead"]
        
        return builder.build()
    
    def validate_input(self, input_data: dict) -> Tuple[bool, List[str]]:
        errors = []
        
        if "input_param" not in input_data:
            errors.append("缺少必填参数: input_param")
        
        return len(errors) == 0, errors
    
    async def execute(self, context: SkillExecutionContext) -> dict:
        # 1. 获取输入参数
        input_param = context.input_data.get("input_param")
        
        # 2. 业务逻辑处理
        result = await self._process(input_param, context)
        
        # 3. 返回结果
        return {
            "output_result": result,
            "status": "success",
        }
    
    async def _process(self, input_param: str, context: SkillExecutionContext) -> str:
        # 具体业务逻辑
        # 可以调用其他服务、Repository、LLM等
        return f"处理结果: {input_param}"
```

### 2. 使用LLM的Skill

```python
class LLMBasedSkill(BaseSkill):
    """使用LLM的Skill示例."""
    
    async def execute(self, context: SkillExecutionContext) -> dict:
        # 获取LLM Gateway
        from app.ai.llm_gateway import get_llm_gateway
        
        llm_gateway = get_llm_gateway()
        
        # 构建Prompt
        prompt = self._build_prompt(context.input_data)
        
        # 调用LLM
        response = await llm_gateway.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
        )
        
        # 解析结果
        parsed_result = self._parse_response(response.content)
        
        return {
            "llm_result": parsed_result,
            "raw_response": response.content,
        }
    
    def _build_prompt(self, input_data: dict) -> str:
        return f"请根据以下信息生成结果:\n{input_data}"
    
    def _parse_response(self, content: str) -> dict:
        # 使用OutputParser解析
        from app.ai.output_parser import OutputParser
        
        parser = OutputParser()
        return parser.parse_json(content)
```

### 3. 使用RAG的Skill

```python
class RAGBasedSkill(BaseSkill):
    """使用RAG的Skill示例."""
    
    async def execute(self, context: SkillExecutionContext) -> dict:
        # 获取RAG QA服务
        from app.rag.qa_service import RAGQAService
        from app.rag.schemas import RAGRequest
        
        qa_service = RAGQAService()
        
        # 构建请求
        request = RAGRequest(
            query=context.input_data.get("query"),
            user_id=context.user_id,
            project_id=context.project_id,
            top_k=5,
        )
        
        # 执行检索问答
        response = await qa_service.answer(request)
        
        return {
            "answer": response.answer,
            "sources": response.sources,
            "has_answer": response.has_answer,
        }
```

### 4. 异步执行的Skill

```python
class AsyncSkill(BaseSkill):
    """支持异步执行的Skill示例."""
    
    def _build_manifest(self) -> dict:
        builder = SkillManifestBuilder(
            skill_name="async_skill",
            display_name="异步技能",
            description="需要异步执行的技能",
        )
        builder.supports_async = True
        return builder.build()
    
    async def execute(self, context: SkillExecutionContext) -> dict:
        # 创建异步任务
        from app.tasks.celery_app import celery_app
        
        task = celery_app.send_task(
            "process_long_task",
            args=[context.input_data],
            kwargs={"project_id": context.project_id},
        )
        
        # 返回任务ID
        return {
            "task_id": task.id,
            "status": "processing",
            "message": "任务已提交，请稍后查看结果",
        }
```

## 五、Skill注册流程

### 1. 自动注册

在 `app/skills/__init__.py` 中自动注册：

```python
from app.skills.base import SkillRegistry
from app.skills.my_custom_skill import MyCustomSkill

# 自动注册
registry = SkillRegistry()
registry.register(MyCustomSkill())
registry.register(LLMBasedSkill())
registry.register(RAGBasedSkill())
```

### 2. 手动注册

```python
from app.orchestrator.skill_registry import SkillRegistry

registry = SkillRegistry()
skill = MyCustomSkill()
registry.register(skill)
```

## 六、Skill测试规范

### 1. 单元测试

```python
import pytest
from unittest.mock import AsyncMock, patch

from app.skills.my_custom_skill import MyCustomSkill
from app.orchestrator.schemas import SkillExecutionContext

class TestMyCustomSkill:
    def test_validate_input_success(self):
        skill = MyCustomSkill()
        valid, errors = skill.validate_input({"input_param": "test"})
        assert valid is True
    
    def test_validate_input_missing_param(self):
        skill = MyCustomSkill()
        valid, errors = skill.validate_input({})
        assert valid is False
        assert "input_param" in errors[0]
    
    @pytest.mark.asyncio
    async def test_execute(self):
        skill = MyCustomSkill()
        context = SkillExecutionContext(
            user_id="test_user",
            project_id="test_project",
            session_id="test_session",
            input_data={"input_param": "test_value"},
        )
        
        result = await skill.execute(context)
        assert result["status"] == "success"
```

### 2. 集成测试

```python
@pytest.mark.asyncio
async def test_skill_full_execution():
    from app.orchestrator.orchestrator import Orchestrator
    from app.orchestrator.skill_registry import SkillRegistry
    
    registry = SkillRegistry()
    skill = MyCustomSkill()
    registry.register(skill)
    
    orchestrator = Orchestrator(registry)
    
    result = await orchestrator.execute_skill(
        skill_name="my_custom_skill",
        user_id="test_user",
        project_id="test_project",
        input_data={"input_param": "test"},
    )
    
    assert result["output_result"] is not None
```

## 七、Skill开发最佳实践

### 1. 输入校验
- 必填参数校验
- 参数类型校验
- 参数范围校验

### 2. 权限声明
- 声明所需权限
- 执行前权限校验
- 项目级权限校验

### 3. 错误处理
- 使用自定义异常
- 提供清晰的错误信息
- 记录错误日志

### 4. 日志记录
- 记录执行开始
- 记录关键步骤
- 记录执行结果

### 5. 性能优化
- 避免重复查询
- 使用缓存
- 耗时操作异步执行

### 6. 安全考虑
- 输入数据净化
- 输出数据脱敏
- 提示词注入防护