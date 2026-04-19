PM机器人系统 - ClaudeCode开发提示词集（专业架构师版）

##  整体规划说明

作为系统架构师，我已详细分析了PM机器人需求规格说明书，将开发任务拆解为**5个递进阶段**，每个阶段都有明确的交付物、验收标准和详细的ClaudeCode可执行提示词。

### 开发阶段总览

| 阶段 | 内容 | 预计交付 | 关键技术点 |
|------|------|---------|-----------|
| **Part 1** | 项目脚手架与基础设施 | 项目结构、配置、Docker、数据库 | FastAPI、PostgreSQL、Redis、Alembic |
| **Part 2** | 飞书集成与权限隔离核心 | 飞书Bot、消息处理、权限管理 | 飞书Open API v2、RBAC |
| **Part 3** | OpenClaw编排引擎与Skill框架 | Agent编排、Skill动态加载 | LLM、意图识别、Skill注册 |
| **Part 4** | 业务Skills批量开发 | 40+具体业务能力 | RAG、文档生成、EVM |
| **Part 5** | 数据维护通道与测试部署 | 多通道数据维护、监控、CI/CD | Bitable、OA对接、K8s |

---

#  Part 1：项目脚手架与基础设施搭建

> **目标**：建立完整的项目骨架，包括目录结构、依赖管理、配置中心、数据库模型、Docker环境
>
> **预计耗时**：1-2天
>
> **前置条件**：已安装 Python 3.11+、Docker Desktop、Git

---

## 提示词 1.1：初始化项目结构与基础配置

```
你是一位资深Python架构师，请为"PM机器人数字员工"项目创建完整的项目脚手架。

【项目背景】
这是一个基于FastAPI + OpenClaw + 飞书的企业级数字员工系统，需要支持高并发、模块化、可扩展的架构。

【任务要求】
请创建以下项目结构和文件：

1. 根目录结构：
pm-robot/
├── app/                          # 应用主目录
│   ├── __init__.py
│   ├── main.py                   # FastAPI应用入口
│   ├── core/                     # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理（基于pydantic-settings）
│   │   ├── logger.py             # 日志配置（loguru）
│   │   ├── exceptions.py         # 自定义异常体系
│   │   ├── security.py           # 安全工具（签名验证等）
│   │   └── constants.py          # 常量定义
│   ├── api/                      # API路由层
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py         # 路由汇总
│   │   │   ├── lark_webhook.py   # 飞书webhook入口
│   │   │   ├── admin.py          # 管理API
│   │   │   ├── skills.py         # Skills管理API
│   │   │   └── health.py         # 健康检查
│   │   └── deps.py               # 依赖注入
│   ├── models/                   # 数据库模型
│   │   ├── __init__.py
│   │   ├── base.py               # SQLAlchemy基类
│   │   ├── project.py
│   │   ├── user.py
│   │   ├── task.py
│   │   ├── skill.py
│   │   ├── document.py
│   │   ├── audit.py
│   │   └── ... (其他模型)
│   ├── schemas/                  # Pydantic Schema
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── lark.py
│   │   └── ...
│   ├── services/                 # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── project_service.py
│   │   ├── permission_service.py
│   │   └── ...
│   ├── repositories/             # 数据访问层（Repository模式）
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── project_repo.py
│   ├── integrations/             # 外部系统集成
│   │   ├── __init__.py
│   │   ├── lark/                 # 飞书集成
│   │   ├── openclaw/             # OpenClaw集成
│   │   ├── llm/                  # 大模型集成
│   │   └── oa/                   # OA系统集成
│   ├── orchestrator/             # OpenClaw编排引擎
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── intent_recognizer.py
│   │   └── ...
│   ├── skills/                   # Skill实现
│   │   ├── __init__.py
│   │   ├── base.py               # Skill基类
│   │   ├── registry.py           # Skill注册中心
│   │   ├── integration_mgmt/     # 整合管理
│   │   ├── scope_mgmt/           # 范围管理
│   │   ├── schedule_mgmt/        # 进度管理
│   │   ├── cost_mgmt/            # 成本管理
│   │   ├── quality_mgmt/         # 质量管理
│   │   ├── resource_mgmt/        # 资源管理
│   │   ├── communication_mgmt/   # 沟通管理
│   │   ├── risk_mgmt/            # 风险管理
│   │   ├── procurement_mgmt/     # 采购管理
│   │   └── stakeholder_mgmt/     # 干系人管理
│   ├── db/                       # 数据库连接
│   │   ├── __init__.py
│   │   ├── session.py            # SQLAlchemy session
│   │   └── redis_client.py       # Redis客户端
│   ├── tasks/                    # 异步任务（Celery）
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── scheduled_tasks.py
│   └── utils/                    # 工具类
│       ├── __init__.py
│       ├── datetime_utils.py
│       ├── crypto_utils.py
│       └── validators.py
├── alembic/                      # 数据库迁移
├── tests/                        # 测试代码
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── scripts/                      # 脚本工具
│   ├── init_db.py
│   ├── seed_data.py
│   └── ...
├── docker/                       # Docker配置
│   ├── Dockerfile
│   ├── Dockerfile.worker
│   └── nginx.conf
├── docs/                         # 文档
│   ├── api/
│   ├── architecture/
│   └── deployment/
├── .env.example                  # 环境变量示例
├── .gitignore
├── .dockerignore
├── docker-compose.yml            # 开发环境
├── docker-compose.prod.yml       # 生产环境
├── pyproject.toml                # 项目配置（使用Poetry）
├── alembic.ini
├── pytest.ini
├── Makefile                      # 常用命令封装
└── README.md

2. 创建 pyproject.toml，包含以下依赖：
   - 核心：fastapi>=0.110.0, uvicorn[standard]>=0.27.0, pydantic>=2.6.0, pydantic-settings>=2.2.0
   - 数据库：sqlalchemy>=2.0.0, asyncpg>=0.29.0, alembic>=1.13.0, redis>=5.0.0
   - 飞书：lark-oapi>=1.2.0
   - LLM：openai>=1.12.0, langchain>=0.1.0
   - 任务队列：celery>=5.3.0, kombu>=5.3.0
   - 工具：loguru>=0.7.0, httpx>=0.26.0, tenacity>=8.2.0, python-multipart>=0.0.9
   - 文档处理：python-docx>=1.1.0, openpyxl>=3.1.0
   - 测试：pytest>=8.0.0, pytest-asyncio>=0.23.0, pytest-cov>=4.1.0, faker>=24.0.0

3. 创建 .env.example，包含所有必要的环境变量分组：
   - APP（应用配置）
   - DATABASE（PostgreSQL）
   - REDIS
   - LARK（飞书）
   - OPENCLAW
   - LLM（大模型）
   - SECURITY
   - LOG

4. 创建 .gitignore（Python标准+IDE文件+敏感信息）

5. 创建 Makefile，包含命令：install, dev, test, lint, format, migrate, docker-up, docker-down, clean

6. 创建 README.md，包含项目简介、技术栈、快速开始、目录说明、开发规范

【代码规范】
- 所有Python文件包含模块docstring说明
- 所有目录包含 __init__.py
- 使用类型注解（Type Hints）
- 遵循PEP 8规范
- 使用中文注释关键业务逻辑

请逐个生成上述文件的完整内容，特别是 pyproject.toml、.env.example、Makefile 和 README.md 要详细完整，可直接使用。
```

---

## 提示词 1.2：核心配置模块开发

```
基于上一步创建的项目结构，现在请实现 app/core/ 下的所有核心模块。

【任务要求】

1. **app/core/config.py** - 配置管理
   - 使用 pydantic-settings 的 BaseSettings
   - 按业务分组（AppSettings、DatabaseSettings、RedisSettings、LarkSettings、LLMSettings、OpenClawSettings、SecuritySettings、LogSettings）
   - 主类 Settings 聚合所有子配置
   - 支持从 .env 文件加载
   - 支持嵌套环境变量（如 DATABASE__HOST）
   - 提供 @lru_cache 装饰的 get_settings() 函数
   - 包含数据库 URL 自动拼接的 computed_field
   - 区分开发/生产环境配置

2. **app/core/logger.py** - 日志配置
   - 使用 loguru 库
   - 支持文件轮转（按大小和时间）
   - 支持不同级别的输出（控制台彩色、文件JSON格式）
   - 集成 FastAPI 的请求日志
   - 支持 trace_id 上下文（用于链路追踪）
   - 提供 get_logger(name) 工厂函数

3. **app/core/exceptions.py** - 异常体系
   设计完整的异常层级：
   ```
   PMRobotException (基类)
   ├── BusinessException (业务异常)
   │   ├── ProjectNotFoundException
   │   ├── PermissionDeniedException
   │   ├── ProjectIsolationException (跨项目违规)
   │   └── DataValidationException
   ├── IntegrationException (集成异常)
   │   ├── LarkAPIException
   │   ├── OpenClawException
   │   ├── LLMException
   │   └── OASystemException
   ├── SkillException (Skill异常)
   │   ├── SkillNotFoundException
   │   ├── SkillNotActiveException
   │   ├── SkillExecutionException
   │   └── SkillPermissionException
   └── SystemException (系统异常)
       ├── DatabaseException
       └── CacheException
   ```
   每个异常包含：错误码、错误消息、详细信息、HTTP状态码
   提供全局异常处理器（FastAPI exception_handler）

4. **app/core/security.py** - 安全工具
   - 飞书签名验证（verify_lark_signature）
   - 飞书事件加密解密（AES-256-CBC）
   - HMAC签名生成与校验
   - JWT Token生成与校验（用于内部API）
   - 密码哈希（bcrypt）
   - 防重放攻击（基于时间戳和nonce）

5. **app/core/constants.py** - 常量定义
   定义所有业务常量：
   - 用户角色枚举（UserRole: PROJECT_MANAGER, PM, TECH_LEAD, MEMBER, VIEWER）
   - 权限操作枚举（Permission: READ, WRITE, SUBMIT, APPROVE, CONFIG）
   - 项目状态枚举（ProjectStatus: PLANNING, EXECUTING, CLOSING, CLOSED）
   - 任务状态枚举（TaskStatus）
   - 文档类型枚举（DocumentType）
   - Skill分类枚举（SkillCategory，对应PMBOK十大领域）
   - 数据来源枚举（DataSource: OA, LARK_CONVERSATION, BITABLE, FILE_IMPORT, SCHEDULED）
   - 缓存键前缀（CacheKeyPrefix）
   - 缓存过期时间（CacheTTL）
   - 错误码定义（ErrorCode）

【代码质量要求】
- 所有类和函数有完整的docstring
- 使用类型注解
- 关键代码有中文注释
- 遵循SOLID原则
- 异常体系要完整且易于扩展

请生成上述所有文件的完整代码，确保可直接运行。每个文件要可独立测试。
```

---

## 提示词 1.3：数据库模型与迁移

```
基于需求规格说明书的数据库设计章节，现在实现完整的SQLAlchemy 2.0数据库模型。

【任务要求】

1. **app/models/base.py** - 基础模型
   - 使用 SQLAlchemy 2.0 的 DeclarativeBase
   - 定义 Base 类，包含通用字段：
     * id (主键，根据需要使用整型或UUID)
     * created_at (创建时间，default=now())
     * updated_at (更新时间，onupdate=now())
   - 定义 SoftDeleteMixin（软删除支持，is_deleted字段）
   - 定义 TimestampMixin
   - 定义 AuditMixin（created_by, updated_by字段）

2. **app/models/** 下创建所有数据模型文件：

   **2.1 user.py** - 用户与权限相关
   - User（用户表）
   - UserProjectRole（用户-项目-角色关联表）
   
   **2.2 project.py** - 项目核心
   - Project（项目主表，包含基本信息、状态、时间、预算等）
   - Milestone（里程碑表）
   - ProjectMember（项目成员表）
   - ChatProjectBinding（飞书群-项目绑定表，关键！用于项目隔离）
   
   **2.3 task.py** - 任务与WBS
   - Task（任务表，支持WBS层级，parent_task_id自引用）
   - TaskHistory（任务变更历史）
   - TaskDependency（任务依赖关系）
   
   **2.4 cost.py** - 成本管理
   - ProjectCost（成本明细）
   - CostEstimate（成本估算）
   - EVMMetrics（EVM指标表，包含PV/EV/AC/CPI/SPI/CV/SV/EAC/ETC）
   
   **2.5 risk.py** - 风险管理
   - ProjectRisk（风险登记册）
   - RiskMitigation（风险应对记录）
   
   **2.6 timesheet.py** - 工时
   - TimesheetEntry（工时记录）
   
   **2.7 document.py** - 文档
   - ProjectDocument（项目文档表）
   - DocumentVersion（文档版本）
   
   **2.8 skill.py** - Skill管理
   - SkillConfiguration（Skill定义表）
   - ProjectSkillMapping（项目-Skill映射表）
   - SkillExecutionLog（Skill执行日志）
   
   **2.9 approval.py** - 审批
   - ApprovalWorkflow（审批流程）
   - ApprovalNode（审批节点）
   
   **2.10 audit.py** - 审计
   - DataMaintenanceAudit（数据维护审计）
   - PermissionAuditLog（权限审计日志）
   
   **2.11 integration.py** - 集成相关
   - ProjectBitableBinding（项目-飞书多维表格绑定）
   - DataSyncStatus（数据同步状态）
   
   **2.12 conversation.py** - 对话上下文
   - ConversationSession（对话会话）
   - ConversationMessage（对话消息历史）

3. **关系映射**：
   - 使用 SQLAlchemy 2.0 的 Mapped 和 mapped_column 语法
   - 正确定义外键关系（relationship）
   - 设置合适的级联策略（cascade）
   - 添加必要的索引和约束

4. **app/models/__init__.py**：
   - 导出所有模型，便于Alembic自动检测

5. **alembic配置**：
   - 初始化alembic（alembic init alembic）
   - 修改 alembic/env.py 支持异步SQLAlchemy
   - 配置自动从 app/models 检测模型变更
   - 创建第一个迁移：alembic revision --autogenerate -m "init schema"

6. **scripts/init_db.py** - 数据库初始化脚本
   - 创建数据库（如果不存在）
   - 运行所有迁移
   - 插入种子数据（seed data）：
     * 默认管理员用户
     * 预定义的Skill配置（40+ Skills元数据）
     * 示例项目数据（用于开发测试）

7. **scripts/seed_data.py** - 种子数据
   - 包含完整的Skill定义数据（按PMBOK十大领域分类）
   - 示例项目和成员
   - 示例任务和里程碑

【技术要点】
- 使用 SQLAlchemy 2.0 异步语法
- 正确使用 Index、UniqueConstraint、CheckConstraint
- 时间字段统一使用 TIMESTAMP WITH TIME ZONE
- 金额字段使用 Numeric(15, 2) 而非 Float
- JSONB字段用于存储灵活配置
- 添加表注释和字段注释（comment参数）
- 重要查询字段添加索引

【交付物】
请按上述要求生成所有模型文件的完整代码，每个文件独立完整，包含必要的导入语句、类型注解、字段注释。
最后给出执行迁移的完整命令序列。
```

---

## 提示词 1.4：数据库会话与Redis客户端

```
现在实现数据库连接、Redis缓存客户端和Repository基础类。

【任务要求】

1. **app/db/session.py** - SQLAlchemy异步Session管理
   实现以下内容：
   - 创建异步引擎（create_async_engine）
   - 配置连接池（pool_size, max_overflow, pool_pre_ping等）
   - 创建AsyncSessionLocal工厂
   - 提供 get_db() 异步依赖（用于FastAPI Depends）
   - 提供 get_db_context() 异步上下文管理器（用于非依赖场景）
   - 实现 init_db() 和 close_db() 生命周期函数
   - 添加SQL执行日志（debug模式）
   - 实现连接健康检查 check_db_health()

2. **app/db/redis_client.py** - Redis客户端封装
   - 基于 redis-py 的异步客户端
   - 实现 RedisClient 类，封装常用操作：
     * get/set/delete (基础)
     * get_json/set_json (自动JSON序列化)
     * incr/decr (计数)
     * hget/hset/hdel (Hash)
     * lpush/rpush/lpop/rpop (List)
     * sadd/smembers (Set)
     * setex (带过期时间)
     * delete_pattern (按模式批量删除)
     * lock/unlock (分布式锁)
     * pipeline (管道操作)
   - 实现连接池管理
   - 提供 get_redis() 依赖
   - 实现 init_redis() 和 close_redis() 
   - 实现健康检查 check_redis_health()
   - 实现缓存装饰器 @cache(key_pattern, ttl)

3. **app/repositories/base.py** - Repository基类
   实现泛型 BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]：
   - get_by_id(id) - 根据ID查询
   - get_by_ids(ids) - 批量查询
   - get_all(skip, limit, filters) - 分页查询
   - get_one_by(filters) - 单条件查询
   - get_many_by(filters) - 多条件查询
   - create(obj_in) - 创建
   - bulk_create(objs_in) - 批量创建
   - update(id, obj_in) - 更新
   - delete(id) - 删除（支持软删除）
   - count(filters) - 计数
   - exists(filters) - 是否存在
   - 支持 select_related/joined_load（预加载关联）

4. **app/repositories/project_repo.py** - 示例Repository实现
   继承BaseRepository，添加项目特定查询：
   - get_user_projects(user_id) - 获取用户参与的所有项目
   - get_by_chat_id(chat_id) - 根据飞书群ID获取项目
   - get_active_projects() - 获取进行中的项目
   - get_project_with_members(project_id) - 加载项目及成员

5. **app/main.py** - FastAPI应用主入口
   实现完整的应用初始化：
   - 创建FastAPI实例（包含title、description、version）
   - 配置CORS中间件
   - 配置GZip压缩中间件
   - 配置请求ID中间件（生成trace_id）
   - 配置请求日志中间件
   - 注册全局异常处理器
   - 配置 lifespan 事件（启动/关闭）：
     * 启动：init_db、init_redis、加载Skill注册表、启动后台任务
     * 关闭：close_db、close_redis、优雅停止
   - 注册API路由
   - 配置OpenAPI文档（swagger_ui_parameters）
   - 添加 /health 健康检查端点

6. **app/api/deps.py** - FastAPI依赖注入
   - get_current_user (从飞书user_id获取当前用户)
   - get_db (数据库session)
   - get_redis (Redis客户端)
   - require_role (角色权限检查装饰器)
   - get_settings (配置)

【技术要点】
- 全部使用async/await异步编程
- 正确处理资源释放（try/finally或async with）
- 异常要捕获并转换为业务异常
- 添加详细的日志
- 性能优化：连接池、批量操作、缓存

请生成所有上述文件的完整代码。
```

---

## 提示词 1.5：Docker环境与开发工具配置

