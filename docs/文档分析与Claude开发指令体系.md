# 一、先给出总体判断

这两份文档整体上已经具备了比较扎实的业务与架构基础，但存在以下典型问题:

## 1. 优点
### 第一份 51 页文档优点
- 偏**工程实现导向**，已经给了:
  - FastAPI 风格接口
  - 权限控制示例代码
  - OpenClaw 编排示例
  - PostgreSQL 表结构
  - Redis 缓存结构
  - 飞书 API 交互示例
  - Skill 生命周期管理设计
- 适合直接转为研发任务。

### 第二份 29 页文档优点
- 偏**管理视角和顶层设计**，更符合国有大行科技子公司项目管理部负责人视角。
- 强调了:
  - 岗位级闭环
  - 金融级安全合规
  - 三层权限隔离
  - RAG 合规增强
  - Multi-Agent 自主闭环
  - 审计日志
  - 可运营、可考核、可持续迭代

## 2. 主要不足
两份文档结合起来，仍有这些缺口:

### (1) 数字员工"产品定义"还不够收敛
文档列了 24~32 个 Skill，但如果一开始全做，必然项目失控。  
需要明确一个**MVP 数字员工**，建议命名为:

> **PM 数字员工(项目管理智能助理)**

并分期:
- **一期 MVP**:做 8~10 个高频、高价值、低集成难度 Skill
- **二期增强**:流程审批、合同回款、人员入离场、重点项目监控
- **三期智能化**:多 Agent 闭环、预测模型、复杂跨系统自动化

---

### (2) OpenClaw 的"技能编排机制"没有落成到代码结构级
文档提到了 Skill、生命周期、调度，但还缺:
- Skill manifest 规范
- Skill 注册协议
- Skill 输入输出 DTO
- Skill 执行上下文
- Skill 路由与编排 DSL
- Skill 版本兼容策略
- Skill 熔断 / 超时 / 降级规范

---

### (3) 飞书侧设计不够"工程化"
缺少明确的:
- 事件订阅清单
- Bot 权限 scopes 列表
- 卡片模板目录
- 单聊 / 群聊状态机
- file / card / form / callback 的统一封装

---

### (4) RAG 方案不够完整
虽然提到了 RAG，但没落到真正可实施的知识链路:
- 文档采集
- 清洁切片
- 元数据打标
- embedding
- 检索
- rerank
- 权限过滤
- 引用回传
- 合规审计

需要补足为**权限感知 RAG + 引用可追溯问答**。

---

### (5) 安全治理还不够金融级落地
需要补:
- 数据分级分类
- 字段级脱敏
- 项目域隔离策略
- 租户/项目双维度过滤
- 审计事件模型
- 提示词注入防护
- 输出内容安全审查
- 模型调用网关与私有化 LLM 适配

---

### (6) 缺少一份"能让 Claude Code 直接干活"的开发指令体系
这个正是你现在的要的重点。  
我会在后面直接给出:

> **一组可以逐步贴给 Claude Code 执行的完整提示词**  
包括:
- 项目初始化
- 目录结构
- 数据库建模
- 核心服务开发
- 飞书接入
- OpenClaw 编排
- RAG
- 多 Agent
- 安全治理
- 测试
- Docker Compose
- README
- 示例数据
- 种子脚本
- CI/CD 基础

---

# 二、建议最终收敛成的"1个数字员工"定义

从项目管理部负责人视角，不建议对外说"32 个分散技能机器人"，而建议定义为:

# **项目经理数字员工(PM Digital Employee)**
一个部署在飞书单聊与项目群内、基于 OpenClaw 技能编排框架运行的岗位级智能助理，围绕项目管理部主责主业，提供项目立项、进度、成本、风险、报告、合规、答疑与事件驱动自动化能力，具备项目级强隔离、权限感知问答、自主任务闭环与全流程审计能力。

---

# 三、建议的一期 MVP 范围

为了便于 Claude Code 先生成一套可运行系统，我建议第一阶段只实现下面 **10 个核心 Skill**:

## 1. 项目总览查询 Skill
- 查询项目基础信息、进度、成本、风险、任务统计

## 2. 周报生成 Skill
- 自动汇总项目进展、成本、风险、待办，输出 Markdown / DOCX

## 3. WBS 自动生成 Skill
- 从需求说明中抽取范围，生成结构化 WBS

## 4. 任务进度更新 Skill
- 更新任务状态、完成率、备注，触发事件

## 5. 风险识别与预警 Skill
- 规则 + LLM 双引擎识别风险

## 6. 成本监控 Skill
- 对比预算与实际，识别超支并推送预警

## 7. 制度规范答疑 Skill
- 基于 RAG 的权限感知问答

## 8. 项目情况咨询 Skill
- 权限过滤后查询任务、里程碑、成本、风险

## 9. 会议纪要生成 Skill
- 输入会议文本/记录，输出纪要+待办

## 10. 合规审核 Skill(预立项/立项材料初审)
- 检查材料完整性、规范性、风险提示

这 10 个 Skill 足以支撑 MVP 演示与试点上线。

---

# 四、综合补全后的推荐技术架构

---

## 1. 架构分层
建议最终落地如下:

### A. 接入层
- Feishu Bot Webhook
- Callback/Card Action
- File Upload Event
- Health Check

### B. API 网关层
- FastAPI
- 请求验签
- 幂等去重
- trace_id 注入
- 统一异常处理

