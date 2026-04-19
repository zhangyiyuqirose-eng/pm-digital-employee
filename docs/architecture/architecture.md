# 项目经理数字员工系统 - 架构设计文档

## 一、系统概述

项目经理数字员工系统（PM Digital Employee）是一个面向国有大型银行科技子公司项目管理部的智能化助手系统。系统以飞书为唯一交互入口，通过多Agent协作、RAG知识检索、智能编排等技术，实现项目管理自动化、规范化、智能化。

### 核心目标
- 释放项目经理30%+事务性工作
- 统一项目管理规范执行
- 实现风险前置预警
- 提供制度规范智能答疑

## 二、架构设计原则

### 1. 分层架构
系统采用9层分层架构，确保职责清晰、易于维护：

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 接入层        │ Feishu Bot Webhook、Callback、File Upload    │
├─────────────────────────────────────────────────────────────────┤
│ 2. API网关层     │ FastAPI、验签、幂等、trace_id、异常处理       │
├─────────────────────────────────────────────────────────────────┤
│ 3. 会话上下文层  │ 用户/群/项目上下文、对话状态机、多轮补参     │
├─────────────────────────────────────────────────────────────────┤
│ 4. 权限隔离层    │ 用户-项目权限、群-项目绑定、Skill权限校验    │
├─────────────────────────────────────────────────────────────────┤
│ 5. 编排层        │ Intent Router、Skill Registry、Orchestrator  │
├─────────────────────────────────────────────────────────────────┤
│ 6. AI能力层      │ LLM Gateway、Prompt Manager、RAG、安全防护   │
├─────────────────────────────────────────────────────────────────┤
│ 7. Skill插件层   │ 10个核心Skill，BaseSkill规范，manifest      │
├─────────────────────────────────────────────────────────────────┤
│ 8. 集成适配层    │ 项目管理、财务、DevOps、OA、飞书适配器       │
├─────────────────────────────────────────────────────────────────┤
│ 9. 数据层        │ PostgreSQL、Redis、pgvector、Celery         │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 核心设计模式

#### Repository Pattern（仓储模式）
所有数据访问通过Repository层，强制携带project_id实现项目隔离：
```python
class BaseRepository:
    async def get_by_id(self, id: str, project_id: str) -> Optional[Model]:
        # 强制project_id过滤
        return await self.session.execute(
            select(Model).where(
                Model.id == id,
                Model.project_id == project_id,
            )
        )
```

#### Skill Plugin Pattern（插件模式）
所有业务能力通过Skill插件实现，遵循统一Manifest规范：
```python
class BaseSkill:
    skill_name: str
    manifest: dict
    
    async def execute(self, context: SkillExecutionContext) -> dict:
        # 统一执行入口
        pass
```

#### Agent Orchestration Pattern（Agent编排模式）
复杂任务通过多Agent协作完成：
```python
class AgentOrchestrator:
    async def run_workflow(self, workflow: List[dict]) -> AgentResult:
        # 协调多个Agent完成复杂任务
        pass
```

### 3. 安全设计原则

#### 默认拒绝策略
所有权限检查采用"默认拒绝，显式允许"：
```python
if not await access_control.check_permission(user_id, resource, action):
    raise PermissionDeniedError()
```

#### 项目级隔离
所有查询强制携带project_id，防止跨项目数据泄露：
```python
# 所有Repository查询必须携带project_id
def get_tasks(project_id: str) -> List[Task]:
    return TaskRepository.find_by_project(project_id)
```

#### 内容安全防护
- 提示词注入检测（PromptInjectionGuard）
- SQL注入检测（InputValidator）
- XSS防护（InputValidator）
- 数据脱敏（DataMasker）
- 内容合规检查（ContentComplianceChecker）

## 三、核心模块设计

### 1. 编排层（Orchestrator）

#### IntentRouter（意图路由）
```python
class IntentRouterV2:
    async def recognize_intent(
        user_input: str,
        user_id: str,
        project_id: str,
    ) -> IntentResult:
        # 基于上下文的意图识别
        # 支持多轮补参
        pass
```

#### SkillRegistry（Skill注册中心）
```python
class SkillRegistry:
    def register(self, skill: BaseSkill) -> None:
        # Skill注册
        
    def get_skill(self, name: str) -> BaseSkill:
        # Skill发现
        
    def get_available_skills(self, user_role: str) -> List[BaseSkill]:
        # 权限感知的Skill发现
        pass
```