```
完成项目脚手架的最后一步：配置Docker开发环境和必要的开发工具。

【任务要求】

1. **docker-compose.yml** - 开发环境编排
   包含以下服务：
   
   - **postgres**: PostgreSQL 15
     * 暴露5432端口
     * 数据持久化（volume）
     * 健康检查
     * 初始化脚本挂载
   
   - **redis**: Redis 7
     * 暴露6379端口
     * 数据持久化
     * 配置AOF
   
   - **kafka**: Kafka (使用 bitnami/kafka 镜像)
     * Zookeeper-less模式（KRaft）
     * 暴露9092端口
   
   - **minio**: MinIO（对象存储，用于文件）
     * 9000和9001端口
     * 默认bucket初始化
   
   - **app**: 主应用服务
     * 基于本地Dockerfile
     * 挂载代码目录（开发时热重载）
     * 依赖postgres、redis
     * 环境变量从.env加载
   
   - **worker**: Celery Worker
     * 处理异步任务
     * 依赖redis、kafka
   
   - **beat**: Celery Beat
     * 定时任务调度
   
   - **flower**: Celery监控
     * 5555端口
   
   配置统一网络（pm-robot-network）和命名volumes。

2. **docker/Dockerfile** - 主应用镜像
   多阶段构建：
   - **builder阶段**：安装依赖（使用pip或poetry）
   - **runtime阶段**：基于python:3.11-slim
     * 创建非root用户
     * 复制依赖和代码
     * 暴露8000端口
     * 健康检查
     * 启动命令：uvicorn

3. **docker/Dockerfile.worker** - Celery Worker镜像
   - 复用builder阶段
   - 启动命令改为celery worker

4. **docker/nginx.conf** - Nginx反向代理配置（生产用）
   - 上游负载均衡
   - SSL配置示例
   - 静态文件缓存
   - 限流配置

5. **scripts/dev_setup.sh** - 一键开发环境搭建脚本
   ```bash
   #!/bin/bash
   # 包含步骤：
   # 1. 检查依赖（docker、python、poetry）
   # 2. 复制 .env.example 到 .env
   # 3. 启动 docker-compose
   # 4. 等待数据库就绪
   # 5. 运行数据库迁移
   # 6. 初始化种子数据
   # 7. 显示成功信息
   ```

6. **scripts/health_check.sh** - 健康检查脚本
   - 检查所有服务状态
   - 测试API端点
   - 检查数据库连接
   - 检查Redis连接

7. **pytest.ini** - 测试配置
   - 异步测试支持
   - 覆盖率配置（最低80%）
   - 测试发现路径
   - 标记定义（unit、integration、e2e）

8. **tests/conftest.py** - pytest全局fixtures
   - test_db fixture（测试数据库）
   - test_redis fixture
   - test_client fixture（FastAPI TestClient）
   - mock_lark_client fixture
   - sample_project fixture
   - sample_user fixture

9. **.pre-commit-config.yaml** - 代码质量预提交检查
   - black（代码格式化）
   - isort（导入排序）
   - flake8（代码检查）
   - mypy（类型检查）
   - bandit（安全检查）

10. **Makefile** 完善（包含所有常用命令）：
    ```makefile
    .PHONY: help install dev test lint format migrate docker-up docker-down clean
    
    help:           # 显示帮助
    install:        # 安装依赖
    dev:            # 启动开发服务器
    test:           # 运行测试
    test-unit:      # 单元测试
    test-coverage:  # 测试覆盖率
    lint:           # 代码检查
    format:         # 代码格式化
    migrate:        # 创建迁移
    upgrade:        # 应用迁移
    downgrade:      # 回滚迁移
    seed:           # 填充种子数据
    docker-up:      # 启动Docker环境
    docker-down:    # 停止Docker环境
    docker-logs:    # 查看日志
    docker-rebuild: # 重新构建
    clean:          # 清理临时文件
    ```

11. **docs/architecture/README.md** - 架构文档
    - 系统架构图（用ASCII或mermaid语法）
    - 技术选型说明
    - 模块职责
    - 部署拓扑

【验收标准】
执行 `make dev_setup.sh` 后能够：
1. 一键启动所有依赖服务
2. 数据库自动初始化
3. 应用成功启动
4. 访问 http://localhost:8000/docs 看到Swagger文档
5. 访问 http://localhost:8000/health 返回健康状态
6. 所有服务健康检查通过

请生成所有上述文件的完整代码和配置，包括详细的注释。最后输出完整的执行步骤说明。
```

---

##  Part 1 完成检查清单

完成 Part 1 后，请验证以下项目：

- [ ] 项目目录结构完整，所有 `__init__.py` 已创建
- [ ] `pyproject.toml` 依赖完整，可用 `poetry install` 或 `pip install -e .` 安装
- [ ] `.env.example` 涵盖所有配置项
- [ ] `app/core/config.py` 可正确加载 .env
- [ ] `app/core/logger.py` 可输出彩色日志和文件日志
- [ ] `app/core/exceptions.py` 异常体系完整
- [ ] 所有数据库模型文件已创建，无导入错误
- [ ] Alembic迁移可成功生成和执行
- [ ] `docker-compose up -d` 可启动所有服务
- [ ] `make dev` 可启动 FastAPI 应用
- [ ] 访问 `/docs` 可看到 Swagger UI
- [ ] `/health` 接口返回所有依赖服务的健康状态

---

##  接下来的开发计划

完成 **Part 1** 后，我们将进入：

- **Part 2**：飞书集成与权限隔离核心（飞书Bot SDK封装、消息处理、群-项目绑定、RBAC权限管理）
- **Part 3**：OpenClaw编排引擎与Skill框架（智能体编排、意图识别、Skill动态加载与执行）
- **Part 4**：业务Skills批量开发（按PMBOK十大领域开发40+具体Skills）
- **Part 5**：数据维护通道与测试部署（OA对接、Bitable双向同步、监控告警、CI/CD）

---

**请告诉我，是否要继续输出 Part 2 的内容？或者您希望对 Part 1 的某些提示词进行调整？**


#  Part 2：飞书集成与权限隔离核心

> **目标**：实现飞书Bot完整集成、消息事件处理、严格的多项目权限隔离机制
>
> **预计耗时**：3-4天
>
> **前置条件**：Part 1 已完成；已申请飞书开发者账号、创建企业自建应用、获取 App ID 和 App Secret

---

## 提示词 2.1：飞书Open API SDK封装

```
你是一位专精于飞书生态集成的资深工程师。请基于飞书最新的 Open API v2 和 lark-oapi Python SDK，封装一个企业级的飞书客户端。

【背景】
我们的PM机器人需要与飞书深度集成，包括：消息收发、卡片交互、文件操作、群组管理、用户信息、多维表格、审批流、云文档等。

【任务要求】

1. **app/integrations/lark/__init__.py** - 模块导出

2. **app/integrations/lark/client.py** - 飞书客户端基类
   实现 LarkClient 类：
   - 基于 lark.Client 进行二次封装
   - 自动管理 tenant_access_token（带缓存和自动刷新）
   - 自动管理 app_access_token
   - 统一的请求重试机制（基于tenacity）
   - 统一的异常处理（转换为 LarkAPIException）
   - 请求日志记录（含 trace_id）
   - 限流处理（飞书API有调用频率限制）
   
   核心方法：
   - get_tenant_access_token() - 获取租户token
   - refresh_token_if_expired() - 刷新token
   - _request(method, path, **kwargs) - 底层请求
   - get(path, params) / post(path, data) / put / delete

3. **app/integrations/lark/message.py** - 消息服务
   实现 LarkMessageService 类：
   
   **发送消息：**
   - send_text(receive_id, text, receive_id_type='chat_id') - 发送文本
   - send_post(receive_id, post_content) - 发送富文本
   - send_card(receive_id, card) - 发送交互卡片
   - send_image(receive_id, image_key) - 发送图片
   - send_file(receive_id, file_key) - 发送文件
   - send_share_chat(receive_id, share_chat_id) - 分享群名片
   - reply_message(message_id, content, msg_type) - 回复消息
   - update_message(message_id, content) - 更新消息（用于卡片）
   - recall_message(message_id) - 撤回消息
   
   **批量发送：**
   - batch_send_text(receive_ids, text)
   - batch_send_card(receive_ids, card)
   
   **消息查询：**
   - get_message(message_id) - 查询消息内容
   - list_messages(chat_id, start_time, end_time) - 查询历史消息
   
   **@提及支持：**
   - mention_user(user_id) - 生成@用户的标签
   - mention_all() - @所有人

4. **app/integrations/lark/card.py** - 卡片构建器
   实现 CardBuilder 类（流式API设计）：
   
   ```python
   card = (
       CardBuilder()
       .header("项目总览", template="blue")
       .div_module(" 整体进度: 82%")
       .hr()
       .markdown_module("**风险预警**\n-  高风险")
       .table_module(headers=[...], rows=[...])
       .action_module([
           Button("查看详情", action_type="link", url="..."),
           Button("更新数据", action_type="callback", value={...})
       ])
       .build()
   )
   ```
   
   支持组件：
   - header（标题区，支持模板色 blue/green/red/orange/grey）
   - div_module（普通文本）
   - markdown_module（Markdown文本）
   - hr（分割线）
   - img_module（图片）
   - note_module（备注）
   - action_module（按钮组）
   - column_set_module（多列布局）
   - select_module（下拉选择）
   - date_picker_module（日期选择）
   - input_module（输入框）
   - table_module（自定义表格，通过markdown实现）
   
   提供常用预置模板：
   - build_project_overview_card(project_data) - 项目总览卡片
   - build_progress_card(progress_data) - 进度卡片
   - build_risk_alert_card(risks) - 风险预警卡片
   - build_confirmation_card(action_desc, callback_value) - 确认卡片
   - build_form_card(fields) - 表单卡片
   - build_error_card(error_msg) - 错误提示卡片
   - build_help_card() - 帮助卡片

5. **app/integrations/lark/chat.py** - 群组服务
   实现 LarkChatService 类：
   - get_chat_info(chat_id) - 获取群信息
   - get_chat_members(chat_id) - 获取群成员列表
   - is_user_in_chat(chat_id, user_id) - 检查用户是否在群
   - add_chat_members(chat_id, user_ids) - 添加成员
   - remove_chat_members(chat_id, user_ids) - 移除成员
   - update_chat_info(chat_id, name, description) - 更新群信息
   - on_bot_added_to_chat(chat_id) - Bot被加入群的回调处理
   - on_bot_removed_from_chat(chat_id) - Bot被移除的回调处理

6. **app/integrations/lark/user.py** - 用户服务
   实现 LarkUserService 类：
   - get_user_info(user_id, user_id_type='open_id') - 获取用户信息
   - get_user_by_email(email) - 邮箱查用户
   - get_user_by_mobile(mobile) - 手机号查用户
   - batch_get_users(user_ids) - 批量获取
   - get_user_department(user_id) - 获取用户部门
   - search_users(query) - 搜索用户
   
   缓存策略：用户信息缓存30分钟

7. **app/integrations/lark/file.py** - 文件服务
   实现 LarkFileService 类：
   - upload_file(file_bytes, filename, parent_node='root') - 上传文件到云空间
   - upload_image(image_bytes, filename) - 上传图片
   - upload_to_chat(chat_id, file_bytes, filename) - 上传到聊天
   - download_file(file_key) - 下载文件
   - get_file_metadata(file_token) - 获取文件元信息
   - create_folder(name, parent_node) - 创建文件夹
   - move_file(file_token, target_folder) - 移动文件

8. **app/integrations/lark/bitable.py** - 多维表格服务（**重要**）
   实现 LarkBitableService 类：
   - create_app(name, folder_token) - 创建多维表格应用
   - create_table(app_token, table_name, fields) - 创建数据表
   - list_tables(app_token) - 列出所有表
   - add_records(app_token, table_id, records) - 批量添加记录
   - update_records(app_token, table_id, records) - 批量更新
   - delete_records(app_token, table_id, record_ids) - 批量删除
   - search_records(app_token, table_id, filter, sort) - 搜索记录
   - get_record(app_token, table_id, record_id) - 获取单条记录
   - subscribe_table_events(app_token, table_id) - 订阅表格变更事件
   
   提供高级方法：
   - create_project_workspace(project_id, project_name) - 为项目创建完整工作区（包含任务表、风险表、工时表等）
   - sync_project_data_to_bitable(project_id) - 同步数据到表格
   - sync_bitable_to_project_data(app_token, table_id) - 反向同步

9. **app/integrations/lark/approval.py** - 审批服务
   实现 LarkApprovalService 类：
   - create_approval_instance(approval_code, user_id, form_data) - 创建审批
   - get_approval_instance(instance_code) - 查询审批
   - approve(instance_code, user_id, comment) - 通过审批
   - reject(instance_code, user_id, comment) - 拒绝审批
   - cancel_approval(instance_code, user_id) - 撤销审批
   - subscribe_approval_events() - 订阅审批事件

10. **app/integrations/lark/event_handler.py** - 事件处理器
    实现 LarkEventHandler 类：
    - 统一的事件分发器
    - 支持事件类型：
      * im.message.receive_v1 (接收消息)
      * im.chat.member.bot.added_v1 (Bot加入群)
      * im.chat.member.bot.deleted_v1 (Bot被移除)
      * im.chat.member.user.added_v1 (用户加入群)
      * card.action.trigger (卡片按钮点击)
      * drive.file.bitable_record_changed_v1 (多维表格变更)
      * approval.instance (审批实例事件)
    - 注册事件回调装饰器 @on_event("event_type")
    - 异步处理事件，立即返回ack
    - 事件去重（基于event_id，避免重复处理）
    - 错误隔离（单个事件失败不影响其他）

【技术要点】
- 全部异步实现（async/await）
- 完善的错误处理和重试机制
- 详细的日志记录（带trace_id）
- 支持本地开发模式（mock飞书API）
- 单元测试覆盖核心方法

【交付物】
请生成上述所有文件的完整代码，特别关注：
1. CardBuilder 的流式API设计要优雅
2. BitableService 要支持完整的双向同步
3. EventHandler 要保证事件处理的可靠性
4. 所有方法都要有清晰的docstring和类型注解
```

---

## 提示词 2.2：飞书Webhook入口与消息处理