### C. 会话与上下文层
- 用户上下文
- 群绑定上下文
- 项目上下文
- 对话状态机
- 多轮补参

### D. 权限与隔离层
- 用户-项目权限映射
- 群-项目绑定校验
- Skill 级权限校验
- SQL/API 项目过滤器
- 审计日志

### E. OpenClaw Orchestration 层
- Intent Router
- Skill Registry
- Workflow Runner
- Agent Planner
- Agent Executor
- Agent Validator
- Agent Feedback

### F. AI 能力层
- LLM Gateway
- Prompt Manager
- RAG Retrieval
- ReRank
- Structured Extraction
- Risk Analysis
- Compliance Review

### G. Skill 插件层
- 项目总览
- 周报生成
- WBS
- 进度更新
- 风险预警
- 成本监控
- 制度答疑
- 项目咨询
- 会议纪要
- 合规审核

### H. 集成适配层
- 项目管理系统适配器
- 财务系统适配器
- DevOps 适配器
- 缺陷系统适配器
- OA 审批适配器
- Feishu 文档/文件适配器

### I. 数据层
- PostgreSQL
- Redis
- Milvus / pgvector
- MongoDB(可选，若你们想简化可先不用)
- Elasticsearch / OpenSearch(审计日志，可二期)

---

## 2. 建议技术栈
为了让 Claude Code 高质量生成，建议先收敛到以下栈:

- **语言**:Python 3.11
- **Web 框架**:FastAPI
- **ORM**:SQLAlchemy 2.x + Alembic
- **校验**:Pydantic v2
- **异步任务**:Celery / Dramatiq(二选一，建议 Celery)
- **消息队列**:RabbitMQ
- **缓存**:Redis
- **数据库**:PostgreSQL
- **向量检索**:pgvector(一期优先，部署简单)
- **文档生成**:python-docx, Jinja2, markdown
- **测试**:pytest + pytest-asyncio
- **代码质量**:ruff + black + mypy
- **容器化**:Docker Compose
- **LLM 网关**:统一 abstraction，支持 OpenAI/Claude/私有模型
- **RAG**:自研 lightweight pipeline，避免 LangChain 过重
- **日志监控**:structlog + Prometheus metrics

---

# 五、从架构师角度，对附件内容做出的关键补全

---

## 1. 补全一:统一领域模型
文档里概念很多，但缺少统一 domain model。建议补成如下主实体:

- User
- Project
- UserProjectRole
- GroupProjectBinding
- SkillDefinition
- ProjectSkillSwitch
- ConversationSession
- ConversationMessage
- Task
- Milestone
- CostBudget
- CostActual
- Risk
- Report
- Document
- ApprovalWorkflow
- AuditLog
- KnowledgeDocument
- RetrievalTrace
- EventRecord

---

## 2. 补全二:统一权限模型
建议不要直接把意图名作为操作权限。  
应采用:

### 资源 + 动作模型
- Resource:
  - project
  - task
  - report
  - document
  - cost
  - risk
  - approval
  - knowledge
- Action:
  - read
  - write
  - submit
  - approve
  - execute
  - manage

### 角色映射
- project_manager
- pm
- tech_lead
- member
- auditor
- admin

### Skill 权限声明示例
```json
{
  "skill_name": "generate_weekly_report",
  "required_permissions": [
    {"resource": "report", "action": "execute"},
    {"resource": "project", "action": "read"}
  ],
  "allowed_roles": ["project_manager", "pm", "tech_lead"]
}
```

---

## 3. 补全三:权限感知 RAG
RAG 不能只是"检索后拼 Prompt"，必须做到:

- 检索前:按知识文档标签过滤
  - scope_type: public / department / project / confidential
  - project_id
  - department_id
- 检索中:按用户权限做 metadata filter
- 检索后:返回引用来源
- 输出前:做内容合规审查
- 审计中:记录"检索了哪些知识片段"

---

## 4. 补全四:多 Agent 边界
不要一开始就上复杂多 Agent 自主规划所有事情。建议采用:

### 一级:单 Skill 执行
适用于查询、更新、周报生成

### 二级:Workflow 编排
适用于预立项全流程、会议纪要闭环

### 三级:Multi-Agent 仅用于复杂场景
- Planner Agent:拆解任务
- Executor Agent:调用 Skill
- Validator Agent:校验结果
- Reporter Agent:结果汇总

---

## 5. 补全五:事件驱动闭环
附件提到了事件总线，但建议规范事件模型:

### 事件类型
- task.updated
- task.completed
- milestone.delayed
- cost.over_budget
- report.generated
- risk.detected
- approval.pending
- approval.completed
- meeting.todo.overdue

### 事件处理器
- 发送飞书预警
- 自动创建审批
- 自动生成跟踪任务
- 自动刷新监控卡片
- 自动触发日报/周报

---

## 6. 补全六:金融级安全控制
一期代码里就建议加上这些"骨架":

- 请求签名验证
- Feishu 事件幂等
- 输入参数白名单校验
- SQLAlchemy 强制 project_id 过滤
- Prompt Injection 防护器
- 输出脱敏器
- 审计日志写入中间件
- LLM 调用审计
- 文档下载/上传操作审计
- 机密字段加密存储预留

---

# 六、最重要部分:Claude Code 可直接执行的详细提示词

下面进入核心内容。

我会按**实际开发顺序**给出一套提示词。  
你可以在 Claude Code 中逐步执行。  
建议方式:

