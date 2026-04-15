# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PM Digital Employee is a **Lark (飞书)**-based project management intelligent assistant for a state-owned bank's technology subsidiary project management department. **Lark is the ONLY user interaction entrypoint.**

## Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python -m app.main

# Or with uvicorn (hot reload)
uvicorn app.main:app --reload --port 8000
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage (80% minimum required)
pytest --cov=app tests/

# Run specific test file
pytest tests/test_main.py -v

# Run specific test
pytest tests/test_orchestrator.py::test_process_message -v
```

### Code Quality
```bash
# Lint with ruff
ruff check app/ --config .ruff.toml

# Format with black
black app/ --line-length 100

# Type check with mypy
mypy app/ --config-file mypy.ini
```

### Docker Deployment
```bash
# Start full service stack
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Database
```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

## Architecture: 9-Layer Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 接入层        │ Lark Bot Webhook、Callback、File Upload      │
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
│ 7. Skill插件层   │ 13个核心Skill，BaseSkill规范，manifest      │
├─────────────────────────────────────────────────────────────────┤
│ 8. 集成适配层    │ 项目管理、财务、DevOps、OA、飞书适配器      │
├─────────────────────────────────────────────────────────────────┤
│ 9. 数据层        │ PostgreSQL、Redis、pgvector、Celery         │
└─────────────────────────────────────────────────────────────────┘
```

## Key Directories

- `app/api/` - FastAPI endpoints (Lark webhook/callback at `lark_webhook.py`, `lark_callback.py`)
- `app/orchestrator/` - Core orchestration: intent routing (`intent_router.py`), dialog state machine (`dialog_state.py`), skill registry (`skill_registry.py`)
- `app/skills/` - 13 Skill implementations inheriting from `BaseSkill`
- `app/integrations/lark/` - Lark integration: client, signature verification, message schemas
- `app/ai/` - LLM gateway, prompt management, output parsing, safety guard
- `app/rag/` - RAG pipeline: chunking, indexing, retrieval, reranking
- `app/domain/models/` - SQLAlchemy domain models (Project, Task, Milestone, Risk, Cost, etc.)

## Core Flow: Orchestrator

The `Orchestrator` (`app/orchestrator/orchestrator.py`) coordinates the complete message processing pipeline:

1. **Receive Lark message** → `process_lark_message()`
2. **Build user context** → `_build_user_context()` using `ContextService`
3. **Get/create dialog session** → `DialogStateMachine`
4. **Route based on dialog state**:
   - `PARAM_COLLECTING` → `_handle_param_collection()`
   - `CONFIRMATION_PENDING` → `_handle_confirmation()`
   - `EXECUTING` → (shouldn't receive new messages)
   - `IDLE` → `_handle_new_intent()`
5. **Intent recognition** → `IntentRouterV2.recognize_with_context()`
6. **Skill execution** → `_execute_skill()`

## Skill Development Pattern

Every Skill must:

1. Inherit from `BaseSkill` (`app/skills/base.py`)
2. Define class attributes: `skill_name`, `display_name`, `description`, `version`
3. Implement `async execute() -> SkillExecutionResult`
4. Define Manifest via `SkillManifestBuilder` (see `app/orchestrator/skill_manifest.py`)
5. Register in `app/skills/__init__.py` via `register_all_skills()`

Example structure:
```python
class MySkill(BaseSkill):
    skill_name = "my_skill"
    display_name = "功能名称"
    description = "功能描述..."
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        # Get params: self.get_param("param_name")
        # Access context: self.project_id, self.user_id, self.trace_id
        # Return: self.build_success_result(...) or self.build_error_result(...)
```

## Lark Integration

- **Client**: `app/integrations/lark/client.py` - API calls (send message, get user info, etc.)
- **Service**: `app/integrations/lark/service.py` - Business operations wrapper
- **Schemas**: `app/integrations/lark/schemas.py` - Message models, `LarkCardBuilder`
- **Signature**: `app/integrations/lark/signature.py` - Callback signature verification

Key message types: text, markdown, interactive_card (interactive cards)

## Dialog State Machine

States defined in `app/orchestrator/schemas.py`:
- `IDLE` - Waiting for new intent
- `PARAM_COLLECTING` - Collecting missing parameters
- `CONFIRMATION_PENDING` - Waiting for user confirmation
- `EXECUTING` - Skill execution in progress
- `COMPLETED` - Execution finished

## Environment Variables

Key configs in `.env`:
- `LARK_APP_ID`, `LARK_APP_SECRET`, `LARK_ENCRYPT_KEY` - Lark app credentials
- `LARK_VERIFICATION_TOKEN` - Callback verification
- `DATABASE_URL` - PostgreSQL (asyncpg driver)
- `REDIS_URL` - Redis connection
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` - Celery config
- `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL_NAME` - LLM config

## Tech Stack

- Python 3.11, FastAPI, SQLAlchemy 2.x + Alembic, Pydantic v2
- Celery + RabbitMQ for async tasks
- PostgreSQL 15+ with pgvector extension
- Redis 7+ for caching
- pytest + pytest-asyncio for testing (80% coverage required)
- ruff + black + mypy for code quality

## Naming Conventions

- Skill names: snake_case English (e.g., `project_overview`, `cost_estimation`)
- Display names: Chinese (e.g., "项目总览查询", "成本估算")
- Domain models: PascalCase classes
- Database tables: lowercase with underscores