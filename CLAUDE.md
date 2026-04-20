# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PM Digital Employee is a **Lark (飞书)**-based project management intelligent assistant for a state-owned bank's technology subsidiary project management department. **Lark is the ONLY user interaction entrypoint.**

Current version: v1.3.0 (see VERSION.txt and CHANGELOG.md for release history).

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
# Run all tests (549 tests, 100% pass rate required)
pytest

# Run with coverage (80% minimum required)
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_file_parser_service.py -v

# Run specific test
pytest tests/unit/test_data_extractor_service.py::TestDataExtractorServiceHelpers::test_extract_dates_standard_format -v
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

# Current migration: 002_document_parse (v1.3.0)
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
│ 7. Skill插件层   │ 12个核心Skill，BaseSkill规范，manifest      │
├─────────────────────────────────────────────────────────────────┤
│ 8. 集成适配层    │ 项目管理、财务、DevOps、OA、飞书适配器      │
├─────────────────────────────────────────────────────────────────┤
│ 9. 数据层        │ PostgreSQL、Redis、pgvector、Celery         │
└─────────────────────────────────────────────────────────────────┘
```

## Key Directories

- `app/api/` - FastAPI endpoints (Lark webhook/callback at `lark_webhook.py`, `lark_callback.py`)
- `app/orchestrator/` - Core orchestration: intent routing, dialog state machine, skill registry
- `app/skills/` - 12 Skill implementations inheriting from `BaseSkill`
- `app/services/` - Business services including v1.3.0 document parsing pipeline
- `app/integrations/lark/` - Lark integration: client, signature verification, message schemas, file APIs
- `app/ai/` - LLM gateway, prompt management, output parsing, safety guard
- `app/rag/` - RAG pipeline: chunking, indexing, retrieval, reranking
- `app/domain/models/` - SQLAlchemy domain models
- `prompts/` - LLM prompt templates (v1.3.0 document parsing templates)

## Core Flow: Orchestrator

The `Orchestrator` coordinates the complete message processing pipeline:

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

**Current Skills (12):**
1. `project_overview` - 项目总览查询
2. `weekly_report` - 项目周报生成
3. `wbs_generation` - WBS自动生成
4. `task_update` - 任务进度更新
5. `risk_alert` - 风险识别与预警
6. `cost_monitor` - 成本监控
7. `policy_qa` - 制度规范答疑
8. `project_query` - 项目情况咨询
9. `meeting_minutes` - 会议纪要生成
10. `compliance_review` - 预立项/立项材料合规初审
11. `document_parse` - 文档智能解析 (v1.3.0)
12. `document_confirm` - 文档确认处理 (v1.3.0)

Every Skill must:

1. Inherit from `BaseSkill` (`app/skills/base.py`)
2. Define class attributes: `skill_name`, `display_name`, `description`, `version`
3. Implement `async execute() -> SkillExecutionResult`
4. Define Manifest via `SkillManifestBuilder` (see `app/orchestrator/skill_manifest.py`)
5. Register in `app/skills/__init__.py` via `register_all_skills()`

## Document Parsing Pipeline (v1.3.0)

Fourth data entry channel for intelligent document parsing:

```
文件下载 → 格式解析 → 文档分类 → 数据提取 → 数据导入 → 用户反馈
    │           │           │           │           │
    ▼           ▼           ▼           ▼           ▼
 Lark API   FileParser  Classifier   Extractor   Importer
```

**Key Services:**
- `FileParserService` - Multi-format file parsing (DOCX/PDF/XLSX/XLS/CSV/PPTX/TXT/MD/JPG/PNG/BMP)
- `DocumentClassifierService` - Smart document classification (weekly_report/meeting_minutes/wbs/risk_register/etc.)
- `DataExtractorService` - LLM-based data extraction with confidence scoring
- `DataImportService` - Data import with ValidationService and SyncEngine integration
- `DocumentParseService` - Main orchestrator coordinating the full pipeline

**Confidence Thresholds:**
- >= 95%: Auto-import, send success card
- >= 80%: Auto-import, send confirmation card
- >= 60%: Send confirmation card for user review
- < 60%: Parse failed, send error card

**Database Model:**
- `DocumentParseRecord` (`app/domain/models/document_parse_record.py`) - 40+ fields tracking full parse process

## Lark Integration

- **Client**: `app/integrations/lark/client.py` - API calls including file download/upload (v1.3.0)
- **Service**: `app/integrations/lark/service.py` - Business operations wrapper
- **Schemas**: `app/integrations/lark/schemas.py` - Message models, `LarkCardBuilder`
- **Signature**: `app/integrations/lark/signature.py` - Callback signature verification

Key message types: text, markdown, interactive_card, file, image (v1.3.0)

## Dialog State Machine

States defined in `app/orchestrator/schemas.py`:
- `IDLE` - Waiting for new intent
- `PARAM_COLLECTING` - Collecting missing parameters
- `CONFIRMATION_PENDING` - Waiting for user confirmation
- `EXECUTING` - Skill execution in progress
- `COMPLETED` - Execution finished

## Multi-Source Data Entry

Four data entry methods share unified validation via `ValidationService`:

1. **Lark Card** - User submits via Lark interactive cards
2. **Excel Import** - Batch import via Excel templates
3. **Lark Sheet Sync** - Auto-sync from Lark sheets
4. **Document Parse** - Intelligent document parsing (v1.3.0)

Key enums for data source handling:
- `DataSource`: lark_card / excel_import / lark_sheet_sync / document_parse
- `SyncMode`: to_sheet / from_sheet / bidirectional
- `SyncFrequency`: realtime / 5min / 15min / 1hour
- `ImportMode`: full_replace / incremental_update / append_only

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
- pytest + pytest-asyncio for testing (549 tests, 80% coverage required)
- ruff + black + mypy for code quality

## Naming Conventions

- Skill names: snake_case English (e.g., `project_overview`, `document_parse`)
- Display names: Chinese (e.g., "项目总览查询", "文档智能解析")
- Domain models: PascalCase classes
- Database tables: lowercase with underscores
- Prompt templates: lowercase with underscores in `prompts/` directory