- 每一步单独开一个任务
- 让 Claude Code 先分析，再生成代码
- 每步完成后 commit 一次

---

# 七、Claude Code 使用总原则

先给 Claude Code 一个统一的总控提示词。

---

## Prompt 0:总控系统统提示词
把下面这段先发给 Claude Code，作为整个工程的总任务背景。

```text
你现在是这个项目的首席架构师 + Tech Lead + 资深 Python 全栈工程师 + 金融行业安全架构师。

请为"项目经理数字员工(PM Digital Employee)"生成一套可运行的企业级代码工程，满足以下要求:

【项目背景】
- 本系统服务于某国有大型银行科技子公司项目管理部。
- 系统运行在内网环境，以飞书为唯一用户交互入口。
- 采用 OpenClaw 风格的 Skill 技能编排架构。
- 机器人部署在飞书单聊与项目群中，帮助项目经理完成项目管理主责主业相关任务。
- 必须满足金融行业的数据安全、权限隔离、审计留痕、合规审查要求。
- 必须支持项目级强隔离:任何用户只能访问自己参与的项目;在项目群内只能访问该群绑定项目的数据，绝不允许跨项目。
- 必须支持 RAG 检索增强、权限感知问答、多轮补参、事件驱动自动化、异步任务执行。
- 必须具备可扩展的 Skill 插件机制和后续多 Agent 编排能力。

【一期 MVP 目标】
一期仅实现以下 10 个核心 Skill:
1. 项目总览查询
2. 项目周报生成
3. WBS 自动生成
4. 任务进度更新
5. 风险识别与预警
6. 成本监控
7. 项目制度规范答疑(RAG)
8. 项目情况咨询
9. 会议纪要生成
10. 预立项/立项材料合规初审

【技术栈要求】
- Python 3.11
- FastAPI
- SQLAlchemy 2.x + Alembic
- Pydantic v2
- PostgreSQL
- Redis
- RabbitMQ
- Celery
- pgvector(用于 RAG)
- Docker Compose
- pytest
- Ruff / Black / mypy
- 统一 LLM 网关，支持后续替换为私有化大模型
- 飞书开放平台接入
- 项目结构清晰、模块边界明确、便于后续扩展

【架构要求】
请严格采用分层架构:
1. app/api            接口层
2. app/core           配置、日志、安全、中间件
3. app/domain         领域模型
4. app/repositories   数据访问层
5. app/services       业务服务层
6. app/orchestrator   OpenClaw 风格编排层
7. app/skills         Skill 插件层
8. app/integrations   第三方系统集成层
9. app/rag            RAG 检索层
10. app/agents        多 Agent 能力层
11. app/tasks         异步任务层
12. app/tests         测试

【关键非功能要求】
- 项目级强隔离
- 审计日志全留痕
- 飞书消息事件验签与幂等
- 输入参数验证与提示词注入防护
- 输出内容合规校验
- 长耗时任务异步执行
- 代码具备生产级可读性与注释
- 所有关键模块要提供单元测试
- 所有配置从环境变量读取
- 输出 README、docker-compose、.env.example、初始化脚本、种子数据脚本

【代码生成方式要求】
- 先进行架构拆解，再逐步落代码
- 每一步先说明你将新增/修改哪些文件，再输出代码
- 每个文件都给出完整内容
- 对于尚未真实接入的外部系统，先提供 adapter interface + mock implementation
- 不要偷懒省略代码，不要只写伪代码
- 如有设计取舍，请直接采用最适合企业内网部署的稳健方案

请先完成以下任务:
1. 输出整体工程目录结构
2. 输出模块职责说明
3. 输出数据库 ER 设计摘要
4. 输出一期 MVP 的 API 清单
5. 输出一期 MVP 的 Skill 清单与 manifest 设计
6. 输出分阶段开发计划
不要立刻开始写代码，先完成设计说明。
```

---

# 八、第一阶段:让 Claude Code 先搭工程骨架

---

## Prompt 1:初始化工程目录与基础文件
```text
基于你刚才输出的架构设计，现在开始生成第一批代码。

任务目标:
初始化整个项目工程骨架，并生成可以直接启动的基础文件。

请完成以下内容:
1. 生成完整项目目录结构
2. 生成以下文件的完整内容:
- pyproject.toml
- requirements.txt(如果你认为 pyproject 足够，也可以不单独给 requirements)
- .env.example
- docker-compose.yml
- Dockerfile
- README.md
- alembic.ini
- app/main.py
- app/core/config.py
- app/core/logging.py
- app/core/security.py
- app/core/exceptions.py
- app/core/middleware.py
- app/api/router.py
- app/api/health.py
- app/domain/base.py
- app/tests/test_health.py

要求:
- FastAPI 可直接启动
- 提供 /health, /ready, /live 三个探活接口
- 使用 Pydantic Settings 读取配置
- 日志采用结构化 JSON 风格
- 中间件至少包括 request_id、审计日志占位、统异常处理
- docker-compose 中包含 postgres、redis、rabbitmq、app 四个服务
- PostgreSQL 预留 pgvector 扩展初始化能力
- README 中写清楚本地启动方式

输出顺序:
先列出将创建的文件清单，然后逐个给出完整代码。
```

---