```
基于飞书SDK封装，现在实现完整的Webhook接收和消息处理流程。

【任务要求】

1. **app/api/v1/lark_webhook.py** - 飞书Webhook统一入口
   
   实现以下端点：
   
   **POST /api/v1/lark/event** - 事件回调统一入口
   ```python
   @router.post("/event")
   async def handle_lark_event(
       request: Request,
       db: AsyncSession = Depends(get_db),
       redis: RedisClient = Depends(get_redis)
   ):
       """飞书事件统一回调入口"""
       # 1. 读取请求体
       body = await request.body()
       
       # 2. 验证签名（防止伪造请求）
       headers = request.headers
       if not verify_lark_signature(headers, body):
           raise HTTPException(401, "签名验证失败")
       
       # 3. 解密（如果启用了加密）
       payload = await parse_lark_payload(body)
       
       # 4. 处理URL验证挑战
       if payload.get("type") == "url_verification":
           return {"challenge": payload.get("challenge")}
       
       # 5. 事件去重（基于event_id）
       event_id = payload["header"]["event_id"]
       if await is_event_processed(redis, event_id):
           return {"code": 0, "msg": "duplicated"}
       await mark_event_processed(redis, event_id)
       
       # 6. 异步处理事件，立即返回
       asyncio.create_task(
           dispatch_event(payload, db, redis)
       )
       
       return {"code": 0, "msg": "success"}
   ```
   
   **POST /api/v1/lark/card/action** - 卡片交互回调
   - 处理卡片按钮点击
   - 处理表单提交
   - 必须在3秒内返回响应（飞书要求）

2. **app/services/event_dispatcher.py** - 事件分发服务
   
   实现 EventDispatcher 类：
   ```python
   class EventDispatcher:
       """飞书事件分发器"""
       
       def __init__(self):
           self.handlers = {}  # 事件类型 -> 处理函数
       
       def register(self, event_type: str):
           """装饰器，注册事件处理函数"""
           def decorator(func):
               self.handlers[event_type] = func
               return func
           return decorator
       
       async def dispatch(self, payload: Dict, db, redis):
           """分发事件"""
           event_type = payload["header"]["event_type"]
           handler = self.handlers.get(event_type)
           
           if not handler:
               logger.warning(f"未注册的事件类型: {event_type}")
               return
           
           try:
               await handler(payload, db, redis)
           except Exception as e:
               logger.error(f"事件处理失败: {event_type}", exc_info=True)
               # 不抛出异常，避免飞书重试
   ```

3. **app/services/handlers/message_handler.py** - 消息事件处理
   
   ```python
   @event_dispatcher.register("im.message.receive_v1")
   async def handle_message_receive(payload, db, redis):
       """处理用户发送的消息"""
       event = payload["event"]
       
       # 1. 提取消息信息
       message = event["message"]
       sender = event["sender"]
       
       message_id = message["message_id"]
       chat_id = message["chat_id"]
       chat_type = message["chat_type"]  # group/p2p
       msg_type = message["message_type"]  # text/post/image/file
       content = message["content"]
       sender_id = sender["sender_id"]["open_id"]
       
       # 2. 过滤Bot自己发的消息（防止死循环）
       if sender.get("sender_type") == "app":
           return
       
       # 3. 解析消息内容
       text = parse_message_content(msg_type, content)
       if not text:
           return
       
       # 4. 群聊场景：检查是否@了机器人
       if chat_type == "group":
           if not is_mentioned_bot(message):
               return  # 群里没@机器人，忽略
           text = remove_bot_mention(text)
       
       # 5. 构建用户上下文
       context = await build_user_context(
           user_id=sender_id,
           chat_id=chat_id,
           db=db,
           redis=redis
       )
       
       # 6. 群-项目绑定校验
       if chat_type == "group" and not context.project_id:
           await reply_no_project_binding(chat_id, message_id)
           return
       
       # 7. 调用编排引擎处理
       from app.orchestrator import orchestrator
       result = await orchestrator.orchestrate(
           user_input=text,
           context=context,
           user_id=sender_id,
           project_id=context.project_id,
           message_id=message_id  # 用于回复
       )
       
       # 8. 发送响应
       await send_orchestrate_response(chat_id, message_id, result)
   ```

4. **app/services/handlers/chat_handler.py** - 群组事件处理
   
   ```python
   @event_dispatcher.register("im.chat.member.bot.added_v1")
   async def handle_bot_added(payload, db, redis):
       """Bot被加入群组时处理"""
       event = payload["event"]
       chat_id = event["chat_id"]
       operator_id = event["operator_id"]["open_id"]
       
       # 1. 获取群信息
       chat_info = await lark_chat_service.get_chat_info(chat_id)
       
       # 2. 引导用户绑定项目
       welcome_card = build_chat_binding_guidance_card(chat_id, operator_id)
       await lark_message_service.send_card(chat_id, welcome_card)
       
       # 3. 记录Bot加入事件
       logger.info(f"Bot加入群组: {chat_id}, 操作人: {operator_id}")
   
   @event_dispatcher.register("im.chat.member.bot.deleted_v1")
   async def handle_bot_removed(payload, db, redis):
       """Bot被移除群组时清理"""
       event = payload["event"]
       chat_id = event["chat_id"]
       
       # 解除群-项目绑定
       await unbind_chat_from_project(chat_id, db)
       
       # 清理缓存
       await redis.delete(f"chat:project_binding:{chat_id}")
       
       logger.info(f"Bot离开群组: {chat_id}, 已清理绑定")
   ```

5. **app/services/handlers/card_action_handler.py** - 卡片交互处理
   
   ```python
   @event_dispatcher.register("card.action.trigger")
   async def handle_card_action(payload, db, redis):
       """处理卡片按钮点击和表单提交"""
       event = payload["event"]
       
       action = event["action"]
       action_value = action.get("value", {})  # 按钮上设置的value
       action_type = action_value.get("action_type")
       
       # 根据action_type分发处理
       handlers = {
           "bind_project": handle_bind_project_action,
           "confirm_update": handle_confirm_update_action,
           "cancel_update": handle_cancel_update_action,
           "generate_report": handle_generate_report_action,
           "view_details": handle_view_details_action,
           # ... 其他action
       }
       
       handler = handlers.get(action_type)
       if handler:
           await handler(event, db, redis)
   ```

6. **app/services/conversation_context.py** - 用户上下文管理
   
   ```python
   class UserContextManager:
       """用户对话上下文管理"""
       
       async def build_context(
           self, user_id: str, chat_id: str,
           db: AsyncSession, redis: RedisClient
       ) -> UserContext:
           """构建用户上下文"""
           
           # 1. 优先从缓存获取
           cache_key = f"context:{user_id}:{chat_id}"
           cached = await redis.get_json(cache_key)
           if cached:
               return UserContext(**cached)
           
           # 2. 获取群-项目绑定
           binding = await chat_project_repo.get_by_chat_id(chat_id, db)
           project_id = binding.project_id if binding else None
           
           # 3. 获取用户信息
           user_info = await lark_user_service.get_user_info(user_id)
           
           # 4. 获取用户在该项目的角色
           user_role = None
           if project_id:
               role_record = await user_project_role_repo.get_role(
                   user_id, project_id, db
               )
               user_role = role_record.role if role_record else None
           
           # 5. 获取用户可访问的所有项目
           accessible_projects = await project_repo.get_user_projects(user_id, db)
           
           # 6. 构建对话历史（最近10轮）
           conversation_history = await self.get_recent_conversation(
               user_id, chat_id, redis, limit=10
           )
           
           context = UserContext(
               user_id=user_id,
               user_name=user_info.get("name"),
               chat_id=chat_id,
               project_id=project_id,
               project_name=binding.project_name if binding else None,
               user_role=user_role,
               accessible_project_ids=[p.id for p in accessible_projects],
               conversation_history=conversation_history,
               timestamp=datetime.now()
           )
           
           # 7. 缓存上下文（8小时）
           await redis.set_json(cache_key, context.dict(), ttl=28800)
           
           return context
       
       async def update_conversation(
           self, user_id, chat_id, role, content, redis
       ):
           """追加对话记录"""
           key = f"conversation:{user_id}:{chat_id}"
           message = {
               "role": role,  # user/assistant
               "content": content,
               "timestamp": datetime.now().isoformat()
           }
           await redis.lpush(key, json.dumps(message))
           await redis.ltrim(key, 0, 19)  # 保留最近20条
           await redis.expire(key, 28800)  # 8小时
   ```

7. **app/schemas/lark.py** - 飞书相关Schema
   定义所有飞书事件的Pydantic模型：
   - LarkEventHeader
   - LarkMessageEvent
   - LarkChatEvent
   - LarkCardActionEvent
   - LarkSender
   - LarkMessage
   - UserContext

8. **app/utils/lark_message_parser.py** - 消息解析工具
   - parse_text_message(content) - 解析文本消息
   - parse_post_message(content) - 解析富文本
   - is_mentioned_bot(message) - 检查是否@了Bot
   - remove_bot_mention(text) - 移除@标签
   - extract_mentions(message) - 提取所有@的人

【关键设计原则】
1. **可靠性**：webhook响应必须快速（<3秒），重活异步做
2. **幂等性**：相同event_id只处理一次
3. **可观测性**：每个事件都有完整的日志链路（trace_id贯穿）
4. **安全性**：严格的签名验证、防重放
5. **优雅降级**：单个事件失败不影响整体

【交付物】
生成上述所有文件的完整代码，重点保证消息处理流程的健壮性。
最后提供一个 `tests/integration/test_lark_webhook.py` 集成测试示例。
```

---

## 提示词 2.3：项目隔离与权限管理（核心安全模块）

```
你正在实现PM机器人最关键的安全模块——项目隔离与权限管理。这是确保"用户绝不能跨项目访问数据"的核心保障。

【任务要求】

1. **app/services/permission_service.py** - 权限服务
   
   实现完整的多层权限校验体系：
   
   ```python
   class PermissionService:
       """权限管理服务"""
       
       # 角色权限矩阵（基于RBAC）
       PERMISSION_MATRIX = {
           UserRole.PROJECT_MANAGER: [
               Permission.READ, Permission.WRITE, Permission.SUBMIT,
               Permission.APPROVE, Permission.CONFIG, Permission.DELETE
           ],
           UserRole.PM: [
               Permission.READ, Permission.WRITE, Permission.SUBMIT,
               Permission.CONFIG
           ],
           UserRole.TECH_LEAD: [
               Permission.READ, Permission.WRITE, Permission.UPDATE
           ],
           UserRole.MEMBER: [
               Permission.READ, Permission.SUBMIT
           ],
           UserRole.VIEWER: [
               Permission.READ
           ]
       }
       
       async def check_project_access(
           self, user_id: str, project_id: str,
           db: AsyncSession, redis: RedisClient
       ) -> bool:
           """检查用户是否有权访问该项目（基础检查）"""
           # 优先从缓存
           cache_key = f"perm:project_access:{user_id}:{project_id}"
           cached = await redis.get(cache_key)
           if cached is not None:
               return cached == "1"
           
           # 数据库查询
           role_record = await self.user_project_role_repo.get_role(
               user_id, project_id, db
           )
           has_access = role_record is not None
           
           # 缓存结果（1小时）
           await redis.setex(cache_key, 3600, "1" if has_access else "0")
           
           return has_access
       
       async def check_operation_permission(
           self, user_id: str, project_id: str,
           operation: Permission, db: AsyncSession, redis: RedisClient
       ) -> bool:
           """检查用户是否有权执行特定操作"""
           # 1. 先检查项目访问权限
           if not await self.check_project_access(user_id, project_id, db, redis):
               return False
           
           # 2. 获取用户角色
           role_record = await self.user_project_role_repo.get_role(
               user_id, project_id, db
           )
           if not role_record:
               return False
           
           # 3. 检查操作权限
           allowed_permissions = self.PERMISSION_MATRIX.get(
               role_record.role, []
           )
           return operation in allowed_permissions
       
       async def check_skill_permission(
           self, user_id: str, project_id: str, skill_name: str,
           db: AsyncSession, redis: RedisClient
       ) -> bool:
           """检查用户是否有权使用特定Skill"""
           # 1. Skill是否对该项目启用
           skill_active = await self.skill_service.is_skill_active_for_project(
               skill_name, project_id, db, redis
           )
           if not skill_active:
               return False
           
           # 2. 用户是否有项目访问权限
           if not await self.check_project_access(user_id, project_id, db, redis):
               return False
           
           # 3. 用户角色是否符合Skill要求
           skill_def = await self.skill_service.get_skill_definition(skill_name, db)
           role_record = await self.user_project_role_repo.get_role(
               user_id, project_id, db
           )
           
           required_roles = skill_def.permission_requirements
           return required_roles.get(role_record.role, False)
       
       async def get_user_accessible_projects(
           self, user_id: str, db: AsyncSession
       ) -> List[Project]:
           """获取用户可访问的所有项目"""
           return await self.project_repo.get_user_projects(user_id, db)
       
       async def get_user_role_in_project(
           self, user_id: str, project_id: str, db: AsyncSession
       ) -> Optional[UserRole]:
           """获取用户在项目中的角色"""
           role_record = await self.user_project_role_repo.get_role(
               user_id, project_id, db
           )
           return role_record.role if role_record else None
       
       async def revoke_user_access(
           self, user_id: str, project_id: str, db, redis
       ):
           """撤销用户的项目访问权限"""
           await self.user_project_role_repo.delete_role(user_id, project_id, db)
           # 清除所有相关缓存
           await self.invalidate_user_permissions(user_id, project_id, redis)
       
       async def invalidate_user_permissions(
           self, user_id: str, project_id: str, redis
       ):
           """清除用户权限缓存"""
           patterns = [
               f"perm:project_access:{user_id}:{project_id}",
               f"perm:operation:{user_id}:{project_id}:*",
               f"perm:skill:{user_id}:{project_id}:*",
               f"context:{user_id}:*"
           ]
           for pattern in patterns:
               await redis.delete_pattern(pattern)
   ```

2. **app/services/project_isolation_service.py** - 项目隔离服务（**核心安全**）
   
   ```python
   class ProjectIsolationService:
       """
       项目隔离服务 - 确保用户绝对不能跨项目访问数据
       
       这是PM机器人的最核心安全模块，所有数据访问都必须经过此服务校验。
       """
       
       async def enforce_chat_project_binding(
           self, chat_id: str, claimed_project_id: str,
           db: AsyncSession, redis: RedisClient
       ) -> bool:
           """
           强制群-项目绑定校验
           确保群聊中操作的项目就是绑定的项目，防止伪造project_id
           """
           binding = await self.get_chat_project_binding(chat_id, db, redis)
           
           if not binding:
               raise ProjectIsolationException(
                   f"群聊 {chat_id} 未绑定任何项目，请先绑定项目"
               )
           
           if binding.project_id != claimed_project_id:
               raise ProjectIsolationException(
                   f"群聊绑定的项目是 {binding.project_id}，"
                   f"但请求操作 {claimed_project_id}，已阻止"
               )
           
           return True
       
       async def enforce_user_in_project(
           self, user_id: str, project_id: str,
           db: AsyncSession, redis: RedisClient
       ) -> bool:
           """
           强制用户在项目中校验
           即使群聊绑定了项目，用户也必须是该项目成员才能操作
           """
           role_record = await self.user_project_role_repo.get_role(
               user_id, project_id, db
           )
           
           if not role_record:
               raise ProjectIsolationException(
                   f"用户 {user_id} 不是项目 {project_id} 的成员，禁止访问"
               )
           
           return True
       
       async def filter_query_by_user_projects(
           self, user_id: str, query, project_id_field
       ):
           """
           查询过滤器 - 自动给所有查询添加用户可访问项目的过滤条件
           这是防止跨项目数据泄露的最后一道防线
           """
           accessible_project_ids = await self.get_user_accessible_project_ids(
               user_id
           )
           return query.filter(project_id_field.in_(accessible_project_ids))
       
       async def get_chat_project_binding(
           self, chat_id: str, db, redis
       ) -> Optional[ChatProjectBinding]:
           """获取群-项目绑定（带缓存）"""
           cache_key = f"chat:project_binding:{chat_id}"
           cached = await redis.get_json(cache_key)
           if cached:
               return ChatProjectBinding(**cached)
           
           binding = await self.chat_project_binding_repo.get_by_chat_id(
               chat_id, db
           )
           if binding:
               await redis.set_json(
                   cache_key, binding.to_dict(), ttl=86400 * 7  # 7天
               )
           return binding
       
       async def bind_chat_to_project(
           self, chat_id: str, project_id: str,
           bound_by: str, db, redis
       ):
           """绑定群聊到项目"""
           # 校验项目存在
           project = await self.project_repo.get_by_id(project_id, db)
           if not project:
               raise ProjectNotFoundException(f"项目 {project_id} 不存在")
           
           # 校验操作人有权限
           if not await self.permission_service.check_operation_permission(
               bound_by, project_id, Permission.CONFIG, db, redis
           ):
               raise PermissionDeniedException(
                   f"用户 {bound_by} 无权绑定项目 {project_id}"
               )
           
           # 检查是否已绑定其他项目
           existing = await self.chat_project_binding_repo.get_by_chat_id(
               chat_id, db
           )
           if existing:
               raise BusinessException(
                   f"群聊已绑定项目 {existing.project_id}，请先解绑"
               )
           
           # 创建绑定
           binding = await self.chat_project_binding_repo.create({
               "chat_id": chat_id,
               "project_id": project_id,
               "bound_by": bound_by,
               "bound_at": datetime.now()
           }, db)
           
           # 清除缓存
           await redis.delete(f"chat:project_binding:{chat_id}")
           
           # 审计日志
           await self.audit_service.log_action(
               user_id=bound_by,
               action="bind_chat_to_project",
               object_type="chat_project_binding",
               object_id=str(binding.id),
               details={"chat_id": chat_id, "project_id": project_id}
           )
           
           return binding
       
       async def unbind_chat(self, chat_id: str, operator_id: str, db, redis):
           """解绑群聊"""
           binding = await self.chat_project_binding_repo.get_by_chat_id(
               chat_id, db
           )
           if not binding:
               return
           
           # 校验权限
           if not await self.permission_service.check_operation_permission(
               operator_id, binding.project_id, Permission.CONFIG, db, redis
           ):
               raise PermissionDeniedException("无权解绑")
           
           await self.chat_project_binding_repo.delete(binding.id, db)
           await redis.delete(f"chat:project_binding:{chat_id}")
   ```

3. **app/services/audit_service.py** - 审计服务
   
   ```python
   class AuditService:
       """审计日志服务 - 记录所有关键操作"""
       
       async def log_action(
           self, user_id: str, action: str,
           object_type: str = None, object_id: str = None,
           details: Dict = None, db = None
       ):
           """记录操作日志"""
           audit_log = AuditLog(
               user_id=user_id,
               action=action,
               object_type=object_type,
               object_id=object_id,
               details=details or {},
               ip_address=get_request_ip(),  # 从上下文获取
               user_agent=get_user_agent(),
               trace_id=get_trace_id(),
               created_at=datetime.now()
           )
           db.add(audit_log)
           await db.commit()
       
       async def log_permission_check(
           self, user_id: str, project_id: str,
           operation: str, allowed: bool, db
       ):
           """记录权限检查日志"""
           # 记录到独立的权限审计表
           pass
       
       async def log_data_access(
           self, user_id: str, data_type: str,
           data_ids: List[str], db
       ):
           """记录数据访问日志"""
           pass
       
       async def query_audit_logs(
           self, user_id: str = None, action: str = None,
           start_time: datetime = None, end_time: datetime = None,
           db = None
       ) -> List[AuditLog]:
           """查询审计日志"""
           pass
   ```

4. **app/api/deps.py** - 完善依赖注入
   
   增加权限检查依赖：
   ```python
   async def get_current_lark_user(
       request: Request,
       db: AsyncSession = Depends(get_db),
       redis: RedisClient = Depends(get_redis)
   ) -> User:
       """从飞书user_id获取当前用户"""
       lark_user_id = request.headers.get("X-Lark-User-Id")
       if not lark_user_id:
           raise HTTPException(401, "缺少用户标识")
       
       user = await user_repo.get_by_lark_id(lark_user_id, db)
       if not user:
           raise HTTPException(401, "用户不存在")
       return user
   
   def require_project_permission(operation: Permission):
       """要求项目操作权限的依赖装饰器"""
       async def dependency(
           project_id: str,
           current_user: User = Depends(get_current_lark_user),
           db: AsyncSession = Depends(get_db),
           redis: RedisClient = Depends(get_redis)
       ):
           has_permission = await permission_service.check_operation_permission(
               current_user.id, project_id, operation, db, redis
           )
           if not has_permission:
               raise PermissionDeniedException(
                   f"用户无权执行 {operation} 操作"
               )
           return current_user
       return dependency
   ```

5. **app/api/v1/admin.py** - 管理API（项目绑定管理）
   
   实现以下端点（需要管理员权限）：
   - POST /api/v1/admin/projects/{project_id}/bind-chat - 绑定群聊
   - DELETE /api/v1/admin/projects/{project_id}/unbind-chat - 解绑群聊
   - GET /api/v1/admin/chat-bindings - 查看所有绑定
   - POST /api/v1/admin/users/{user_id}/projects/{project_id}/role - 分配角色
   - DELETE /api/v1/admin/users/{user_id}/projects/{project_id}/role - 撤销角色

6. **app/services/handlers/binding_handler.py** - 绑定卡片交互处理
   
   处理群聊中通过卡片完成项目绑定的流程：
   ```
   用户点击"绑定项目"按钮
   → 弹出项目选择卡片（仅显示用户有权限的项目）
   → 用户选择项目
   → 弹出确认卡片
   → 用户确认
   → 完成绑定，发送成功消息
   ```

7. **tests/unit/test_permission_service.py** - 权限服务测试
   完整的单元测试，覆盖：
   - 不同角色的权限矩阵
   - 缓存命中/未命中场景
   - 边界条件（用户不存在、项目不存在）
   - 跨项目访问拒绝

8. **tests/integration/test_project_isolation.py** - 项目隔离集成测试
   关键测试用例：
   - **test_user_cannot_access_other_project_data** - 用户不能访问其他项目数据
   - **test_chat_project_binding_enforced** - 群-项目绑定强制校验
   - **test_user_must_be_project_member** - 用户必须是项目成员
   - **test_query_filter_prevents_data_leak** - 查询过滤器防止数据泄露

【安全设计原则】
1. **默认拒绝**：所有访问默认拒绝，必须显式授权
2. **最小权限**：用户仅获得完成工作所需的最小权限
3. **多层防御**：权限校验在多个层次进行（API层、服务层、数据层）
4. **审计完备**：所有权限相关操作必须记录审计日志
5. **缓存安全**：权限变更必须立即清除相关缓存

【交付物】
生成上述所有文件的完整代码，特别强调安全性和测试覆盖。
项目隔离是PM机器人成败的关键，代码质量必须达到生产级。
```

---

##  Part 2 完成检查清单

- [ ] 飞书SDK封装完整，覆盖消息、卡片、群组、用户、文件、多维表格、审批
- [ ] CardBuilder可流式构建复杂卡片
- [ ] Webhook入口可正确接收并验签
- [ ] 事件分发器可正确路由不同类型事件
- [ ] 用户上下文构建机制完整
- [ ] 权限矩阵实现正确（5种角色、6种权限）
- [ ] 项目隔离服务通过所有安全测试
- [ ] 群-项目绑定流程可通过卡片完成
- [ ] 所有关键操作有审计日志
- [ ] 测试覆盖率达到80%+