#### Orchestrator（编排引擎）
```python
class Orchestrator:
    async def process_message(
        user_input: str,
        user_id: str,
        project_id: str,
    ) -> dict:
        # 意图识别 → Skill执行 → 结果格式化
        pass
```

### 2. AI能力层

#### LLM Gateway（统一网关）
支持多Provider调用：
- OpenAI
- Azure OpenAI
- 智谱AI（GLM）
- 通义千问（Qwen）

```python
class LLMGateway:
    async def generate(
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        # 统一LLM调用入口
        pass
```

#### Prompt Manager（提示词管理）
```python
class PromptManager:
    def get_prompt(self, name: str) -> str:
        # 加载Prompt模板
        
    def render_prompt(self, name: str, variables: dict) -> str:
        # 渲染Prompt
        pass
```

#### Output Parser（结构化解析）
```python
class OutputParser:
    def parse_json(self, text: str) -> dict:
        # JSON解析
        
    def parse_table(self, text: str) -> List[dict]:
        # 表格解析
        pass
```

### 3. RAG检索层

#### 权限感知检索
```python
class PermissionAwareRetriever:
    async def retrieve(
        query: str,
        user_id: str,
        project_id: str,
    ) -> RAGResponse:
        # 只检索用户有权限访问的知识
        pass
```

#### 无依据不回答
```python
class RAGQAService:
    async def answer(self, request: RAGRequest) -> RAGAnswer:
        if not response.has_answer:
            return "抱歉，我没有找到相关信息..."
        
        # 回答必须带引用来源
        return f"{answer}\n\n参考来源：{sources}"
```

### 4. 多Agent层

#### Agent角色
- **PlannerAgent**：任务规划、步骤分解
- **ExecutorAgent**：具体业务执行
- **ValidatorAgent**：结果校验、合规检查
- **ReporterAgent**：报告生成、通知发送

#### Agent协作流程
```python
workflow = [
    {"agent": "planner", "task_type": "plan"},
    {"agent": "executor", "task_type": "execute"},
    {"agent": "validator", "task_type": "validate"},
    {"agent": "reporter", "task_type": "report"},
]
result = await orchestrator.run_workflow(workflow, input_data)
```

## 四、数据模型设计

### 核心实体关系

```
User ──┬── UserProjectRole ─── Project
       │
       └── ConversationSession ─── ConversationMessage
       
Project ──┬── Task
          ├── Milestone
          ├── ProjectCostBudget ─── ProjectCostActual
          ├── ProjectRisk
          ├── ProjectDocument
          └── ApprovalWorkflow
          
KnowledgeDocument ─── RetrievalTrace
```

### pgvector配置
```sql
CREATE TABLE knowledge_document (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    scope_type VARCHAR(20),
    metadata JSONB
);

CREATE INDEX ON knowledge_document 
USING ivfflat (embedding vector_cosine_ops);
```

## 五、集成设计

### 飞书集成
- Webhook接收事件
- Signature验签
- Card卡片交互
- Message消息发送

### 外部系统适配器
- 项目管理系统（ProjectSystemAdapter）
- 财务系统（FinanceSystemAdapter）
- DevOps系统（DevOpsSystemAdapter）
- OA审批系统（OASystemAdapter）

## 六、异步任务设计

### Celery任务
- 周报生成（generate_weekly_report）
- WBS生成（generate_wbs）
- 会议纪要生成（generate_meeting_minutes）
- 知识库索引（index_knowledge）

### 定时任务
- 每日风险扫描（daily_risk_scan）
- 每周成本监控（weekly_cost_monitor）
- 每月里程碑检查（monthly_milestone_check）

## 七、监控与日志

### 结构化日志
```python
logger.info(
    "Skill executed",
    skill_name=skill_name,
    user_id=user_id,
    project_id=project_id,
    trace_id=trace_id,
    duration_ms=duration,
)
```

### 审计日志
- 用户操作记录
- 项目访问记录
- Skill执行记录
- 权限检查记录

## 八、部署架构

### Docker Compose
```yaml
services:
  postgres:
    image: postgres:15
  redis:
    image: redis:7
  rabbitmq:
    image: rabbitmq:3
  app:
    build: .
  celery_worker:
    build: .
  celery_beat:
    build: .
```

### 高可用建议
- 应用层：多实例 + 负载均衡
- 数据层：PostgreSQL主从复制
- 缓存层：Redis Sentinel
- 消息队列：RabbitMQ集群