## Prompt 2:补全数据库模型与 Alembic
```text
现在继续在现有工程基础上开发数据库层。

任务目标:
实现一期 MVP 所需的核心数据库模型、SQLAlchemy 2.x ORM、Alembic 初始迁移、种子数据脚本。

请完成以下内容:
1. 生成以下 ORM 模型:
- User
- Project
- UserProjectRole
- GroupProjectBinding
- SkillDefinition
- ProjectSkillSwitch
- ConversationSession
- ConversationMessage
- Task
- Milestone
- ProjectCostBudget
- ProjectCostActual
- ProjectRisk
- ProjectDocument
- ApprovalWorkflow
- AuditLog
- KnowledgeDocument
- RetrievalTrace
- EventRecord

2. 要求:
- 所有表包含 created_at、updated_at
- 核心表包含 project_id 外键或显式过滤字段
- 审计日志表要支持 user_id、project_id、action、resource_type、resource_id、result、trace_id、details
- KnowledgeDocument 支持 metadata_json、scope_type、department_id、project_id、embedding 字段(embedding 可以先占位)
- RetrievalTrace 记录每次 RAG 检索命中的文档及片段

3. 生成以下文件:
- app/db/session.py
- app/domain/models/*.py
- app/repositories/base.py
- scripts/init_db.py
- scripts/seed_demo_data.py
- alembic 初始 migration 文件

4. 额外要求:
- 使用 SQLAlchemy 2.x typed ORM 风格
- 提供基础索引设计，尤其是 user_id、project_id、chat_id、skill_name
- 设计枚举类型:角色、项目状态、任务状态、审批状态、文档状态、风险状态、事件状态

5. 生成测试:
- app/tests/test_models.py
- app/tests/test_seed_data.py

输出顺序:
先给出模型设计摘要，再列出文件清单，再输出完整代码。
```

---

# 九、第二阶段:权限隔离与审计能力

---

## Prompt 3:实现项目级强隔离与权限引擎
```text
现在继续开发安全与权限模块。

任务目标:
实现项目级强隔离、用户-项目权限校验、飞书群-项目绑定校验、Skill 权限校验、审计日志写入能力。

请新增并实现以下模块:
- app/services/access_control_service.py
- app/services/context_service.py
- app/services/audit_service.py
- app/core/project_scope.py
- app/core/dependencies.py
- app/api/deps.py

必须实现以下能力:
1. build_user_context(user_id, chat_id)
   - 获取用户信息
   - 获取群绑定项目
   - 获取用户角色
   - 获取用户可访问项目列表
   - 缓存到 Redis

2. verify_project_access(user_id, project_id, resource, action)
   - 基于角色和资源动作模型校验
   - 默认拒绝
   - 严格返回 bool 和拒绝原因

3. enforce_group_project_binding(chat_id, project_id)
   - 校验群聊只能访问绑定项目
   - 防止跨项目访问

4. check_skill_access(user_id, project_id, skill_name)
   - 检查 skill 是否对项目启用
   - 检查 skill 对角色是否开放

5. SQL / Repository 层强制 project_id 过滤机制
   - 给出一个可复用的 project scoped repository 基类
   - 防止开发人员遗漏 project_id 条件

6. 审计日志中间件
   - 记录请求入口、用户、项目、trace_id、接口、结果
   - 记录 Skill 调用事件

7. 缓存策略
   - 用户上下文 8 小时
   - 权限缓存 1 小时
   - 群绑定缓存 24 小时

8. 测试
   - test_access_control.py
   - test_context_service.py
   - test_project_scope.py

请注意:
- 这是金融级隔离核心模块，代码必须可读、稳健、默认拒绝、错误信息不泄露敏感信息
- 所有无权限场景必须给出统一错误码和用户可见消息
- 先提供 mock 的 lark user info adapter

输出顺序:
先说明权限模型设计，再输出代码。
```

---

# 十、第三阶段:飞书接入层

---

## Prompt 4:实现飞书 Bot 接入网关
```text
继续开发飞书接入层。

任务目标:
实现飞书事件接收、验签、幂等去重、消息解析、异步处理入口、消息回发封装、文件上传封装、交互卡片回调处理。

请新增并实现以下文件:
- app/integrations/lark/client.py
- app/integrations/lark/signature.py
- app/integrations/lark/schemas.py
- app/integrations/lark/service.py
- app/api/lark_webhook.py
- app/api/lark_callback.py
- app/services/idempotency_service.py
- app/tests/test_lark_signature.py
- app/tests/test_lark_webhook.py

具体要求:
1. 支持飞书 url_verification
2. 支持消息事件接收
3. 支持卡片按钮回调
4. 支持事件幂等去重(基于 event_id 或 message_id)
5. 支持发送 text / interactive / file 三类消息
6. 支持上传文件后回发到群聊或单聊
7. 支持解析 @机器人 文本消息
8. 回调接口响应必须快速返回，实际处理走异步任务或后台任务
9. 所有飞书调用统一走 client 封装，便于后续替换 SDK 或 mock
10. 输出飞书权限 scopes 建议清单和 README 中的飞书配置说明

请在代码中预留:
- tenant_access_token 获取与缓存
- 指数退避重试
- 接口异常统一封装
- trace_id 透传

输出顺序:
先说明飞书事件处理流程，再输出完整代码。
```

---

# 十一、第四阶段:OpenClaw 风格编排核心

---