---

#  Part 3：OpenClaw编排引擎与Skill框架

> **目标**：构建可扩展的智能体编排引擎和Skill动态加载框架
>
> **预计耗时**：4-5天

---

## 提示词 3.1：LLM集成与意图识别

```
你是一位精通大模型应用开发的资深工程师。请构建PM机器人的LLM集成层和意图识别引擎。

【任务要求】

1. **app/integrations/llm/__init__.py** - 模块导出

2. **app/integrations/llm/base.py** - LLM基类
   
   ```python
   class BaseLLMClient(ABC):
       """LLM客户端抽象基类"""
       
       @abstractmethod
       async def chat_completion(
           self, messages: List[Dict],
           model: str = None,
           temperature: float = 0.7,
           max_tokens: int = 2000,
           response_format: str = None,  # text/json
           tools: List[Dict] = None,  # function calling
           **kwargs
       ) -> LLMResponse:
           """对话补全"""
           pass
       
       @abstractmethod
       async def stream_completion(
           self, messages: List[Dict], **kwargs
       ) -> AsyncIterator[str]:
           """流式输出"""
           pass
       
       @abstractmethod
       async def embedding(
           self, texts: List[str], model: str = None
       ) -> List[List[float]]:
           """向量化"""
           pass
   ```

3. **app/integrations/llm/openai_client.py** - OpenAI/兼容客户端
   - 支持原生OpenAI API
   - 支持兼容OpenAI接口的国产模型（DeepSeek、通义千问、智谱GLM等）
   - 实现重试、限流、错误处理
   - Token用量统计

4. **app/integrations/llm/qianwen_client.py** - 通义千问客户端
   - 调用阿里云DashScope API
   - 支持流式输出

5. **app/integrations/llm/factory.py** - LLM工厂
   ```python
   class LLMFactory:
       """LLM工厂，根据配置动态选择LLM"""
       
       _instances = {}
       
       @classmethod
       def get_client(cls, provider: str = None) -> BaseLLMClient:
           provider = provider or settings.LLM.DEFAULT_PROVIDER
           if provider not in cls._instances:
               cls._instances[provider] = cls._create_client(provider)
           return cls._instances[provider]
       
       @classmethod
       def _create_client(cls, provider: str) -> BaseLLMClient:
           if provider == "openai":
               return OpenAIClient(...)
           elif provider == "deepseek":
               return DeepSeekClient(...)
           elif provider == "qianwen":
               return QianwenClient(...)
           # ...
   ```

6. **app/integrations/llm/prompt_manager.py** - Prompt管理
   
   ```python
   class PromptManager:
       """Prompt模板管理"""
       
       def __init__(self, templates_dir: str = "prompts/"):
           self.templates_dir = templates_dir
           self.templates = {}
           self._load_templates()
       
       def render(self, template_name: str, **variables) -> str:
           """渲染模板"""
           template = self.templates.get(template_name)
           if not template:
               raise ValueError(f"模板 {template_name} 不存在")
           return template.render(**variables)
       
       def _load_templates(self):
           """从文件系统加载所有模板"""
           # 使用Jinja2加载.j2模板文件
           pass
   ```

7. **prompts/** 目录 - Prompt模板文件
   
   创建以下Jinja2模板：
   
   **prompts/intent_recognition.j2**:
   ```
   你是PM机器人的意图识别助手，需要从用户输入中识别用户意图。
   
   【可用的功能列表】
   {% for skill in available_skills %}
   - 名称：{{ skill.name }}
     描述：{{ skill.description }}
     参数：{{ skill.parameters | tojson }}
   {% endfor %}
   
   【用户上下文】
   - 当前项目：{{ context.project_name }}
   - 用户角色：{{ context.user_role }}
   - 历史对话：
   {% for msg in context.conversation_history[-5:] %}
     [{{ msg.role }}] {{ msg.content }}
   {% endfor %}
   
   【用户输入】
   {{ user_input }}
   
   【任务要求】
   请分析用户意图，并以JSON格式输出：
   {
     "success": true,
     "intent": "对应的功能名称（必须是上面列出的功能之一）",
     "confidence": 0.95,
     "parameters": {
       "参数名1": "参数值1",
       "参数名2": "参数值2"
     },
     "reasoning": "识别理由",
     "missing_parameters": ["缺失的必需参数"],
     "clarification_question": "如果需要澄清，要问用户什么"
   }
   
   【注意事项】
   1. 如果用户意图明确且参数完整，confidence应≥0.9
   2. 如果意图明确但参数不完整，列出缺失参数
   3. 如果意图不明确，confidence<0.7，并给出澄清问题
   4. intent必须严格匹配功能名称，不要自创
   5. 时间相关参数请转换为ISO格式（YYYY-MM-DD）
   ```
   
   **prompts/document_generation.j2** - 文档生成模板
   **prompts/risk_analysis.j2** - 风险分析模板
   **prompts/report_summary.j2** - 报告总结模板
   **prompts/meeting_minutes.j2** - 会议纪要模板
   **prompts/qa_with_rag.j2** - 问答模板（RAG）

8. **app/orchestrator/intent_recognizer.py** - 意图识别器
   
   ```python
   class IntentRecognizer:
       """意图识别器"""
       
       def __init__(self, llm_client, prompt_manager, skill_registry):
           self.llm = llm_client
           self.prompts = prompt_manager
           self.skill_registry = skill_registry
       
       async def recognize(
           self, user_input: str, context: UserContext,
           project_id: str
       ) -> IntentResult:
           """识别用户意图"""
           
           # 1. 获取该项目可用的Skills
           available_skills = await self.skill_registry.get_active_skills(
               project_id
           )
           
           # 2. 构建Prompt
           prompt = self.prompts.render(
               "intent_recognition",
               available_skills=available_skills,
               context=context,
               user_input=user_input
           )
           
           # 3. 调用LLM
           response = await self.llm.chat_completion(
               messages=[
                   {"role": "system", "content": "你是专业的意图识别助手"},
                   {"role": "user", "content": prompt}
               ],
               temperature=0.1,  # 意图识别要稳定
               response_format="json"
           )
           
           # 4. 解析结果
           try:
               result = json.loads(response.content)
               return IntentResult(**result)
           except (json.JSONDecodeError, ValidationError) as e:
               logger.error(f"意图解析失败: {e}, 原始响应: {response.content}")
               # 降级处理：返回低置信度结果
               return IntentResult(
                   success=False,
                   intent=None,
                   confidence=0.0,
                   message="抱歉，我没能理解您的意思，请换种方式表达"
               )
       
       async def recognize_with_function_calling(
           self, user_input: str, context: UserContext,
           project_id: str
       ) -> IntentResult:
           """
           使用Function Calling方式识别意图
           （对于支持的模型，效果更好）
           """
           # 1. 将Skills转换为tools定义
           tools = await self.skill_registry.get_tools_definition(project_id)
           
           # 2. 调用LLM
           response = await self.llm.chat_completion(
               messages=[
                   {"role": "system", "content": "..."},
                   {"role": "user", "content": user_input}
               ],
               tools=tools,
               tool_choice="auto"
           )
           
           # 3. 解析tool_calls
           if response.tool_calls:
               tool_call = response.tool_calls[0]
               return IntentResult(
                   success=True,
                   intent=tool_call.function.name,
                   confidence=0.95,
                   parameters=json.loads(tool_call.function.arguments)
               )
           else:
               # LLM未调用任何函数，转为普通对话
               return IntentResult(
                   success=False,
                   intent="general_chat",
                   message=response.content
               )
   ```

9. **app/orchestrator/parameter_extractor.py** - 参数提取器
   
   用于从对话中提取和补全参数：
   ```python
   class ParameterExtractor:
       """参数提取器 - 处理多轮对话中的参数补全"""
       
       async def extract_missing_parameters(
           self, intent: str, current_params: Dict,
           required_params: List[str], context: UserContext
       ) -> Dict:
           """从历史对话中尝试提取缺失参数"""
           pass
       
       async def generate_parameter_question(
           self, missing_param: str, intent: str, schema: Dict
       ) -> str:
           """生成询问用户参数的问题"""
           # 例如："请问您要查询哪个时间段的数据？"
           pass
       
       def validate_parameters(
           self, params: Dict, schema: Dict
       ) -> ValidationResult:
           """根据JSON Schema验证参数"""
           pass
   ```

10. **app/orchestrator/conversation_manager.py** - 对话状态管理
    
    管理多轮对话中的状态机：
    ```python
    class ConversationStateManager:
        """对话状态管理 - 处理多轮对话状态"""
        
        STATES = {
            "IDLE": "空闲状态",
            "AWAITING_PARAMETER": "等待参数",
            "AWAITING_CONFIRMATION": "等待确认",
            "EXECUTING": "执行中",
            "COMPLETED": "完成"
        }
        
        async def get_state(self, user_id: str, chat_id: str, redis) -> Dict:
            """获取当前状态"""
            pass
        
        async def transition(
            self, user_id: str, chat_id: str,
            new_state: str, state_data: Dict, redis
        ):
            """状态转换"""
            pass
        
        async def clear_state(self, user_id: str, chat_id: str, redis):
            """清除状态（用户取消或完成）"""
            pass
    ```

11. **app/integrations/llm/rag.py** - RAG（检索增强生成）
    
    用于知识问答场景：
    ```python
    class RAGEngine:
        """检索增强生成引擎"""
        
        def __init__(self, vector_store, llm_client, embedding_client):
            self.vector_store = vector_store
            self.llm = llm_client
            self.embedding = embedding_client
        
        async def query(
            self, question: str, top_k: int = 5,
            score_threshold: float = 0.7
        ) -> RAGResponse:
            """RAG问答"""
            # 1. 问题向量化
            query_vector = await self.embedding.encode(question)
            
            # 2. 向量检索
            relevant_docs = await self.vector_store.search(
                query_vector, top_k=top_k, score_threshold=score_threshold
            )
            
            # 3. 构建Prompt（带引用）
            context_text = "\n\n".join([
                f"[文档{i+1}] {doc.content}" 
                for i, doc in enumerate(relevant_docs)
            ])
            
            prompt = self.prompts.render(
                "qa_with_rag",
                question=question,
                context=context_text
            )
            
            # 4. 生成回答
            response = await self.llm.chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            
            return RAGResponse(
                answer=response.content,
                sources=relevant_docs,
                confidence=self._calculate_confidence(relevant_docs)
            )
        
        async def index_documents(
            self, documents: List[Document], collection: str
        ):
            """文档索引"""
            # 1. 文档分块（chunking）
            chunks = self._chunk_documents(documents)
            
            # 2. 向量化
            vectors = await self.embedding.encode_batch(
                [c.content for c in chunks]
            )
            
            # 3. 存入向量库
            await self.vector_store.add(chunks, vectors, collection)
    ```

12. **app/integrations/vector_store/milvus_client.py** - 向量数据库客户端
    
    封装Milvus操作：
    - create_collection
    - insert
    - search
    - delete
    - update

【交付物】
生成上述所有文件的完整代码。Prompt模板要专业、详细，能准确引导LLM输出。
重点关注：
1. LLM调用的可靠性（重试、降级）
2. 意图识别的准确率
3. 多轮对话的状态管理
4. Token成本控制
```

---

## 提示词 3.2：Skill框架设计与注册中心

```
现在构建PM机器人的核心 - Skill框架。这个框架决定了系统的可扩展性。

【设计目标】
- Skill是独立的、可插拔的业务能力单元
- 支持动态注册、动态启用/禁用
- 标准化的输入输出
- 完善的权限控制
- 详细的执行日志和审计

【任务要求】

1. **app/skills/base.py** - Skill基类
   
   ```python
   class SkillResult(BaseModel):
       """Skill执行结果"""
       status: Literal["success", "error", "partial"]
       data: Optional[Dict] = None
       message: Optional[str] = None
       artifacts: Optional[List[Dict]] = None  # 生成的文件等产物
       next_action: Optional[Dict] = None  # 建议的下一步操作
       metrics: Optional[Dict] = None  # 执行指标
   
   class SkillContext(BaseModel):
       """Skill执行上下文"""
       user_id: str
       user_name: str
       project_id: str
       project_name: str
       chat_id: Optional[str] = None
       message_id: Optional[str] = None
       trace_id: str
       conversation_history: List[Dict] = []
       extra: Dict = {}
   
   class BaseSkill(ABC):
       """Skill抽象基类
       
       每个具体Skill都必须继承此类并实现抽象方法。
       """
       
       # 元数据（子类必须定义）
       NAME: str = ""  # Skill唯一标识（中文，对用户可见）
       CODE: str = ""  # Skill代码（英文，用于内部）
       DISPLAY_NAME: str = ""
       DESCRIPTION: str = ""
       CATEGORY: SkillCategory = None  # PMBOK十大领域之一
       VERSION: str = "1.0.0"
       AUTHOR: str = "项目管理部"
       
       # 输入输出Schema（JSON Schema）
       INPUT_SCHEMA: Dict = {}
       OUTPUT_SCHEMA: Dict = {}
       
       # 权限要求（角色 -> 是否允许）
       PERMISSION_REQUIREMENTS: Dict[str, bool] = {
           "project_manager": True,
           "pm": True,
           "tech_lead": False,
           "member": False,
           "viewer": False
       }
       
       # 执行配置
       TIMEOUT_SECONDS: int = 30  # 执行超时
       REQUIRES_CONFIRMATION: bool = False  # 是否需要二次确认
       SUPPORTS_ASYNC: bool = False  # 是否支持异步执行（长任务）
       
       # 依赖项
       DEPENDENCIES: List[str] = []  # 依赖的其他Skills
       REQUIRED_INTEGRATIONS: List[str] = []  # 需要的外部系统集成
       
       def __init__(self, db, redis, services):
           self.db = db
           self.redis = redis
           self.services = services  # 注入的服务集合
       
       @abstractmethod
       async def execute(
           self, params: Dict, context: SkillContext
       ) -> SkillResult:
           """执行Skill的核心逻辑（子类必须实现）"""
           pass
       
       async def validate_input(self, params: Dict) -> ValidationResult:
           """验证输入参数（基于JSON Schema）"""
           try:
               jsonschema.validate(params, self.INPUT_SCHEMA)
               return ValidationResult(valid=True)
           except jsonschema.ValidationError as e:
               return ValidationResult(
                   valid=False, error_msg=str(e.message)
               )
       
       async def pre_execute(
           self, params: Dict, context: SkillContext
       ) -> Optional[SkillResult]:
           """执行前钩子（可选实现）
           
           返回非None则中断执行，常用于：
           - 业务规则检查
           - 二次确认流程
           - 数据准备
           """
           return None
       
       async def post_execute(
           self, params: Dict, context: SkillContext, result: SkillResult
       ) -> SkillResult:
           """执行后钩子（可选实现）
           
           常用于：
           - 结果增强
           - 通知发送
           - 数据归档
           """
           return result
       
       async def on_error(
           self, params: Dict, context: SkillContext, error: Exception
       ) -> SkillResult:
           """错误处理钩子"""
           logger.error(
               f"Skill {self.NAME} 执行失败",
               exc_info=True,
               extra={"context": context.dict()}
           )
           return SkillResult(
               status="error",
               message=f"执行失败：{str(error)}"
           )
       
       def get_metadata(self) -> Dict:
           """获取Skill元数据"""
           return {
               "name": self.NAME,
               "code": self.CODE,
               "display_name": self.DISPLAY_NAME,
               "description": self.DESCRIPTION,
               "category": self.CATEGORY.value if self.CATEGORY else None,
               "version": self.VERSION,
               "author": self.AUTHOR,
               "input_schema": self.INPUT_SCHEMA,
               "output_schema": self.OUTPUT_SCHEMA,
               "permissions": self.PERMISSION_REQUIREMENTS,
               "timeout": self.TIMEOUT_SECONDS,
               "requires_confirmation": self.REQUIRES_CONFIRMATION,
               "dependencies": self.DEPENDENCIES,
               "required_integrations": self.REQUIRED_INTEGRATIONS
           }
       
       def get_tool_definition(self) -> Dict:
           """获取Function Calling格式的工具定义"""
           return {
               "type": "function",
               "function": {
                   "name": self.CODE,
                   "description": self.DESCRIPTION,
                   "parameters": self.INPUT_SCHEMA
               }
           }
   ```

2. **app/skills/registry.py** - Skill注册中心
   
   ```python
   class SkillRegistry:
       """Skill注册中心 - 管理所有Skills的全局注册表"""
       
       _skills: Dict[str, Type[BaseSkill]] = {}
       _instances: Dict[str, BaseSkill] = {}
       
       @classmethod
       def register(cls, skill_class: Type[BaseSkill]):
           """注册Skill类（装饰器用法）"""
           if not skill_class.CODE:
               raise ValueError(f"Skill {skill_class.__name__} 必须定义CODE")
           
           if skill_class.CODE in cls._skills:
               logger.warning(f"Skill {skill_class.CODE} 已存在，将被覆盖")
           
           cls._skills[skill_class.CODE] = skill_class
           logger.info(f"已注册 Skill: {skill_class.CODE}")
           return skill_class
       
       @classmethod
       def get_skill_class(cls, code: str) -> Optional[Type[BaseSkill]]:
           """获取Skill类"""
           return cls._skills.get(code)
       
       @classmethod
       def get_skill_instance(
           cls, code: str, db, redis, services
       ) -> Optional[BaseSkill]:
           """获取Skill实例（按需创建）"""
           skill_class = cls.get_skill_class(code)
           if not skill_class:
               return None
           
           # 简单实现：每次创建新实例
           # 优化：可以做单例池
           return skill_class(db, redis, services)
       
       @classmethod
       def list_all_skills(cls) -> List[Dict]:
           """列出所有已注册Skills的元数据"""
           return [
               skill_class().get_metadata()
               for skill_class in cls._skills.values()
           ]
       
       @classmethod
       def list_skills_by_category(
           cls, category: SkillCategory
       ) -> List[Type[BaseSkill]]:
           """按分类列出Skills"""
           return [
               s for s in cls._skills.values()
               if s.CATEGORY == category
           ]
       
       @classmethod
       def auto_discover(cls, package: str = "app.skills"):
           """自动发现并加载所有Skills
           
           扫描指定包下的所有模块，自动注册标记的Skills
           """
           import importlib
           import pkgutil
           
           package_module = importlib.import_module(package)
           for _, name, is_pkg in pkgutil.walk_packages(
               package_module.__path__, prefix=f"{package}."
           ):
               if is_pkg:
                   continue
               try:
                   importlib.import_module(name)
               except Exception as e:
                   logger.error(f"加载Skill模块失败 {name}: {e}")
   ```

3. **app/services/skill_service.py** - Skill业务服务
   
   ```python
   class SkillService:
       """Skill管理服务"""
       
       async def initialize_skills_in_db(self, db: AsyncSession):
           """将所有已注册的Skills元数据同步到数据库"""
           all_skills = SkillRegistry.list_all_skills()
           for skill_meta in all_skills:
               await self.upsert_skill_config(skill_meta, db)
       
       async def upsert_skill_config(
           self, skill_meta: Dict, db: AsyncSession
       ):
           """更新或插入Skill配置"""
           pass
       
       async def is_skill_active_for_project(
           self, skill_code: str, project_id: str,
           db, redis
       ) -> bool:
           """检查Skill是否对项目启用"""
           cache_key = f"skill:active:{project_id}:{skill_code}"
           cached = await redis.get(cache_key)
           if cached is not None:
               return cached == "1"
           
           mapping = await self.project_skill_mapping_repo.get(
               project_id, skill_code, db
           )
           is_active = mapping is not None and mapping.is_active
           
           await redis.setex(cache_key, 3600, "1" if is_active else "0")
           return is_active
       
       async def enable_skill_for_project(
           self, project_id: str, skill_code: str,
           operator_id: str, db, redis
       ):
           """为项目启用Skill"""
           # 检查Skill存在
           skill_class = SkillRegistry.get_skill_class(skill_code)
           if not skill_class:
               raise SkillNotFoundException(f"Skill {skill_code} 不存在")
           
           # 检查依赖
           for dep in skill_class.DEPENDENCIES:
               dep_active = await self.is_skill_active_for_project(
                   dep, project_id, db, redis
               )
               if not dep_active:
                   raise BusinessException(
                       f"Skill {skill_code} 依赖 {dep}，请先启用"
               )
           
           # 创建/更新映射
           await self.project_skill_mapping_repo.upsert({
               "project_id": project_id,
               "skill_code": skill_code,
               "is_active": True,
               "activated_by": operator_id,
               "activated_at": datetime.now()
           }, db)
           
           # 清除缓存
           await redis.delete(f"skill:active:{project_id}:{skill_code}")
           await redis.delete(f"skill:active_list:{project_id}")
           
           # 审计
           await self.audit_service.log_action(
               user_id=operator_id,
               action="enable_skill",
               object_type="project_skill",
               object_id=f"{project_id}:{skill_code}"
           )
       
       async def disable_skill_for_project(
           self, project_id: str, skill_code: str,
           operator_id: str, db, redis
       ):
           """为项目禁用Skill"""
           # 类似实现
           pass
       
       async def batch_enable_skills(
           self, project_id: str, skill_codes: List[str],
           operator_id: str, db, redis
       ) -> Dict[str, bool]:
           """批量启用"""
           results = {}
           for code in skill_codes:
               try:
                   await self.enable_skill_for_project(
                       project_id, code, operator_id, db, redis
                   )
                   results[code] = True
               except Exception as e:
                   logger.error(f"启用Skill {code} 失败: {e}")
                   results[code] = False
           return results
       
       async def get_active_skills_for_project(
           self, project_id: str, db, redis
       ) -> List[Dict]:
           """获取项目已启用的所有Skills"""
           cache_key = f"skill:active_list:{project_id}"
           cached = await redis.get_json(cache_key)
           if cached:
               return cached
           
           mappings = await self.project_skill_mapping_repo.get_active(
               project_id, db
           )
           skills = []
           for mapping in mappings:
               skill_class = SkillRegistry.get_skill_class(mapping.skill_code)
               if skill_class:
                   skills.append(skill_class().get_metadata())
           
           await redis.set_json(cache_key, skills, ttl=1800)
           return skills
       
       async def configure_for_project_type(
           self, project_id: str, project_type: str,
           operator_id: str, db, redis
       ):
           """根据项目类型批量配置Skills"""
           SKILL_TEMPLATES = {
               "标准IT项目": [
                   "create_pre_initiation_doc", "create_initiation_doc",
                   "create_wbs", "create_schedule_plan",
                   "track_task_progress", "estimate_cost", "monitor_cost",
                   "track_timesheet", "generate_weekly_report",
                   "create_meeting_minutes", "identify_risks",
                   "query_project_overview", "prepare_stakeholder_report"
               ],
               "敏捷项目": [
                   "create_wbs", "sprint_planning", "burndown_chart",
                   "daily_standup_minutes", "sprint_retrospective",
                   "track_timesheet", "query_project_overview"
               ],
               "运维项目": [
                   "track_defect_fix", "monitor_cost", "track_timesheet",
                   "generate_weekly_report", "query_project_overview"
               ]
           }
           skill_codes = SKILL_TEMPLATES.get(project_type, [])
           return await self.batch_enable_skills(
               project_id, skill_codes, operator_id, db, redis
           )
   ```

4. **app/skills/executor.py** - Skill执行引擎
   
   ```python
   class SkillExecutor:
       """Skill执行引擎 - 统一的执行流程管控"""
       
       def __init__(self, db, redis, services):
           self.db = db
           self.redis = redis
           self.services = services
       
       async def execute(
           self, skill_code: str, params: Dict,
           context: SkillContext
       ) -> SkillResult:
           """执行Skill的统一入口"""
           
           start_time = time.time()
           execution_id = str(uuid.uuid4())
           
           # 记录执行开始
           await self._log_execution_start(
               execution_id, skill_code, params, context
           )
           
           try:
               # 1. 获取Skill实例
               skill = SkillRegistry.get_skill_instance(
                   skill_code, self.db, self.redis, self.services
               )
               if not skill:
                   raise SkillNotFoundException(
                       f"Skill {skill_code} 未找到"
                   )
               
               # 2. 输入验证
               validation = await skill.validate_input(params)
               if not validation.valid:
                   return SkillResult(
                       status="error",
                       message=f"参数错误：{validation.error_msg}"
                   )
               
               # 3. 执行前钩子
               pre_result = await skill.pre_execute(params, context)
               if pre_result is not None:
                   return pre_result  # 中断执行
               
               # 4. 主执行（带超时控制）
               try:
                   result = await asyncio.wait_for(
                       skill.execute(params, context),
                       timeout=skill.TIMEOUT_SECONDS
                   )
               except asyncio.TimeoutError:
                   return SkillResult(
                       status="error",
                       message=f"执行超时（>{skill.TIMEOUT_SECONDS}秒）"
                   )
               
               # 5. 执行后钩子
               result = await skill.post_execute(params, context, result)
               
               # 6. 记录执行成功
               elapsed = time.time() - start_time
               await self._log_execution_success(
                   execution_id, skill_code, result, elapsed
               )
               
               # 7. 更新执行统计
               await self._update_skill_metrics(
                   skill_code, "success", elapsed
               )
               
               return result
               
           except Exception as e:
               # 错误处理
               elapsed = time.time() - start_time
               
               try:
                   error_result = await skill.on_error(params, context, e)
               except:
                   error_result = SkillResult(
                       status="error",
                       message=f"执行失败：{str(e)}"
                   )
               
               await self._log_execution_failure(
                   execution_id, skill_code, e, elapsed
               )
               await self._update_skill_metrics(
                   skill_code, "failure", elapsed
               )
               
               # 检查是否需要熔断
               await self._check_circuit_breaker(skill_code)
               
               return error_result
       
       async def _log_execution_start(self, execution_id, skill_code, params, context):
           """记录执行开始日志"""
           pass
       
       async def _log_execution_success(self, execution_id, skill_code, result, elapsed):
           """记录执行成功日志"""
           pass
       
       async def _log_execution_failure(self, execution_id, skill_code, error, elapsed):
           """记录执行失败日志"""
           pass
       
       async def _update_skill_metrics(self, skill_code, status, elapsed):
           """更新Skill执行指标"""
           # Redis计数器
           # success_count, failure_count, total_elapsed, avg_elapsed
           pass
       
       async def _check_circuit_breaker(self, skill_code: str):
           """熔断检查 - 失败率过高时自动熔断"""
           # 滑动窗口统计：最近100次执行的失败率
           # 失败率>50%时自动禁用Skill
           pass
   ```

5. **app/skills/circuit_breaker.py** - 熔断器
   
   实现Skill级别的熔断机制：
   - 滑动窗口统计
   - 失败率阈值
   - 半开状态恢复

6. **app/api/v1/skills.py** - Skills管理API
   
   实现以下端点：
   - GET /api/v1/skills - 列出所有Skills
   - GET /api/v1/skills/{code} - 获取Skill详情
   - GET /api/v1/projects/{project_id}/skills - 列出项目已启用的Skills
   - POST /api/v1/projects/{project_id}/skills/{code}/enable - 启用Skill
   - POST /api/v1/projects/{project_id}/skills/{code}/disable - 禁用Skill
   - POST /api/v1/projects/{project_id}/skills/batch-enable - 批量启用
   - GET /api/v1/projects/{project_id}/skills/templates - 获取模板
   - POST /api/v1/projects/{project_id}/skills/apply-template - 应用模板
   - GET /api/v1/skills/{code}/executions - 查询执行历史
   - GET /api/v1/skills/{code}/metrics - 查询执行指标

【交付物】
生成上述所有文件的完整代码，特别关注：
1. Skill框架的可扩展性
2. 注册中心的优雅设计
3. 执行引擎的健壮性（超时、熔断、错误处理）
4. 完善的执行日志和指标
```

---

## 提示词 3.3：编排引擎主体与多Agent协同

```
现在实现PM机器人的"大脑" - OpenClaw编排引擎主体。

【任务要求】

1. **app/orchestrator/orchestrator.py** - 主编排引擎
   
   ```python
   class Orchestrator:
       """
       PM机器人主编排引擎
       
       协调以下组件完成端到端的请求处理：
       - 意图识别器
       - 权限校验
       - Skill执行器
       - 对话管理
       - 结果格式化
       """
       
       def __init__(
           self,
           intent_recognizer: IntentRecognizer,
           skill_executor: SkillExecutor,
           permission_service: PermissionService,
           isolation_service: ProjectIsolationService,
           skill_service: SkillService,
           conversation_manager: ConversationStateManager,
           response_formatter: ResponseFormatter,
           db, redis
       ):
           self.intent_recognizer = intent_recognizer
           self.skill_executor = skill_executor
           self.permission_service = permission_service
           self.isolation_service = isolation_service
           self.skill_service = skill_service
           self.conversation_manager = conversation_manager
           self.response_formatter = response_formatter
           self.db = db
           self.redis = redis
       
       async def orchestrate(
           self, user_input: str, context: UserContext,
           user_id: str, project_id: str,
           message_id: str = None
       ) -> Dict:
           """主编排流程"""
           
           trace_id = generate_trace_id()
           
           with tracing_context(trace_id=trace_id, user_id=user_id):
               try:
                   # === 阶段1：状态机检查 ===
                   # 检查是否在多轮对话的某个状态中
                   conv_state = await self.conversation_manager.get_state(
                       user_id, context.chat_id, self.redis
                   )
                   
                   if conv_state and conv_state["state"] != "IDLE":
                       # 处理多轮对话的后续输入
                       return await self._handle_continued_conversation(
                           user_input, conv_state, context, user_id, project_id
                       )
                   
                   # === 阶段2：项目隔离强制校验 ===
                   await self.isolation_service.enforce_chat_project_binding(
                       context.chat_id, project_id, self.db, self.redis
                   )
                   await self.isolation_service.enforce_user_in_project(
                       user_id, project_id, self.db, self.redis
                   )
                   
                   # === 阶段3：意图识别 ===
                   intent_result = await self.intent_recognizer.recognize(
                       user_input, context, project_id
                   )
                   
                   # 处理特殊意图
                   if intent_result.intent == "general_chat":
                       # 普通对话，调用通用对话能力
                       return await self._handle_general_chat(
                           user_input, context
                       )
                   
                   if intent_result.intent == "help":
                       return await self._handle_help_request(
                           context, project_id
                       )
                   
                   # 低置信度，请求澄清
                   if intent_result.confidence < 0.7:
                       return self._build_clarification_response(intent_result)
                   
                   # === 阶段4：参数完整性检查 ===
                   if intent_result.missing_parameters:
                       # 进入参数收集状态
                       await self.conversation_manager.transition(
                           user_id, context.chat_id,
                           new_state="AWAITING_PARAMETER",
                           state_data={
                               "intent": intent_result.intent,
                               "collected_params": intent_result.parameters,
                               "missing_params": intent_result.missing_parameters
                           },
                           redis=self.redis
                       )
                       return self._build_parameter_request(intent_result)
                   
                   # === 阶段5：权限校验 ===
                   has_permission = await self.permission_service.check_skill_permission(
                       user_id, project_id, intent_result.intent,
                       self.db, self.redis
                   )
                   if not has_permission:
                       return {
                           "status": "error",
                           "message": f"您无权执行【{intent_result.intent}】操作，"
                                      f"请联系项目经理"
                       }
                   
                   # === 阶段6：Skill激活检查 ===
                   skill_active = await self.skill_service.is_skill_active_for_project(
                       intent_result.intent, project_id, self.db, self.redis
                   )
                   if not skill_active:
                       return {
                           "status": "error",
                           "message": f"功能【{intent_result.intent}】未在该项目启用，"
                                      f"请联系项目管理员开启"
                       }
                   
                   # === 阶段7：二次确认（如需要）===
                   skill_class = SkillRegistry.get_skill_class(intent_result.intent)
                   if skill_class.REQUIRES_CONFIRMATION:
                       await self.conversation_manager.transition(
                           user_id, context.chat_id,
                           new_state="AWAITING_CONFIRMATION",
                           state_data={
                               "intent": intent_result.intent,
                               "params": intent_result.parameters
                           },
                           redis=self.redis
                       )
                       return self._build_confirmation_request(intent_result)
                   
                   # === 阶段8：执行Skill ===
                   skill_context = SkillContext(
                       user_id=user_id,
                       user_name=context.user_name,
                       project_id=project_id,
                       project_name=context.project_name,
                       chat_id=context.chat_id,
                       message_id=message_id,
                       trace_id=trace_id,
                       conversation_history=context.conversation_history
                   )
                   
                   skill_result = await self.skill_executor.execute(
                       skill_code=intent_result.intent,
                       params=intent_result.parameters,
                       context=skill_context
                   )
                   
                   # === 阶段9：清除状态机 ===
                   await self.conversation_manager.clear_state(
                       user_id, context.chat_id, self.redis
                   )
                   
                   # === 阶段10：格式化响应 ===
                   formatted_response = await self.response_formatter.format(
                       skill_result, intent_result.intent, context
                   )
                   
                   # === 阶段11：更新对话历史 ===
                   await self._update_conversation_history(
                       user_id, context.chat_id, user_input, formatted_response
                   )
                   
                   return formatted_response
                   
               except ProjectIsolationException as e:
                   logger.warning(f"项目隔离违规: {e}")
                   return {
                       "status": "error",
                       "message": "您不在该项目中，无权访问"
                   }
               except PermissionDeniedException as e:
                   return {"status": "error", "message": str(e)}
               except Exception as e:
                   logger.error("编排失败", exc_info=True)
                   return {
                       "status": "error",
                       "message": "处理失败，请稍后重试或联系管理员"
                   }
       
       async def _handle_continued_conversation(
           self, user_input, conv_state, context, user_id, project_id
       ):
           """处理多轮对话的后续输入"""
           state = conv_state["state"]
           state_data = conv_state["data"]
           
           if state == "AWAITING_PARAMETER":
               # 用户在补充参数
               return await self._collect_parameter(
                   user_input, state_data, context, user_id, project_id
               )
           
           elif state == "AWAITING_CONFIRMATION":
               # 用户在确认
               return await self._handle_confirmation(
                   user_input, state_data, context, user_id, project_id
               )
           
           else:
               # 未知状态，重置
               await self.conversation_manager.clear_state(
                   user_id, context.chat_id, self.redis
               )
               return await self.orchestrate(
                   user_input, context, user_id, project_id
               )
       
       async def _collect_parameter(self, user_input, state_data, context, user_id, project_id):
           """收集参数"""
           # 1. 解析用户输入，更新参数
           # 2. 检查是否还有缺失参数
           # 3. 如果完整，继续执行；否则继续询问
           pass
       
       async def _handle_confirmation(self, user_input, state_data, context, user_id, project_id):
           """处理确认"""
           # 简单匹配："是/确认/yes" 或 "否/取消/no"
           if user_input.lower() in ["是", "确认", "yes", "y", "好的", "确定"]:
               # 用户确认，执行Skill
               # ...
               pass
           else:
               # 用户取消
               await self.conversation_manager.clear_state(
                   user_id, context.chat_id, self.redis
               )
               return {"status": "cancelled", "message": "已取消操作"}
       
       async def _handle_general_chat(self, user_input, context):
           """处理普通对话"""
           # 调用LLM进行通用对话
           pass
       
       async def _handle_help_request(self, context, project_id):
           """处理帮助请求"""
           # 列出当前项目可用的所有功能
           skills = await self.skill_service.get_active_skills_for_project(
               project_id, self.db, self.redis
           )
           return {
               "status": "success",
               "type": "help",
               "data": {"available_skills": skills}
           }
       
       def _build_clarification_response(self, intent_result):
           """构建澄清请求响应"""
           pass
       
       def _build_parameter_request(self, intent_result):
           """构建参数请求响应"""
           pass
       
       def _build_confirmation_request(self, intent_result):
           """构建确认请求响应"""
           pass
       
       async def _update_conversation_history(self, user_id, chat_id, user_input, response):
           """更新对话历史"""
           pass
   ```

2. **app/orchestrator/response_formatter.py** - 响应格式化器
   
   ```python
   class ResponseFormatter:
       """统一响应格式化"""
       
       async def format(
           self, skill_result: SkillResult,
           skill_code: str, context: UserContext
       ) -> Dict:
           """根据Skill结果格式化为飞书可发送的内容"""
           
           if skill_result.status == "error":
               return self._format_error(skill_result)
           
           # 根据数据类型选择不同的展示方式
           data = skill_result.data or {}
           data_type = data.get("type", "text")
           
           formatters = {
               "text": self._format_text,
               "card": self._format_card,
               "table": self._format_table,
               "file": self._format_file,
               "report": self._format_report,
               "chart": self._format_chart,
               "form": self._format_form,
           }
           
           formatter = formatters.get(data_type, self._format_text)
           return await formatter(skill_result, context)
       
       def _format_text(self, result, context):
           """格式化为文本消息"""
           pass
       
       def _format_card(self, result, context):
           """格式化为卡片消息"""
           pass
       
       def _format_table(self, result, context):
           """格式化为表格"""
           pass
       
       def _format_file(self, result, context):
           """格式化为文件消息"""
           pass
       
       def _format_report(self, result, context):
           """格式化为报告（卡片+文件）"""
           pass
       
       def _format_chart(self, result, context):
           """格式化为图表"""
           pass
       
       def _format_form(self, result, context):
           """格式化为表单卡片"""
           pass
   ```

3. **app/orchestrator/agents/__init__.py** - 多Agent模块
   
   设计多Agent协同架构：
   
4. **app/orchestrator/agents/planner_agent.py** - Planner Agent
   
   负责复杂任务的拆解：
   ```python
   class PlannerAgent:
       """
       规划Agent - 处理需要多步骤的复杂任务
       
       例如："准备给老板的项目汇报"，需要：
       1. 收集进度数据
       2. 分析风险
       3. 生成PPT
       4. 发送通知
       """
       
       async def plan(self, user_intent: str, context: UserContext) -> Plan:
           """生成执行计划"""
           # 调用LLM拆解任务
           pass
       
       async def execute_plan(self, plan: Plan, context: SkillContext):
           """执行计划"""
           # 按依赖顺序执行各步骤
           # 处理步骤间的数据传递
           pass
   ```

5. **app/orchestrator/agents/auditor_agent.py** - Auditor Agent
   
   负责结果审核：
   ```python
   class AuditorAgent:
       """
       审核Agent - 对生成的内容进行合规性审核
       
       例如：生成的立项材料是否符合规范？
       """
       
       async def audit(
           self, content_type: str, content: str,
           rules: List[str] = None
       ) -> AuditResult:
           """审核内容"""
           pass
   ```

6. **app/orchestrator/__init__.py** - 编排引擎初始化
   
   ```python
   def create_orchestrator(db, redis, settings) -> Orchestrator:
       """创建编排引擎实例"""
       # 初始化各个组件并注入
       pass
   ```

【交付物】
生成上述所有文件的完整代码，确保整个编排流程清晰、可调试、可扩展。
```