## Prompt 5:实现 Skill Manifest、注册中心与编排引擎
```text
继续开发 OpenClaw 风格的编排核心。

任务目标:
实现 Skill manifest 规范、Skill 注册中心、意图识别入口、多轮补参状态机、Skill 执行器、统一返回结构。

请新增并实现以下文件:
- app/orchestrator/schemas.py
- app/orchestrator/skill_manifest.py
- app/orchestrator/skill_registry.py
- app/orchestrator/intent_router.py
- app/orchestrator/dialog_state.py
- app/orchestrator/orchestrator.py
- app/orchestrator/result_formatter.py
- app/tests/test_skill_registry.py
- app/tests/test_orchestrator.py

具体要求:
1. 定义统一 Skill Manifest 结构，至少包含:
   - skill_name
   - display_name
   - description
   - version
   - domain
   - input_schema
   - output_schema
   - allowed_roles
   - required_permissions
   - enabled_by_default
   - supports_async
   - supports_confirmation
   - dependencies

2. 定义 BaseSkill 抽象基类，要求:
   - manifest 属性
   - execute(context, params) 方法
   - optional validate(params) 方法
   - optional preview(params) 方法

3. 实现 SkillRegistry:
   - register(skill)
   - get(skill_name)
   - list_all()
   - list_available_for_user(project_id, role)

4. 实现 IntentRouter:
   - 先规则匹配
   - 再调用 LLM 网关进行意图识别
   - 返回结构化结果:intent, confidence, parameters, clarification_needed, missing_params

5. 实现多轮补参状态机:
   - 当参数缺失时保存对话状态
   - 下一轮消息自动补齐参数
   - 参数齐全后继续执行

6. 实现 Orchestrator 主流程:
   - 加载上下文
   - 权限校验
   - 群绑定校验
   - Skill 启用校验
   - 参数验证
   - 执行 Skill
   - 结果格式化
   - 审计日志
   - 统一错误处理

7. 提供 mock llm gateway，先不要接真实大模型

8. 结果格式统一支持:
   - text
   - card
   - file
   - async_task_accepted
   - clarification_needed
   - error

输出顺序:
先给出 Skill 机制设计说明，然后输出完整代码。
```

---

# 十二、第五阶段:LLM 网关与 Prompt 管理

---

## Prompt 6:实现 LLM 网关、Prompt 管理与输出约束
```text
继续开发 AI 核心模块。

任务目标:
实现统一 LLM 网关、Prompt 模板管理、结构化输出解析、内容安全检查、提示词注入防护。

请新增并实现以下文件:
- app/ai/llm_gateway.py
- app/ai/prompt_manager.py
- app/ai/output_parser.py
- app/ai/safety_guard.py
- app/ai/schemas.py
- app/tests/test_llm_gateway.py
- app/tests/test_safety_guard.py

具体要求:
1. 提供统一 LLMGateway 抽象
   - chat(messages, model, temperature, response_format)
   - structured_generate(prompt, schema)
   - embed(texts)
   - 支持 mock provider 和 openai-compatible provider 两种实现

2. PromptManager
   - 支持系统提示词模板
   - 支持 Skill 专属 prompt 模板
   - 支持模板变量渲染
   - 支持版本管理(先文件级即可)

3. OutputParser
   - 解析 JSON 结构化输出
   - 当模型输出非 JSON 时尝试修复
   - 失败时返回结构化错误

4. SafetyGuard
   - 输入安全检查:prompt injection、越权指令、敏感词
   - 输出安全检查:敏感信息、跨项目信息、无引用的制度结论
   - 提供 redact_sensitive_content 方法
   - 提供 block_if_unsafe 方法

5. 对所有 LLM 请求和响应记录审计日志占位

6. 在 README 中补充如何接入私有化大模型或 openai-compatible 模型服务

输出顺序:
先说明 LLM 层职责，再输出代码。
```

---

# 十三、第六阶段:RAG 检索增强与权限感知问答

---

## Prompt 7:实现 RAG 知识库与权限感知检索
```text
继续开发 RAG 模块。

任务目标:
实现企业项目管理制度知识库、文档入库、切片、embedding、权限过滤检索、引用回传、检索审计。

请新增并实现以下文件:
- app/rag/chunker.py
- app/rag/indexer.py
- app/rag/retriever.py
- app/rag/reranker.py
- app/rag/qa_service.py
- app/rag/schemas.py
- app/scripts/import_knowledge.py
- app/tests/test_rag_chunker.py
- app/tests/test_rag_retriever.py

具体要求:
1. 文档切片:
   - 支持按标题、段落、字数混合切片
   - 生成 chunk_id、document_id、section_path、chunk_text、metadata

2. 向量存储:
   - 一期用 pgvector
   - 如果 embedding 服务不可用，先 fallback 到 mock embedding

3. 权限感知检索:
   - 检索时必须按 scope_type / department_id / project_id 过滤
   - scope_type 支持 public / department / project / confidential
   - 用户无权限的知识文档不可被召回

4. 检索结果:
   - 返回 chunk 内容、来源文档名、章节、相似度
   - 支持 top_k 和 rerank

5. QA Service:
   - 先检索，再拼装带引用的 prompt
   - 输出中必须包含 citations
   - 对制度类答疑，没有命中知识库时禁止瞎答，必须返回"未检索到足够依据"

6. 检索审计:
   - 每次检索写入 RetrievalTrace
   - 记录 query、命中文档、项目上下文、用户上下文

7. 请提供一个 demo 知识库导入脚本，导入几份示例制度文本

输出顺序:
先说明权限感知 RAG 设计，再输出完整代码。
```

---

# 十四、第七阶段:先落 10 个核心 Skill

---