---

##  Part 3 完成检查清单

- [ ] LLM抽象层完成，支持多个provider切换
- [ ] Prompt模板系统可工作
- [ ] 意图识别准确率达到目标
- [ ] Skill基类设计完整
- [ ] Skill注册中心可自动发现Skills
- [ ] 编排引擎可正确处理完整流程
- [ ] 多轮对话状态机可工作
- [ ] 熔断器机制有效
- [ ] RAG引擎可正确检索知识
- [ ] 所有组件的单元测试覆盖

---

#  Part 4：业务Skills批量开发（按PMBOK十大领域）

> **目标**：开发40+具体业务Skills，覆盖PMBOK十大知识领域
>
> **预计耗时**：8-10天

---

## 提示词 4.1：基础查询类Skills开发

```
基于已建立的Skill框架，开发第一批基础查询类Skills。

【任务要求】

1. **app/skills/integration_mgmt/query_project_overview.py** - 项目总览查询
   
   ```python
   @SkillRegistry.register
   class QueryProjectOverviewSkill(BaseSkill):
       """项目总览查询 - 查询项目当前的完整状态"""
       
       NAME = "项目总览查询"
       CODE = "query_project_overview"
       DISPLAY_NAME = " 项目总览"
       DESCRIPTION = "查询项目当前的整体情况，包括进度、成本、风险、里程碑等"
       CATEGORY = SkillCategory.INTEGRATION_MGMT
       
       INPUT_SCHEMA = {
           "type": "object",
           "properties": {
               "include_details": {
                   "type": "boolean",
                   "default": True,
                   "description": "是否包含详细信息"
               }
           }
       }
       
       PERMISSION_REQUIREMENTS = {
           "project_manager": True,
           "pm": True,
           "tech_lead": True,
           "member": True,
           "viewer": True
       }
       
       async def execute(self, params, context):
           project_id = context.project_id
           
           # 并行查询多个维度的数据
           project, progress, cost, risks, milestones, team = await asyncio.gather(
               self.services.project_service.get_project(project_id),
               self.services.progress_service.get_overall_progress(project_id),
               self.services.cost_service.get_cost_status(project_id),
               self.services.risk_service.get_top_risks(project_id, limit=3),
               self.services.milestone_service.get_milestones(project_id),
               self.services.team_service.get_team_summary(project_id)
           )
           
           overview_data = {
               "project_info": {
                   "id": project.id,
                   "name": project.name,
                   "status": project.status,
                   "stage": project.current_stage,
                   "manager": project.responsible_person,
                   "team_size": team.total_members
               },
               "schedule": {
                   "overall_progress": progress.percentage,
                   "completed_tasks": progress.completed_count,
                   "total_tasks": progress.total_count,
                   "is_on_schedule": progress.on_schedule,
                   "delay_days": progress.delay_days,
                   "current_milestone": milestones.current,
                   "next_milestone": milestones.next
               },
               "cost": {
                   "budget": cost.budget_total,
                   "spent": cost.actual_spent,
                   "remaining": cost.remaining,
                   "spent_percentage": cost.spent_percentage,
                   "cpi": cost.cpi,
                   "spi": cost.spi,
                   "is_over_budget": cost.is_over_budget,
                   "forecast": cost.eac
               },
               "risks": [
                   {
                       "name": r.risk_name,
                       "level": r.risk_level,
                       "score": r.risk_score
                   } for r in risks
               ]
           }
           
           return SkillResult(
               status="success",
               data={
                   "type": "project_overview_card",
                   "overview": overview_data,
                   "rendered_at": datetime.now().isoformat()
               },
               message="已为您准备项目总览"
           )
   ```

2. **app/skills/schedule_mgmt/query_progress.py** - 查询进度
3. **app/skills/schedule_mgmt/query_milestones.py** - 查询里程碑
4. **app/skills/schedule_mgmt/query_tasks.py** - 查询任务列表
5. **app/skills/schedule_mgmt/query_my_tasks.py** - 查询我的任务
6. **app/skills/cost_mgmt/query_cost_status.py** - 查询成本状态
7. **app/skills/cost_mgmt/query_evm_metrics.py** - 查询EVM指标
8. **app/skills/risk_mgmt/query_risks.py** - 查询风险列表
9. **app/skills/resource_mgmt/query_team_workload.py** - 查询团队负荷
10. **app/skills/resource_mgmt/query_timesheet.py** - 查询工时统计
11. **app/skills/stakeholder_mgmt/query_stakeholders.py** - 查询干系人

每个Skill都要：
- 完整的元数据定义
- 输入输出Schema
- 详细的业务逻辑
- 错误处理
- 单元测试

【交付物】
生成上述11个查询类Skills的完整实现。
```

---

## 提示词 4.2：文档生成类Skills开发

```
开发文档生成类Skills，这是PM机器人最有价值的能力之一。

【任务要求】

1. **app/skills/integration_mgmt/create_pre_initiation_doc.py** - 预立项材料生成
   
   ```python
   @SkillRegistry.register
   class CreatePreInitiationDocSkill(BaseSkill):
       """预立项材料编写"""
       
       NAME = "预立项材料编写"
       CODE = "create_pre_initiation_doc"
       DISPLAY_NAME = " 预立项材料"
       DESCRIPTION = "根据项目基本信息，自动生成预立项申请材料"
       CATEGORY = SkillCategory.INTEGRATION_MGMT
       
       REQUIRES_CONFIRMATION = True  # 需要确认
       TIMEOUT_SECONDS = 60
       
       INPUT_SCHEMA = {
           "type": "object",
           "properties": {
               "project_name": {"type": "string", "description": "项目名称"},
               "background": {"type": "string", "description": "项目背景"},
               "objectives": {"type": "string", "description": "项目目标"},
               "scope": {"type": "string", "description": "项目范围"},
               "estimated_budget": {"type": "number", "description": "预估预算（万元）"},
               "estimated_duration": {"type": "integer", "description": "预估周期（月）"},
               "format": {
                   "type": "string",
                   "enum": ["docx", "pdf", "markdown"],
                   "default": "docx"
               }
           },
           "required": ["project_name", "background", "objectives"]
       }
       
       PERMISSION_REQUIREMENTS = {
           "project_manager": True,
           "pm": True,
           "tech_lead": False,
           "member": False
       }
       
       async def execute(self, params, context):
           # 1. 收集项目相关数据
           project_data = await self._gather_project_data(
               context.project_id, params
           )
           
           # 2. 加载预立项模板
           template = await self.services.template_service.get_template(
               "pre_initiation"
           )
           
           # 3. 调用LLM生成内容（基于模板和数据）
           content = await self.services.llm_service.generate_document(
               template_name="pre_initiation",
               template_content=template.content,
               variables=project_data,
               style_guide="正式商务风格，符合银行业项目立项规范"
           )
           
           # 4. 内容审核（合规性检查）
           audit_result = await self.services.audit_agent.audit(
               content_type="pre_initiation",
               content=content,
               rules=[
                   "必须包含项目背景、目标、范围",
                   "预算金额必须合理",
                   "需求描述清晰准确"
               ]
           )
           
           if not audit_result.passed:
               # 自动修正
               content = await self.services.llm_service.refine_document(
                   content, audit_result.issues
               )
           
           # 5. 渲染为目标格式
           file_bytes, file_name = await self._render_document(
               content, params.get("format", "docx"),
               project_name=params["project_name"]
           )
           
           # 6. 上传到飞书云空间
           file_token = await self.services.lark_file_service.upload_file(
               file_bytes, file_name
           )
           
           # 7. 保存文档记录
           doc_record = await self.services.document_service.save_document({
               "project_id": context.project_id,
               "doc_type": "预立项材料",
               "doc_name": file_name,
               "file_token": file_token,
               "content": content,
               "created_by": context.user_id,
               "status": "draft"
           })
           
           # 8. 创建审批流（可选）
           approval_url = None
           if self.services.config.AUTO_CREATE_APPROVAL:
               approval = await self.services.approval_service.create(
                   approval_type="pre_initiation",
                   document_id=doc_record.id,
                   initiator=context.user_id
               )
               approval_url = approval.url
           
           return SkillResult(
               status="success",
               data={
                   "type": "report",
                   "doc_id": doc_record.id,
                   "file_token": file_token,
                   "file_name": file_name,
                   "preview_url": f"https://lark.../docs/{file_token}",
                   "approval_url": approval_url,
                   "summary": {
                       "项目名称": params["project_name"],
                       "页数": "约5页",
                       "字数": len(content),
                       "状态": "草稿"
                   }
               },
               message=" 预立项材料已生成，请查收并审核",
               artifacts=[{
                   "type": "file",
                   "file_token": file_token,
                   "file_name": file_name
               }],
               next_action={
                   "suggestion": "建议您预览文档后提交审批",
                   "actions": [
                       {"label": "预览", "type": "view", "value": file_token},
                       {"label": "提交审批", "type": "submit", "value": doc_record.id},
                       {"label": "重新生成", "type": "regenerate"}
                   ]
               }
           )
       
       async def _gather_project_data(self, project_id, params):
           """收集生成文档所需的数据"""
           pass
       
       async def _render_document(self, content, format, **kwargs):
           """渲染文档为指定格式"""
           if format == "docx":
               return await self._render_docx(content, **kwargs)
           elif format == "pdf":
               return await self._render_pdf(content, **kwargs)
           else:
               return content.encode("utf-8"), f"{kwargs['project_name']}.md"
   ```

2. **app/skills/integration_mgmt/create_initiation_doc.py** - 立项材料编写
3. **app/skills/scope_mgmt/create_wbs.py** - WBS编写（含WBS可视化）
4. **app/skills/integration_mgmt/create_collaboration_doc.py** - 内部协同材料
5. **app/skills/procurement_mgmt/create_contract.py** - 合同编写
6. **app/skills/communication_mgmt/generate_daily_report.py** - 日报生成
7. **app/skills/communication_mgmt/generate_weekly_report.py** - 周报生成
8. **app/skills/communication_mgmt/generate_monthly_report.py** - 月报生成
9. **app/skills/communication_mgmt/create_meeting_minutes.py** - 会议纪要
10. **app/skills/communication_mgmt/prepare_stakeholder_report.py** - 干系人汇报材料（含PPT生成）
11. **app/skills/integration_mgmt/create_closure_report.py** - 结项总结报告

【共性技术要点】
- 使用python-docx生成Word文档
- 使用python-pptx生成PPT
- 模板存储在templates/目录
- 支持LLM动态生成+模板填充
- 自动上传到飞书云空间
- 版本管理

【交付物】
生成上述11个文档生成类Skills的完整实现。
请同时提供模板文件结构和示例。
```

---

## 提示词 4.3：进度、成本、风险管理类Skills开发

```
开发PMBOK核心领域的管理类Skills。

【任务要求】

**进度管理类（5个）：**

1. **app/skills/schedule_mgmt/create_schedule_plan.py** - 进度计划制定
   - 输入：里程碑列表、任务清单
   - 输出：甘特图（图片）+ 任务排期
   - 自动计算关键路径
   
2. **app/skills/schedule_mgmt/update_task_status.py** - 更新任务状态
   - 支持单个/批量更新
   - 自动重新计算项目进度
   - 触发依赖任务的状态更新
   - 关键路径变化预警

3. **app/skills/schedule_mgmt/track_defect_fix.py** - 缺陷修复跟进
   - 对接缺陷管理系统
   - 自动跟踪缺陷状态
   - 闭环报告生成

4. **app/skills/schedule_mgmt/critical_path_analysis.py** - 关键路径分析
   - CPM算法实现
   - 关键任务标识
   - 浮动时间计算

5. **app/skills/schedule_mgmt/schedule_variance_alert.py** - 进度偏差预警
   - 实时监控
   - 偏差>阈值自动预警

**成本管理类（5个）：**

6. **app/skills/cost_mgmt/estimate_cost.py** - 成本估算
   ```python
   @SkillRegistry.register
   class EstimateCostSkill(BaseSkill):
       NAME = "成本估算"
       CODE = "estimate_cost"
       DESCRIPTION = "基于人力、采购、运维等维度估算项目成本"
       
       async def execute(self, params, context):
           # 1. 人力成本估算
           labor_cost = await self._estimate_labor_cost(
               params.get("team_composition"),
               params.get("duration_months")
           )
           
           # 2. 采购成本估算
           procurement_cost = await self._estimate_procurement_cost(
               params.get("procurement_items", [])
           )
           
           # 3. 运维成本估算
           maintenance_cost = await self._estimate_maintenance_cost(
               params.get("maintenance_scope")
           )
           
           # 4. 应急储备（通常10%-15%）
           contingency = (labor_cost + procurement_cost + maintenance_cost) * 0.1
           
           # 5. 管理储备（通常5%）
           management_reserve = (labor_cost + procurement_cost + maintenance_cost) * 0.05
           
           total = labor_cost + procurement_cost + maintenance_cost + contingency + management_reserve
           
           # 6. 保存估算
           estimate = await self.services.cost_service.save_estimate({
               "project_id": context.project_id,
               "labor_cost": labor_cost,
               "procurement_cost": procurement_cost,
               "maintenance_cost": maintenance_cost,
               "contingency": contingency,
               "management_reserve": management_reserve,
               "total": total,
               "breakdown": {...},
               "assumptions": params.get("assumptions", []),
               "created_by": context.user_id
           })
           
           # 7. 生成成本估算报告
           # ... 
           
           return SkillResult(
               status="success",
               data={
                   "estimate_id": estimate.id,
                   "total": total,
                   "breakdown": {...},
                   "report_file_token": "..."
               }
           )
   ```

7. **app/skills/cost_mgmt/calculate_actual_cost.py** - 成本核算
   - 对接财务系统
   - 归集实际成本
   - 按WBS分配

8. **app/skills/cost_mgmt/monitor_cost.py** - 成本监控
   - 实时监控
   - 偏差分析
   - 超支预警
   - 自动触发审批流程

9. **app/skills/cost_mgmt/calculate_evm.py** - EVM指标计算
   - PV/EV/AC计算
   - CPI/SPI计算
   - EAC/ETC预测
   - VAC计算

10. **app/skills/cost_mgmt/cost_forecast.py** - 成本预测
    - 基于EVM的预测
    - 多种预测模型
    - 趋势分析

**风险管理类（5个）：**

11. **app/skills/risk_mgmt/identify_risks.py** - AI风险识别
    ```python
    @SkillRegistry.register
    class IdentifyRisksSkill(BaseSkill):
        NAME = "风险识别"
        CODE = "identify_risks"
        DESCRIPTION = "AI智能识别项目潜在风险"
        
        async def execute(self, params, context):
            # 1. 收集项目数据
            project_data = await self._gather_project_data(context.project_id)
            
            # 2. AI风险分析（基于LLM）
            ai_risks = await self._ai_analyze_risks(project_data)
            
            # 3. 规则风险识别
            rule_risks = await self._rule_based_risks(project_data)
            
            # 4. 历史相似项目风险参考
            historical_risks = await self._historical_risks_reference(
                context.project_id, project_data
            )
            
            # 5. 风险合并、去重、排序
            all_risks = self._merge_risks(ai_risks, rule_risks, historical_risks)
            
            # 6. 保存风险登记册
            for risk in all_risks:
                await self.services.risk_service.save_risk({
                    "project_id": context.project_id,
                    **risk
                })
            
            return SkillResult(...)
    ```

12. **app/skills/risk_mgmt/assess_risks.py** - 风险评估
    - 概率×影响打分
    - 风险矩阵生成
    - 风险等级划分

13. **app/skills/risk_mgmt/plan_risk_response.py** - 风险应对计划
    - 应对策略推荐（避免/转移/减轻/接受）
    - 应对措施生成

14. **app/skills/risk_mgmt/monitor_risks.py** - 风险监控
    - 触发条件检测
    - 实时预警
    - 状态追踪

15. **app/skills/risk_mgmt/risk_matrix_visualization.py** - 风险矩阵可视化
    - 5×5风险矩阵
    - 热力图展示

【交付物】
生成上述15个Skills的完整代码实现。
重点保证：
1. 业务逻辑的准确性（特别是EVM等专业计算）
2. 与外部系统的对接（财务、缺陷系统）
3. 可视化输出的美观（图表、矩阵）
```

---

## 提示词 4.4：合规、审批、知识答疑类Skills开发