## Prompt 8:实现第一批核心 Skill
```text
继续开发 Skill 层。

任务目标:
实现一期 MVP 的 10 个核心 Skill，并完成 manifest 注册、服务层调用、统一返回。

请新增并实现以下文件:
- app/skills/base.py
- app/skills/project_overview_skill.py
- app/skills/weekly_report_skill.py
- app/skills/wbs_generation_skill.py
- app/skills/task_update_skill.py
- app/skills/risk_alert_skill.py
- app/skills/cost_monitor_skill.py
- app/skills/policy_qa_skill.py
- app/skills/project_query_skill.py
- app/skills/meeting_minutes_skill.py
- app/skills/compliance_review_skill.py
- app/skills/__init__.py
- app/tests/test_skills_*.py

各 Skill 具体要求:

1. ProjectOverviewSkill
- 返回项目基础信息、任务统计、里程碑状态、成本执行、风险数量
- 支持卡片格式结果

2. WeeklyReportSkill
- 输入 start_date, end_date, format
- 汇总任务、风险、成本、里程碑
- 生成 markdown 文本
- 预留导出 docx 的方法
- 支持异步执行

3. WBSGenerationSkill
- 输入需求文本或文档解析结果
- 生成树形 WBS
- 输出结构化 JSON 和 markdown 双版本
- 使用 LLM + 规则双重生成

4. TaskUpdateSkill
- 更新任务状态、完成率、备注
- 写任务历史
- 若完成则发布 task.completed 事件

5. RiskAlertSkill
- 规则识别延期、超支、人力不足风险
- 可选调用 LLM 进行根因分析
- 返回 top 风险列表与建议措施

6. CostMonitorSkill
- 计算预算、实际、偏差、偏差率
- 超支时发布 cost.over_budget 事件

7. PolicyQASkill
- 基于 RAG QA Service
- 输出必须带引用
- 无依据不得回答

8. ProjectQuerySkill
- 允许查询任务、里程碑、风险、成本
- 只能查询当前项目
- 支持过滤器

9. MeetingMinutesSkill
- 输入会议记录文本
- 输出会议纪要、决议事项、待办清单、责任人列表
- 使用 LLM 结构化抽取

10. ComplianceReviewSkill
- 对预立项/立项材料做完整性和合规性检查
- 规则 + RAG + LLM 综合判断
- 输出风险项、修改建议、合规结论

统一要求:
- 每个 Skill 都继承 BaseSkill
- 每个 Skill 都有 manifest
- 每个 Skill 都有 execute 方法
- 每个 Skill 都有清晰的输入输出 schema
- 技能里禁止直接访问数据库，统一通过 service/repository
- 对敏感内容做输出前安全检查

输出顺序:
先列出所有 Skill 清单与其 manifest 摘要，再输出代码。
```

---

# 十五、第八阶段:业务服务层与适配器层

---

## Prompt 9:实现服务层与第三方适配器
```text
继续开发服务层与第三方系统适配层。

任务目标:
将 Skill 与底层数据访问、外部系统访问解耦，形成标准服务层与 adapter 层。

请新增并实现以下文件:
- app/services/project_service.py
- app/services/task_service.py
- app/services/report_service.py
- app/services/risk_service.py
- app/services/cost_service.py
- app/services/document_service.py
- app/services/compliance_service.py
- app/services/event_service.py

- app/integrations/project_system/adapter.py
- app/integrations/finance_system/adapter.py
- app/integrations/devops_system/adapter.py
- app/integrations/defect_system/adapter.py
- app/integrations/oa_system/adapter.py

要求:
1. 为每个外部系统定义 adapter interface + mock 实现
2. service 层封装业务逻辑，供 skills 调用
3. 对于尚未接入的真实系统，mock 数据必须可用于本地演示
4. event_service 提供 publish_event / subscribe handler 占位设计
5. report_service 支持 markdown 转 docx 占位
6. compliance_service 支持规则清单校验 + RAG 检索增强校验

额外要求:
- 所有 service 层方法要有类型注解
- 所有 adapter 错误统一封装为 IntegrationError
- 对外部系统调用写审计日志占位

输出顺序:
先说明服务边界，再输出代码。
```

---

# 十六、第九阶段:事件驱动自动化与异步任务

---

## Prompt 10:实现 Celery 异步任务与事件驱动闭环
```text
继续开发异步任务和事件驱动能力。

任务目标:
实现 Celery、异步任务、事件总线基础能力，以及几个关键事件处理器。

请新增并实现以下文件:
- app/tasks/celery_app.py
- app/tasks/report_tasks.py
- app/tasks/event_tasks.py
- app/tasks/knowledge_tasks.py
- app/events/bus.py
- app/events/handlers.py
- app/tests/test_event_bus.py

具体要求:
1. Celery 连接 RabbitMQ / Redis
2. 周报生成、知识导入、风险扫描支持异步执行
3. 事件总线支持:
   - task.completed
   - cost.over_budget
   - risk.detected
   - report.generated
   - approval.pending

4. 实现处理器:
   - task.completed -> 推送项目群通知
   - cost.over_budget -> 给 PM 推送预警消息
   - report.generated -> 推送文件或链接
   - risk.detected -> 推送风险卡片

5. 事件记录必须写 EventRecord 表
6. 所有 handler 要做异常捕获，不允许影响主流程
7. 输出 Docker Compose 中 celery worker 服务和 beat 服务补充配置

输出顺序:
先说明事件闭环机制，再输出代码。
```

---