```
开发流程合规、审批管理和知识服务相关的Skills。

【任务要求】

**合规审核类（4个）：**

1. **app/skills/integration_mgmt/audit_pre_initiation.py** - 预立项审核
2. **app/skills/integration_mgmt/audit_initiation.py** - 立项审核
3. **app/skills/integration_mgmt/audit_change_request.py** - 变更审核
4. **app/skills/integration_mgmt/audit_closure.py** - 结项审核

每个审核Skill的通用结构：
```python
@SkillRegistry.register
class AuditXXXSkill(BaseSkill):
    """XX审核"""
    
    AUDIT_RULES = [
        {
            "rule_code": "MATERIAL_COMPLETE",
            "rule_name": "材料完整性",
            "description": "必需材料是否齐全",
            "weight": 0.3,
            "checker": "check_material_complete"
        },
        {
            "rule_code": "CONTENT_COMPLIANCE",
            "rule_name": "内容合规性",
            "description": "内容是否符合规范",
            "weight": 0.4,
            "checker": "check_content_compliance"
        },
        {
            "rule_code": "FINANCIAL_RISK",
            "rule_name": "财务风险",
            "description": "预算合理性",
            "weight": 0.3,
            "checker": "check_financial_risk"
        }
    ]
    
    async def execute(self, params, context):
        document_id = params["document_id"]
        document = await self.services.document_service.get(document_id)
        
        # 执行所有审核规则
        audit_results = []
        for rule in self.AUDIT_RULES:
            checker = getattr(self, rule["checker"])
            result = await checker(document, context)
            audit_results.append({
                "rule_code": rule["rule_code"],
                "rule_name": rule["rule_name"],
                "passed": result.passed,
                "score": result.score,
                "issues": result.issues,
                "weight": rule["weight"]
            })
        
        # 计算总分
        total_score = sum(r["score"] * r["weight"] for r in audit_results)
        passed = total_score >= 0.7  # 70分及格
        
        # 风险等级
        risk_level = self._calculate_risk_level(total_score, audit_results)
        
        # 保存审核结果
        await self.services.audit_service.save_audit_result({
            "document_id": document_id,
            "audit_type": self.AUDIT_TYPE,
            "total_score": total_score,
            "passed": passed,
            "risk_level": risk_level,
            "details": audit_results,
            "auditor": context.user_id
        })
        
        # 生成审核报告
        report = await self._generate_audit_report(audit_results, total_score)
        
        return SkillResult(
            status="success",
            data={
                "passed": passed,
                "score": total_score,
                "risk_level": risk_level,
                "issues": [issue for r in audit_results for issue in r["issues"]],
                "report_file_token": report.file_token
            }
        )
```

**审批流程类（3个）：**

5. **app/skills/integration_mgmt/submit_approval.py** - 提交审批
   - 创建飞书审批实例
   - 通知审批人
   - 跟踪审批状态

6. **app/skills/integration_mgmt/track_approval.py** - 审批跟踪
   - 查询当前审批状态
   - 提醒未审批人

7. **app/skills/integration_mgmt/handle_approval_callback.py** - 审批回调处理
   - 审批通过后的后续动作
   - 审批拒绝的处理

**知识答疑类（3个）：**

8. **app/skills/support/qa_project_regulation.py** - 项目制度规范答疑
   ```python
   @SkillRegistry.register
   class QARegulationSkill(BaseSkill):
       """项目制度规范答疑（基于RAG）"""
       
       NAME = "制度规范答疑"
       CODE = "qa_project_regulation"
       
       PERMISSION_REQUIREMENTS = {
           "project_manager": True, "pm": True,
           "tech_lead": True, "member": True, "viewer": True
       }
       
       async def execute(self, params, context):
           question = params["question"]
           
           # 调用RAG引擎
           rag_response = await self.services.rag_engine.query(
               question=question,
               collection="pm_regulations",
               top_k=5
           )
           
           if rag_response.confidence < 0.6:
               return SkillResult(
                   status="success",
                   data={
                       "answer": "抱歉，我没有找到相关的制度规范信息，建议您：\n"
                                 "1. 重新表述问题\n"
                                 "2. 联系项目管理部咨询",
                       "sources": []
                   }
               )
           
           return SkillResult(
               status="success",
               data={
                   "answer": rag_response.answer,
                   "sources": [
                       {
                           "title": doc.metadata.get("title"),
                           "section": doc.metadata.get("section"),
                           "url": doc.metadata.get("url")
                       } for doc in rag_response.sources
                   ],
                   "confidence": rag_response.confidence
               }
           )
   ```

9. **app/skills/support/qa_project_status.py** - 项目情况咨询
10. **app/skills/support/general_help.py** - 通用帮助

**资源、采购、干系人管理类（5个）：**

11. **app/skills/resource_mgmt/timesheet_statistics.py** - 工时统计
12. **app/skills/resource_mgmt/member_onboarding.py** - 成员入场
13. **app/skills/resource_mgmt/member_offboarding.py** - 成员离场
14. **app/skills/procurement_mgmt/track_contract_payment.py** - 合同回款跟进
15. **app/skills/stakeholder_mgmt/identify_stakeholders.py** - 干系人识别

【交付物】
生成上述15个Skills的完整代码实现。
重点关注审核规则的可配置化和RAG的准确性。

完成后，整个Skills矩阵应包含约45个Skills，覆盖PMBOK十大领域。
请最后给出完整的Skills清单（按分类）。
```

---

#  Part 5：数据维护通道、测试与部署

> **目标**：完成多通道数据维护、全面测试、监控告警、CI/CD部署
>
> **预计耗时**：5-7天

---

## 提示词 5.1：OA系统对接与数据同步

```
实现PM机器人与OA/PMO系统的深度对接。

【任务要求】

1. **app/integrations/oa/__init__.py** - OA集成模块

2. **app/integrations/oa/client.py** - OA客户端封装
   ```python
   class OASystemClient:
       """OA系统API客户端"""
       
       def __init__(self, base_url, api_key, timeout=30):
           self.base_url = base_url
           self.api_key = api_key
           self.client = httpx.AsyncClient(
               base_url=base_url,
               timeout=timeout,
               headers={"Authorization": f"Bearer {api_key}"}
           )
       
       async def get_project(self, project_code):
           """获取项目信息"""
           response = await self.client.get(f"/api/v1/projects/{project_code}")
           return self._parse_response(response)
       
       async def list_projects(self, filters=None, page=1, size=50):
           """查询项目列表"""
           pass
       
       async def get_project_members(self, project_code):
           """获取项目成员"""
           pass
       
       async def get_project_budget(self, project_code):
           """获取项目预算"""
           pass
       
       async def get_actual_cost(self, project_code, start_date, end_date):
           """从财务系统获取实际成本"""
           pass
       
       async def get_timesheet(self, project_code, start_date, end_date):
           """从报工系统获取工时数据"""
           pass
       
       async def get_change_requests(self, project_code):
           """获取变更申请"""
           pass
       
       async def get_contracts(self, project_code):
           """获取合同信息"""
           pass
   ```

3. **app/services/oa_sync_service.py** - OA同步服务
   ```python
   class OASyncService:
       """OA数据同步服务"""
       
       async def sync_project(self, project_code, db, redis):
           """同步单个项目的完整数据"""
           # 1. 获取项目基本信息
           oa_project = await self.oa_client.get_project(project_code)
           
           # 2. 转换数据格式
           project_data = self._transform_project(oa_project)
           
           # 3. 写入数据库（upsert）
           await self.project_service.upsert_project(project_data, db)
           
           # 4. 同步成员
           members = await self.oa_client.get_project_members(project_code)
           await self._sync_members(project_code, members, db)
           
           # 5. 同步预算
           budget = await self.oa_client.get_project_budget(project_code)
           await self._sync_budget(project_code, budget, db)
           
           # 6. 记录同步状态
           await self._record_sync_status(
               source="OA",
               project_id=project_code,
               status="success"
           )
           
           # 7. 清除相关缓存
           await self._invalidate_caches(project_code, redis)
       
       async def sync_all_active_projects(self, db, redis):
           """同步所有活跃项目"""
           project_codes = await self._get_active_project_codes()
           
           # 并发同步（控制并发数）
           semaphore = asyncio.Semaphore(5)
           tasks = [
               self._sync_with_semaphore(semaphore, code, db, redis)
               for code in project_codes
           ]
           await asyncio.gather(*tasks, return_exceptions=True)
       
       async def sync_financial_data(self, project_id, db):
           """同步财务数据"""
           pass
       
       async def sync_timesheet_data(self, project_id, db):
           """同步报工数据"""
           pass
   ```

4. **app/api/v1/oa_webhook.py** - OA Webhook接收
   ```python
   @router.post("/webhook")
   async def receive_oa_webhook(
       request: Request,
       db: AsyncSession = Depends(get_db),
       redis: RedisClient = Depends(get_redis)
   ):
       """接收OA系统的事件回调"""
       # 1. 验签
       # 2. 解析事件
       event = await request.json()
       event_type = event.get("event_type")
       
       # 3. 分发处理
       handlers = {
           "project_approved": handle_project_approved,
           "project_changed": handle_project_changed,
           "contract_signed": handle_contract_signed,
           "budget_adjusted": handle_budget_adjusted,
           "member_added": handle_member_added,
           "member_removed": handle_member_removed,
       }
       handler = handlers.get(event_type)
       if handler:
           await handler(event, db, redis)
       
       return {"code": 0}
   ```

5. **app/tasks/scheduled_tasks.py** - 定时同步任务（Celery Beat）
   ```python
   from app.tasks.celery_app import celery_app
   
   @celery_app.task
   def sync_oa_data_daily():
       """每日凌晨2点同步OA数据"""
       async def _run():
           async with get_db_context() as db:
               redis = await get_redis()
               await oa_sync_service.sync_all_active_projects(db, redis)
       asyncio.run(_run())
   
   @celery_app.task
   def sync_financial_data_hourly():
       """每小时同步财务数据"""
       pass
   
   @celery_app.task
   def sync_timesheet_daily():
       """每日同步工时数据"""
       pass
   
   @celery_app.task
   def cleanup_expired_cache():
       """清理过期缓存"""
       pass
   
   @celery_app.task
   def generate_daily_metrics():
       """生成每日指标"""
       pass
   
   # Beat调度配置
   celery_app.conf.beat_schedule = {
       'sync-oa-daily': {
           'task': 'app.tasks.scheduled_tasks.sync_oa_data_daily',
           'schedule': crontab(hour=2, minute=0),
       },
       'sync-financial-hourly': {
           'task': 'app.tasks.scheduled_tasks.sync_financial_data_hourly',
           'schedule': crontab(minute=0),
       },
       'sync-timesheet-daily': {
           'task': 'app.tasks.scheduled_tasks.sync_timesheet_daily',
           'schedule': crontab(hour=1, minute=30),
       },
       'cleanup-cache': {
           'task': 'app.tasks.scheduled_tasks.cleanup_expired_cache',
           'schedule': crontab(hour='*/6'),
       },
   }
   ```

【交付物】
生成上述所有OA对接相关代码。
```

---

## 提示词 5.2：飞书多维表格双向同步与对话式数据维护

```
实现PM机器人最具创新性的功能 - 多通道数据维护。

【任务要求】

1. **app/services/bitable_sync_service.py** - 多维表格同步服务
   ```python
   class BitableSyncService:
       """飞书多维表格双向同步服务"""
       
       PROJECT_TABLES = {
           "tasks": {
               "name": "任务清单",
               "fields": [
                   {"field_name": "任务名称", "type": 1},  # 文本
                   {"field_name": "负责人", "type": 11},  # 人员
                   {"field_name": "状态", "type": 3, "property": {  # 单选
                       "options": [
                           {"name": "待开始", "color": 0},
                           {"name": "进行中", "color": 1},
                           {"name": "已完成", "color": 2},
                           {"name": "阻塞", "color": 3}
                       ]
                   }},
                   {"field_name": "开始日期", "type": 5},  # 日期
                   {"field_name": "结束日期", "type": 5},
                   {"field_name": "进度", "type": 2},  # 数字
                   {"field_name": "优先级", "type": 3, "property": {...}},
                   {"field_name": "备注", "type": 1}
               ]
           },
           "risks": {
               "name": "风险登记册",
               "fields": [...]
           },
           "milestones": {
               "name": "里程碑",
               "fields": [...]
           },
           "timesheet": {
               "name": "工时台账",
               "fields": [...]
           },
           "changes": {
               "name": "变更记录",
               "fields": [...]
           },
           "defects": {
               "name": "缺陷台账",
               "fields": [...]
           }
       }
       
       async def create_project_workspace(
           self, project_id: str, project_name: str, db, redis
       ):
           """为项目创建配套的多维表格工作区"""
           
           # 1. 创建多维表格应用
           app_token = await self.lark_bitable.create_app(
               name=f"PM-{project_name}-数据中心",
               folder_token=settings.LARK.PM_FOLDER_TOKEN
           )
           
           # 2. 创建所有数据表
           table_mappings = {}
           for table_key, table_def in self.PROJECT_TABLES.items():
               table_id = await self.lark_bitable.create_table(
                   app_token=app_token,
                   table_name=table_def["name"],
                   fields=table_def["fields"]
               )
               table_mappings[table_key] = table_id
           
           # 3. 保存绑定关系
           await self.bitable_binding_repo.create({
               "project_id": project_id,
               "app_token": app_token,
               "table_mappings": table_mappings
           }, db)
           
           # 4. 初始同步现有数据
           await self.sync_db_to_bitable(project_id, db)
           
           # 5. 订阅表格变更事件
           for table_id in table_mappings.values():
               await self.lark_bitable.subscribe_table_events(
                   app_token, table_id
               )
           
           return {
               "app_token": app_token,
               "url": f"https://lark../base/{app_token}",
               "tables": table_mappings
           }
       
       async def sync_db_to_bitable(self, project_id: str, db):
           """数据库 → 多维表格（初始同步）"""
           binding = await self.bitable_binding_repo.get_by_project(
               project_id, db
           )
           
           # 同步任务
           tasks = await self.task_service.get_project_tasks(project_id, db)
           records = [self._task_to_bitable_record(t) for t in tasks]
           await self.lark_bitable.add_records(
               binding.app_token,
               binding.table_mappings["tasks"],
               records
           )
           
           # 同步其他表...
       
       async def handle_bitable_change(
           self, app_token: str, table_id: str, record_id: str,
           action: str  # create/update/delete
       ):
           """处理多维表格的变更事件（表格 → 数据库）"""
           # 1. 获取项目绑定
           binding = await self.bitable_binding_repo.get_by_app_token(
               app_token
           )
           project_id = binding.project_id
           
           # 2. 识别表类型
           table_type = self._identify_table_type(
               binding.table_mappings, table_id
           )
           
           # 3. 获取记录数据
           if action != "delete":
               record = await self.lark_bitable.get_record(
                   app_token, table_id, record_id
               )
           
           # 4. 同步到数据库
           if table_type == "tasks":
               await self._sync_task_to_db(project_id, record, action)
           elif table_type == "risks":
               await self._sync_risk_to_db(project_id, record, action)
           # ...
           
           # 5. 记录审计
           await self.audit_service.log_action(
               action=f"bitable_{action}",
               object_type=table_type,
               object_id=record_id,
               channel="bitable"
           )
   ```

2. **app/services/conversational_data_service.py** - 对话式数据维护
   ```python
   class ConversationalDataService:
       """对话式数据维护服务"""
       
       async def handle_data_update_request(
           self, user_input: str, context: UserContext,
           user_id: str, project_id: str
       ) -> Dict:
           """处理对话式数据更新请求"""
           
           # 1. 识别更新意图（更新什么数据）
           update_intent = await self._recognize_update_intent(
               user_input, context, project_id
           )
           
           if update_intent.target == "task":
               return await self._handle_task_update(
                   update_intent, context, user_id, project_id
               )
           elif update_intent.target == "risk":
               return await self._handle_risk_update(...)
           # ...
       
       async def _handle_task_update(
           self, intent, context, user_id, project_id
       ):
           """处理任务更新"""
           
           # 如果未指定具体任务，列出所有任务让用户选择
           if not intent.task_identifier:
               tasks = await self.task_service.get_active_tasks(project_id)
               return {
                   "type": "task_selection",
                   "tasks": tasks,
                   "next_action": "请选择要更新的任务"
               }
           
           # 模糊匹配任务
           task = await self.task_service.find_task_by_identifier(
               project_id, intent.task_identifier
           )
           
           if not task:
               return {
                   "type": "error",
                   "message": f"未找到任务'{intent.task_identifier}'"
               }
           
           # 解析更新内容
           update_data = intent.update_data
           
           # 业务规则校验
           validation = await self._validate_task_update(task, update_data)
           if not validation.valid:
               return {
                   "type": "error",
                   "message": validation.error_msg
               }
           
           # 构建确认卡片
           return {
               "type": "confirmation",
               "summary": {
                   "operation": "更新任务",
                   "task_name": task.name,
                   "changes": [
                       {
                           "field": k,
                           "old_value": getattr(task, k),
                           "new_value": v
                       } for k, v in update_data.items()
                   ]
               },
               "confirmation_callback": {
                   "action": "confirm_task_update",
                   "task_id": task.id,
                   "update_data": update_data
               }
           }
       
       async def execute_confirmed_update(
           self, callback_data: Dict, user_id: str, db, redis
       ):
           """执行已确认的更新"""
           # 实际写入数据库
           # 触发后续动作（如同步到Bitable、通知项目组）
           pass
   ```

3. **app/services/file_import_service.py** - 文件导入服务
   ```python
   class FileImportService:
       """Excel/CSV文件导入服务"""
       
       SUPPORTED_TEMPLATES = {
           "project_plan": ProjectPlanImporter,
           "wbs": WBSImporter,
           "team_members": TeamMembersImporter,
           "risk_register": RiskRegisterImporter,
           "timesheet": TimesheetImporter
       }
       
       async def import_from_file(
           self, file_bytes: bytes, file_name: str,
           project_id: str, user_id: str, db
       ) -> Dict:
           """从文件导入数据"""
           
           # 1. 识别文件类型
           file_type = self._detect_file_type(file_name)
           
           # 2. 解析文件
           if file_type in ["xlsx", "xls"]:
               data = self._parse_excel(file_bytes)
           elif file_type == "csv":
               data = self._parse_csv(file_bytes)
           
           # 3. AI辅助识别模板
           template_type, confidence = await self._identify_template(data)
           
           if confidence < 0.7:
               return {
                   "status": "needs_clarification",
                   "message": "无法确定文件类型，请选择",
                   "options": list(self.SUPPORTED_TEMPLATES.keys())
               }
           
           # 4. 字段映射（AI辅助）
           field_mapping = await self._auto_map_fields(
               data.columns, template_type
           )
           
           # 5. 数据校验
           importer = self.SUPPORTED_TEMPLATES[template_type]()
           validation = await importer.validate(data, field_mapping)
           
           # 6. 返回预览（让用户确认）
           return {
               "status": "preview",
               "template_type": template_type,
               "field_mapping": field_mapping,
               "total_rows": len(data),
               "valid_rows": validation.valid_count,
               "invalid_rows": validation.invalid_count,
               "warnings": validation.warnings,
               "preview_data": data.head(5).to_dict(),
               "confirmation_callback": {
                   "action": "confirm_import",
                   "data_id": await self._cache_import_data(data, field_mapping)
               }
           }
       
       async def execute_import(
           self, data_id: str, user_id: str, project_id: str, db
       ):
           """执行导入"""
           # 从缓存取数据
           # 批量写入数据库
           # 同步到Bitable
           pass
   ```

4. **app/skills/integration_mgmt/update_project_data.py** - 数据更新Skill
   作为对话式数据维护的统一入口Skill。

5. **app/skills/integration_mgmt/import_project_data.py** - 数据导入Skill

【交付物】
生成上述所有数据维护相关代码，确保多通道数据流转的可靠性和一致性。
```