# 十七、第十阶段:API 与飞书消息处理主流程打通

---

## Prompt 11:打通从飞书消息到 Skill 执行的主链路
```text
现在把所有模块真正串起来。

任务目标:
实现"飞书消息 -> 上下文 -> 权限校验 -> 意图识别 -> Skill 执行 -> 结果返回飞书"的主流程。

请修改和补全以下模块:
- app/api/lark_webhook.py
- app/orchestrator/orchestrator.py
- app/integrations/lark/service.py
- app/services/message_dispatch_service.py
- app/services/session_service.py
- app/tests/test_message_flow.py

必须实现以下链路:
1. 接收飞书消息事件
2. 验签 + 去重
3. 解析 user_id、chat_id、message_text
4. 构建用户上下文
5. 检查群绑定和项目访问权限
6. 进行意图识别
7. 命中 Skill 或进入澄清流程
8. 执行 Skill
9. 格式化结果
10. 回发到飞书(text/card/file)
11. 记录 conversation_log、task_exec_record、audit_log

需要支持的用户输入示例:
- 项目总览
- 帮我生成本周周报
- 帮我更新任务 T-1001 为已完成
- 这个项目有哪些风险
- 按制度要求，预立项材料需要包含什么
- 帮我生成会议纪要

如果是长耗时任务:
- 先回复"任务处理中"
- 后台异步执行
- 完成后主动推送结果

输出顺序:
先画出主流程文字版时序说明，再输出代码。
```

---

# 十八、第十一阶段:会议、文档、卡片模板增强

---

## Prompt 12:补充飞书卡片模板和文档生成能力
```text
继续优化用户体验。

任务目标:
为一期 MVP 增加飞书卡片模板、结果渲染器、文档导出器，提升可用性。

请新增并实现以下文件:
- app/presentation/cards/base.py
- app/presentation/cards/project_overview_card.py
- app/presentation/cards/risk_alert_card.py
- app/presentation/cards/approval_status_card.py
- app/presentation/cards/clarification_card.py
- app/presentation/renderers.py
- app/utils/docx_exporter.py
- app/tests/test_cards.py

要求:
1. 定义统一 card builder 接口
2. 项目总览 Skill 输出可渲染为卡片
3. 风险预警可渲染为卡片
4. clarification_needed 场景可返回确认按钮卡片
5. 周报与会议纪要可导出 docx
6. 所有 renderer 必须与 orchestrator 的统一结果结构兼容

输出顺序:
先说明展示层设计，再输出代码。
```

---

# 十九、第十二阶段:多 Agent 闭环实现一个"复杂任务"

---

## Prompt 13:实现一个多 Agent 闭环样例 -- 预立项全流程
```text
继续开发多 Agent 能力，但仅做一个可运行样例，不要过度复杂。

任务目标:
实现"预立项全流程助手"这个多 Agent 闭环样例，作为二期能力的基础。

请新增并实现以下文件:
- app/agents/base.py
- app/agents/planner_agent.py
- app/agents/executor_agent.py
- app/agents/validator_agent.py
- app/agents/reporter_agent.py
- app/agents/pre_initiation_workflow.py
- app/tests/test_pre_initiation_workflow.py

功能要求:
用户输入:"帮我完成这个项目的预立项全流程"

系统自动执行:
1. 解析需求文本
2. 生成 WBS
3. 成本估算
4. 生成预立项材料初稿
5. 调用合规审核
6. 汇总结果并返回
7. 若某一步失败，返回失败点和人工介入建议

要求:
- PlannerAgent 只做任务拆解
- ExecutorAgent 调用已有 Skill
- ValidatorAgent 检查必要产物是否齐全
- ReporterAgent 输出最终结果摘要
- 每个 Agent 的输入输出都必须结构化
- 记录多 Agent 的执行链路日志

输出顺序:
先说明 Agent 职责边界，再输出代码。
```

---

# 二十、第十三阶段:完善安全治理

---

## Prompt 14:实现安全治理增强模块
```text
继续补强金融行业安全与合规能力。

任务目标:
实现输入校验、脱敏、敏感信息保护、审计增强、内容安全拦截等安全模块。

请新增并实现以下文件:
- app/security/input_validator.py
- app/security/data_masking.py
- app/security/content_compliance.py
- app/security/encryption.py
- app/security/prompt_injection_guard.py
- app/tests/test_security_modules.py

要求:
1. 输入校验
- 防 SQL 注入
- 防 XSS
- 防越权参数伪造
- 对外部输入做长度、字符集、危险模式检查

2. 数据脱敏
- 支持人名、手机号、身份证号、合同金额等常见敏感字段脱敏
- 支持按角色决定是否脱敏展示

3. 内容合规
- 对 LLM 输出进行规则扫描
- 对制度答疑类输出要求必须带 citation
- 对跨项目信息、敏感词、推测性表述进行拦截

4. 加密模块
- 提供字段加密接口占位
- 提供国密兼容设计说明(代码先以通用接口封装，不强绑定具体国密库)

5. 审计增强
- 记录 LLM 输入摘要、输出摘要、知识检索摘要、文件操作记录

输出顺序:
先说明安全模型，再输出代码。
```

---

# 二十一、第十四阶段:完善测试、质量、CI

---

## Prompt 15:补齐测试、lint、mypy、CI 配置
```text
继续完善工程质量体系。

任务目标:
补齐测试体系、代码规范、静态检查、基础 CI 工作流。

请新增并实现以下文件:
- .github/workflows/ci.yml
- pytest.ini
- .ruff.toml
- mypy.ini
- scripts/run_tests.sh
- scripts/lint.sh
- scripts/format.sh

并补齐测试:
- orchestrator 关键流程测试
- access control 边界测试
- rag 权限过滤测试
- skill 调用测试
- 飞书 webhook 测试
- 安全模块测试
- 至少给出一个端到端 API 测试

要求:
- 测试覆盖率目标 >= 80%
- CI 包含 lint、type check、unit test
- README 增加开发规范与测试命令

输出顺序:
先说明质量门禁设计，再输出代码。
```

---

# 二十二、第十五阶段:部署与运维文档

---

## Prompt 16:生成部署脚本、运维手册与项目文档
```text
最后请整理交付物。

任务目标:
生成适合企业内网试点部署的交付文档和脚本。

请补充或生成以下内容:
- 完整 README.md(重写为正式版)
- docs/architecture.md
- docs/security.md
- docs/feishu_integration.md
- docs/skill_development_guide.md
- docs/operations_runbook.md
- docs/api_reference.md
- scripts/bootstrap.sh
- scripts/create_admin_user.py
- scripts/import_demo_knowledge.py

README 必须包含:
1. 项目背景
2. 架构说明
3. 目录结构
4. 启动方式
5. 环境变量说明
6. 飞书配置说明
7. LLM 配置说明
8. RAG 知识导入方式
9. 测试方式
10. 常见问题
11. 后续扩展路线图

输出顺序:
先列出交付清单，再逐个输出。
```

---

# 二十三、如果你想更高效:再给 Claude Code 一个"工作方式约束提示词"

建议在正式开工前，再补一段约束，避免它偷工减料。

---

## Prompt 17:代码风格与交付约束
```text
从现在开始，请严格遵循以下输出约束:

1. 不允许只给伪代码，必须给可运行代码
2. 每次生成代码前，先说明修改点和文件清单
3. 若涉及多个文件，必须给出每个文件的完整内容
4. 不允许省略 import
5. 不允许把关键逻辑用"TODO"代替，除非是外部系统真实对接点
6. 对外部系统必须至少给 interface + mock 实现
7. 所有核心函数必须有类型注解
8. 所有关键模块必须写 docstring
9. 所有安全相关代码必须采用默认拒绝策略
10. 所有查询项目数据的 repository/service 必须显式带 project_id
11. 所有 Skill 必须继承 BaseSkill 并带 manifest
12. 所有 LLM 生成结果必须先经过结构化解析与安全校验
13. 所有面向用户的制度类回答必须带引用来源
14. 所有飞书事件处理必须具备幂等控制
15. 如发现前面设计不合理，可以主动提出更优方案，但必须给出清晰取舍理由

如果单次输出过长，请分批继续，不要省略代码。
```

---

# 二十四、建议你给 Claude Code 的实际执行顺序

实际操作中，建议按下面顺序跑:

1. Prompt 0 总控背景
2. Prompt 17 约束
3. Prompt 1 工程骨架
4. Prompt 2 数据模型
5. Prompt 3 权限隔离
6. Prompt 4 飞书接入
7. Prompt 5 编排引擎
8. Prompt 6 LLM 网关
9. Prompt 7 RAG
10. Prompt 8 核心 Skill
11. Prompt 9 服务层和适配器
12. Prompt 10 异步和事件
13. Prompt 11 主流程打通
14. Prompt 12 卡片和文档
15. Prompt 13 多 Agent 样例
16. Prompt 14 安全增强
17. Prompt 15 测试与 CI
18. Prompt 16 文档交付

---

# 二十五、从项目管理部负责人的视角，再补一句"方案包装话术"

如果你需要把这个方案向领导汇报，可以概括成下面这段:

> 本次 PM 数字员工建设，不是做一个简单问答机器人，而是建设一个面向项目管理部主责主业的岗位级数字员工。  
> 该数字员工以飞书为唯一入口，以 OpenClaw 为骨架，以 Skill 插件为能力单元，以大模型、RAG、多 Agent 和事件驱动自动化为智能中枢，围绕项目立项、进度、成本、风险、报告、合规与答疑等核心场景形成自主闭环。  
> 同时，严格落实项目级数据隔离、权限感知问答、全流程审计留痕和内容合规校验，满足国有大型银行科技子公司在金融数据安全、监管合规和规模化运营方面的要求。  
> 一期聚焦 10 个高频核心 Skill，优先解决 PM 重复性事务负担重、跨系统信息整合难、风险识别滞后、制度执行不统一等问题，形成可试点、可量化、可复制、可迭代的数字员工建设样板。

---

# 二十六、最后给你的结论

如果你问我这两份附件综合下来，**最适合 Claude Code 开发的落地方式**是什么，我的结论是:

## 最优路线
不是一次性开发"全量 32 Skill"，而是:

### 先做一个
**项目经理数字员工(PM Digital Employee)**

### 一期落地
**10 个核心 Skill + 1 条飞书主链路 + 1 套权限隔离 + 1 套 RAG + 1 套事件闭环**

### 技术实现
**FastAPI + PostgreSQL + Redis + RabbitMQ + Celery + pgvector + OpenClaw 风格编排层**

### 智能化策略
**先单 Skill + 工作流编排，复杂场景再引入多 Agent**

### 风险控制策略
**先把"权限、审计、合规、项目隔离"做扎实，再扩能力**