---

## 提示词 5.3：监控、告警与审计

```
实现完善的监控、告警和审计系统。

【任务要求】

1. **app/core/middleware/metrics_middleware.py** - 指标中间件
   ```python
   from prometheus_client import Counter, Histogram, Gauge
   
   # 定义指标
   request_counter = Counter(
       'pm_robot_requests_total',
       'Total requests',
       ['method', 'endpoint', 'status']
   )
   
   request_duration = Histogram(
       'pm_robot_request_duration_seconds',
       'Request duration',
       ['method', 'endpoint']
   )
   
   active_users = Gauge(
       'pm_robot_active_users',
       'Currently active users'
   )
   
   skill_execution_counter = Counter(
       'pm_robot_skill_executions_total',
       'Skill executions',
       ['skill_code', 'status']
   )
   
   skill_execution_duration = Histogram(
       'pm_robot_skill_duration_seconds',
       'Skill execution duration',
       ['skill_code']
   )
   
   class MetricsMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request, call_next):
           start_time = time.time()
           response = await call_next(request)
           duration = time.time() - start_time
           
           request_counter.labels(
               method=request.method,
               endpoint=request.url.path,
               status=response.status_code
           ).inc()
           
           request_duration.labels(
               method=request.method,
               endpoint=request.url.path
           ).observe(duration)
           
           return response
   ```

2. **app/api/v1/metrics.py** - Metrics端点
   ```python
   @router.get("/metrics")
   async def metrics():
       """Prometheus指标端点"""
       return Response(
           content=generate_latest(),
           media_type=CONTENT_TYPE_LATEST
       )
   ```

3. **app/services/monitoring_service.py** - 监控服务
   ```python
   class MonitoringService:
       """业务监控服务"""
       
       async def collect_business_metrics(self, db, redis):
           """采集业务指标"""
           metrics = {
               "active_projects": await self._count_active_projects(db),
               "active_users_today": await self._count_active_users_today(redis),
               "skill_executions_today": await self._count_skill_executions(redis),
               "skill_success_rate": await self._calculate_success_rate(redis),
               "avg_response_time": await self._calculate_avg_response_time(redis),
               "data_sync_status": await self._check_data_sync_status(db),
           }
           return metrics
       
       async def health_check(self, db, redis):
           """健康检查"""
           checks = {
               "database": await self._check_database(db),
               "redis": await self._check_redis(redis),
               "lark_api": await self._check_lark_api(),
               "llm": await self._check_llm(),
               "openclaw": await self._check_openclaw(),
               "oa_system": await self._check_oa_system(),
           }
           overall = all(c["status"] == "healthy" for c in checks.values())
           return {
               "status": "healthy" if overall else "unhealthy",
               "checks": checks,
               "timestamp": datetime.now().isoformat()
           }
   ```

4. **app/services/alerting_service.py** - 告警服务
   ```python
   class AlertingService:
       """告警服务"""
       
       ALERT_RULES = [
           {
               "name": "skill_failure_rate_high",
               "description": "Skill失败率过高",
               "metric": "skill_failure_rate",
               "threshold": 0.1,  # 10%
               "duration": 300,  # 持续5分钟
               "severity": "warning",
               "notification_channels": ["lark_admin_group"]
           },
           {
               "name": "api_response_slow",
               "description": "API响应过慢",
               "metric": "p99_response_time",
               "threshold": 5000,  # 5秒
               "duration": 180,
               "severity": "warning",
           },
           {
               "name": "database_connection_lost",
               "description": "数据库连接丢失",
               "metric": "db_health",
               "threshold": False,
               "duration": 30,
               "severity": "critical",
           },
           # ... 更多规则
       ]
       
       async def check_and_alert(self):
           """检查告警规则并发送通知"""
           for rule in self.ALERT_RULES:
               triggered = await self._check_rule(rule)
               if triggered:
                   await self._send_alert(rule, triggered)
       
       async def _send_alert(self, rule, alert_data):
           """发送告警通知"""
           for channel in rule["notification_channels"]:
               if channel == "lark_admin_group":
                   await self.lark_message.send_card(
                       chat_id=settings.ADMIN_CHAT_ID,
                       card=self._build_alert_card(rule, alert_data)
                   )
               elif channel == "email":
                   await self.email_service.send_alert(...)
               elif channel == "sms":
                   await self.sms_service.send_alert(...)
   ```

5. **app/core/middleware/audit_middleware.py** - 审计中间件
   ```python
   class AuditMiddleware(BaseHTTPMiddleware):
       """请求审计中间件"""
       
       async def dispatch(self, request, call_next):
           # 记录请求开始
           request_id = str(uuid.uuid4())
           request.state.request_id = request_id
           
           # 提取上下文
           user_id = request.headers.get("X-Lark-User-Id")
           
           # 调用下游
           response = await call_next(request)
           
           # 异步记录审计日志
           if self._should_audit(request):
               asyncio.create_task(self._log_audit(
                   request_id=request_id,
                   user_id=user_id,
                   method=request.method,
                   path=request.url.path,
                   status=response.status_code,
                   ip=request.client.host
               ))
           
           response.headers["X-Request-ID"] = request_id
           return response
   ```

6. **docker/grafana/dashboards/** - Grafana仪表板配置
   提供以下仪表板的JSON配置：
   - PM机器人总览仪表板
   - API性能监控
   - Skill执行监控
   - 业务指标监控
   - 系统资源监控

7. **docker/prometheus/prometheus.yml** - Prometheus配置

【交付物】
生成上述所有监控告警相关代码和配置文件。
```

---

## 提示词 5.4：完整测试体系

```
建立PM机器人的完整测试体系，确保代码质量和系统稳定性。

【任务要求】

1. **tests/conftest.py** - 全局fixtures
   ```python
   import pytest
   import pytest_asyncio
   from httpx import AsyncClient
   
   @pytest_asyncio.fixture
   async def test_db():
       """测试数据库（使用内存SQLite或独立测试库）"""
       # 创建测试库
       # 运行迁移
       # yield session
       # 清理
       pass
   
   @pytest_asyncio.fixture
   async def test_redis():
       """测试Redis（使用fakeredis）"""
       pass
   
   @pytest_asyncio.fixture
   async def test_client(test_db, test_redis):
       """FastAPI测试客户端"""
       async with AsyncClient(app=app, base_url="http://test") as client:
           yield client
   
   @pytest.fixture
   def mock_lark_client(mocker):
       """模拟飞书客户端"""
       pass
   
   @pytest.fixture
   def mock_llm_client(mocker):
       """模拟LLM客户端"""
       pass
   
   @pytest_asyncio.fixture
   async def sample_project(test_db):
       """示例项目数据"""
       pass
   
   @pytest_asyncio.fixture
   async def sample_user_with_role(test_db, sample_project):
       """带角色的示例用户"""
       pass
   ```

2. **tests/unit/** - 单元测试
   
   覆盖所有核心模块：
   - test_config.py
   - test_logger.py
   - test_security.py
   - test_exceptions.py
   - test_permission_service.py（重点）
   - test_isolation_service.py（重点）
   - test_intent_recognizer.py
   - test_skill_registry.py
   - test_skill_executor.py
   - test_orchestrator.py
   - 每个Skill都要有对应单元测试

3. **tests/integration/** - 集成测试
   - test_lark_webhook_integration.py
   - test_database_integration.py
   - test_redis_integration.py
   - test_oa_integration.py
   - test_bitable_integration.py
   - test_llm_integration.py

4. **tests/e2e/** - 端到端测试
   ```python
   # tests/e2e/test_complete_flow.py
   async def test_complete_user_flow(test_client, sample_project, sample_user_with_role):
       """测试完整的用户使用流程"""
       
       # 1. 模拟飞书发送消息
       response = await test_client.post(
           "/api/v1/lark/event",
           json=build_lark_message_event(
               user_id=sample_user_with_role.lark_user_id,
               chat_id="test_chat_id",
               text="查询项目当前情况"
           )
       )
       assert response.status_code == 200
       
       # 2. 等待异步处理完成
       await asyncio.sleep(2)
       
       # 3. 验证响应消息已发送（通过mock_lark_client）
       # ...
   
   async def test_project_isolation(test_client, two_users_in_different_projects):
       """关键测试：项目隔离"""
       user_a, project_a = two_users_in_different_projects[0]
       user_b, project_b = two_users_in_different_projects[1]
       
       # user_a 尝试查询 project_b 的数据
       response = await test_client.post(
           "/api/v1/lark/event",
           json=build_lark_message_event(
               user_id=user_a.lark_user_id,
               chat_id=project_b.chat_id,  # 故意用其他项目的群
               text="查询项目情况"
           )
       )
       
       # 应该被拒绝
       # 验证审计日志记录了违规尝试
   ```

5. **tests/performance/** - 性能测试
   ```python
   # tests/performance/test_load.py (使用locust)
   from locust import HttpUser, task, between
   
   class PMRobotUser(HttpUser):
       wait_time = between(1, 5)
       
       @task(3)
       def query_project_overview(self):
           self.client.post("/api/v1/lark/event", json=...)
       
       @task(1)
       def generate_weekly_report(self):
           self.client.post("/api/v1/lark/event", json=...)
   ```

6. **tests/security/** - 安全测试
   - test_signature_verification.py
   - test_sql_injection.py
   - test_xss_prevention.py
   - test_unauthorized_access.py
   - test_data_leakage.py

7. **pyproject.toml 测试配置补充**：
   ```toml
   [tool.pytest.ini_options]
   asyncio_mode = "auto"
   testpaths = ["tests"]
   python_files = ["test_*.py"]
   python_classes = ["Test*"]
   python_functions = ["test_*"]
   markers = [
       "unit: 单元测试",
       "integration: 集成测试",
       "e2e: 端到端测试",
       "performance: 性能测试",
       "security: 安全测试",
       "slow: 慢测试"
   ]
   addopts = [
       "--strict-markers",
       "--cov=app",
       "--cov-report=term-missing",
       "--cov-report=html",
       "--cov-fail-under=80"
   ]
   ```

8. **tests/factories/** - 测试数据工厂（基于factory_boy）
   ```python
   import factory
   from app.models import Project, User, Task
   
   class ProjectFactory(factory.Factory):
       class Meta:
           model = Project
       
       id = factory.Sequence(lambda n: f"PRJ-{n:04d}")
       name = factory.Faker("sentence", nb_words=3)
       status = "executing"
       budget_total = factory.Faker("pyfloat", min_value=100000, max_value=10000000)
   ```

【验收标准】
- 单元测试覆盖率 ≥ 80%
- 所有关键业务流程有E2E测试
- 项目隔离相关测试100%覆盖
- 所有Skill都有对应测试
- CI流水线集成所有测试

【交付物】
生成上述所有测试文件，并提供运行测试的完整命令文档。
```

---

## 提示词 5.5：CI/CD与生产部署

```
最后一步，建立完整的CI/CD流水线和生产部署方案。

【任务要求】

1. **.github/workflows/ci.yml** - GitHub Actions CI配置
   ```yaml
   name: CI Pipeline
   
   on:
     push:
       branches: [main, develop]
     pull_request:
       branches: [main, develop]
   
   jobs:
     lint:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.11'
         - name: Install dependencies
           run: |
             pip install poetry
             poetry install
         - name: Run linters
           run: |
             poetry run black --check .
             poetry run isort --check .
             poetry run flake8 .
             poetry run mypy app/
     
     test:
       runs-on: ubuntu-latest
       services:
         postgres:
           image: postgres:15
           env:
             POSTGRES_PASSWORD: test
           options: >-
             --health-cmd pg_isready
             --health-interval 10s
         redis:
           image: redis:7
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
         - name: Install dependencies
         - name: Run migrations
         - name: Run tests
           run: poetry run pytest --cov --cov-report=xml
         - name: Upload coverage
           uses: codecov/codecov-action@v4
     
     security_scan:
       runs-on: ubuntu-latest
       steps:
         - name: Run Bandit
           run: bandit -r app/
         - name: Run Safety
           run: safety check
         - name: Run Trivy
           uses: aquasecurity/trivy-action@master
     
     build_image:
       needs: [lint, test, security_scan]
       runs-on: ubuntu-latest
       if: github.ref == 'refs/heads/main'
       steps:
         - name: Build Docker image
         - name: Push to registry
   ```

2. **.github/workflows/cd.yml** - CD配置
   ```yaml
   name: Deploy
   on:
     workflow_run:
       workflows: ["CI Pipeline"]
       branches: [main]
       types: [completed]
   
   jobs:
     deploy_staging:
       runs-on: ubuntu-latest
       environment: staging
       steps:
         - name: Deploy to Staging K8s
         - name: Run smoke tests
     
     deploy_production:
       needs: deploy_staging
       runs-on: ubuntu-latest
       environment: production
       steps:
         - name: Manual approval required
         - name: Blue-Green Deployment
   ```

3. **k8s/** - Kubernetes部署配置
   
   **k8s/namespace.yaml**:
   ```yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: pm-robot
   ```
   
   **k8s/configmap.yaml** - 配置
   **k8s/secret.yaml** - 密钥（使用sealed-secrets）
   **k8s/deployment.yaml** - 应用部署
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: pm-robot-api
     namespace: pm-robot
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: pm-robot-api
     template:
       spec:
         containers:
         - name: api
           image: registry.xxx.com/pm-robot:latest
           ports:
           - containerPort: 8000
           resources:
             requests:
               cpu: 500m
               memory: 1Gi
             limits:
               cpu: 2000m
               memory: 4Gi
           livenessProbe:
             httpGet:
               path: /health/live
               port: 8000
             initialDelaySeconds: 30
             periodSeconds: 10
           readinessProbe:
             httpGet:
               path: /health/ready
               port: 8000
             initialDelaySeconds: 10
             periodSeconds: 5
           env:
           - name: ENVIRONMENT
             value: "production"
           envFrom:
           - configMapRef:
               name: pm-robot-config
           - secretRef:
               name: pm-robot-secrets
   ```
   
   **k8s/service.yaml** - 服务暴露
   **k8s/ingress.yaml** - 入口
   **k8s/hpa.yaml** - 水平扩缩容
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: pm-robot-api
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: pm-robot-api
     minReplicas: 3
     maxReplicas: 20
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
     - type: Resource
       resource:
         name: memory
         target:
           type: Utilization
           averageUtilization: 80
   ```
   
   **k8s/worker-deployment.yaml** - Celery Worker部署
   **k8s/beat-deployment.yaml** - Celery Beat部署
   **k8s/postgres-statefulset.yaml** - PostgreSQL（生产建议用云数据库）
   **k8s/redis-statefulset.yaml** - Redis
   **k8s/network-policy.yaml** - 网络策略

4. **helm/pm-robot/** - Helm Chart（推荐方式）
   - Chart.yaml
   - values.yaml（开发/staging/生产环境的values）
   - templates/

5. **scripts/deploy.sh** - 部署脚本
   ```bash
   #!/bin/bash
   set -e
   
   ENVIRONMENT=${1:-staging}
   VERSION=${2:-latest}
   
   echo "Deploying PM Robot to $ENVIRONMENT (version: $VERSION)"
   
   # 1. 构建镜像
   docker build -t registry.xxx.com/pm-robot:$VERSION .
   
   # 2. 推送镜像
   docker push registry.xxx.com/pm-robot:$VERSION
   
   # 3. 更新K8s部署
   helm upgrade pm-robot ./helm/pm-robot \
     --namespace pm-robot \
     --values ./helm/pm-robot/values-$ENVIRONMENT.yaml \
     --set image.tag=$VERSION \
     --wait
   
   # 4. 运行数据库迁移
   kubectl exec -n pm-robot deploy/pm-robot-api -- alembic upgrade head
   
   # 5. 运行冒烟测试
   ./scripts/smoke_test.sh $ENVIRONMENT
   
   echo "Deployment complete!"
   ```

6. **scripts/smoke_test.sh** - 冒烟测试脚本

7. **scripts/rollback.sh** - 回滚脚本

8. **docs/deployment/README.md** - 完整的部署文档
   - 环境要求
   - 部署步骤（本地/Docker/K8s）
   - 配置说明
   - 故障排查
   - 备份恢复

9. **docs/operations/runbook.md** - 运维手册
   - 常见问题处理
   - 性能调优指南
   - 应急响应流程
   - 监控告警处理

10. **docs/api/openapi.yaml** - API文档（自动从FastAPI生成）

【最终交付物清单】
请按以下结构交付完整的项目：

```
pm-robot/
├── 应用代码（app/）
├── 测试（tests/）
├── 数据库迁移（alembic/）
├── 脚本（scripts/）
├── Docker配置（docker/）
├── K8s配置（k8s/）或 Helm Chart（helm/）
├── CI/CD配置（.github/）
├── 文档（docs/）
└── 完整的README和部署文档
```

请生成上述所有文件，并最后提供：
1. 完整的部署步骤清单
2. 验收测试清单
3. 上线检查清单
4. 培训材料大纲
```

---

##  Part 5 完成检查清单

- [ ] OA系统对接完成，可同步项目数据
- [ ] 飞书多维表格双向同步可工作
- [ ] 对话式数据维护功能完善
- [ ] 文件导入支持多种格式
- [ ] 监控指标完整采集
- [ ] 告警规则覆盖关键场景
- [ ] 测试覆盖率达到80%+
- [ ] CI/CD流水线可工作
- [ ] K8s部署配置完整
- [ ] 文档齐全（开发/部署/运维）

---

#  整体项目交付总结

##  完整交付物

| 阶段 | 主要交付物 | 关键指标 |
|------|----------|---------|
| **Part 1** | 项目脚手架、配置、数据库、Docker | 一键启动开发环境 |
| **Part 2** | 飞书集成、权限隔离 | 项目隔离100%安全 |
| **Part 3** | 编排引擎、Skill框架 | 意图识别准确率≥95% |
| **Part 4** | 45+业务Skills | 覆盖PMBOK十大领域 |
| **Part 5** | 数据维护、测试、部署 | 测试覆盖率≥80%，可生产部署 |

##  推荐执行顺序

1. **先完成Part 1**（1-2天），打好基础
2. **再做Part 2**（3-4天），跑通飞书集成主链路
3. **接着Part 3**（4-5天），构建编排引擎
4. **然后Part 4**（8-10天），分批开发Skills（可并行）
5. **最后Part 5**（5-7天），完善生产化能力

**总预计工期：21-28个工作日**（1个开发者全职），团队协作可压缩到 **2-3周**。

