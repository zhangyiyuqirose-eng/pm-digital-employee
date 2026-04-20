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
pip install -r requirements-dev.txt

# Run development server (hot reload)
make dev
# Or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery Worker
make dev-celery

# Start Celery Beat scheduler
make dev-celery-beat
```

### Testing
```bash
# Run all tests (559 tests)
make test
# Or: pytest tests/ -v

# Run with coverage (80% minimum)
make test-cov

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration

# Run E2E tests
make test-e2e

# Run specific test file
pytest tests/unit/test_file_parser_service.py -v

# Run specific test method
pytest tests/unit/test_data_extractor_service.py::TestDataExtractorServiceHelpers::test_extract_dates_standard_format -v
```

### Code Quality
```bash
# Run all quality checks (lint + format + type-check)
make quality

# Lint with ruff
make lint

# Auto-fix lint issues
make lint-fix

# Format with black
make format

# Check format without modifying
make format-check

# Type check with mypy
make type-check

# Security check with bandit
make security

# Run pre-commit on all files
make pre-commit

# Install pre-commit hooks
make pre-commit-install
```

### Docker Deployment
```bash
# Build Docker images
make docker-build

# Start all Docker services
make docker-up

# View logs
make docker-logs

# Restart services
make docker-restart

# Stop services
make docker-down

# Clean up containers and volumes
make docker-clean
```

### Database
```bash
# Initialize database (create extensions + migrate)
make db-init

# Run migrations
make db-migrate

# Rollback one migration version
make db-migrate-down

# Create new migration (requires MSG variable)
make db-migration-create MSG="add_new_table"

# Seed demo data
make db-seed

# Reset database (WARNING: destructive)
make db-reset

# Current migration: 002_document_parse (v1.3.0)
```

### Operations
```bash
# Health check
make health-check

# Bootstrap system
make bootstrap

# Backup database
make backup

# Clean temp files
make clean
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

## Project Structure

```
pm-digital-employee/
├── app/                      # Application source code
│   ├── api/                  # FastAPI endpoints
│   ├── ai/                   # LLM gateway, prompts, safety
│   ├── core/                 # Config, dependencies, exceptions
│   ├── domain/               # Domain models (SQLAlchemy)
│   ├── events/               # Event handlers
│   ├── integrations/         # External integrations (Lark)
│   ├── orchestrator/         # Core orchestration layer
│   ├── rag/                  # RAG pipeline
│   ├── repositories/         # Data repositories
│   ├── services/             # Business services
│   ├── skills/               # Skill plugins (12 skills)
│   ├── tasks/                # Celery async tasks
│   └── utils/                # Utilities
├── tests/                    # Test suite (559 tests)
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └ e2e/                    # End-to-end tests
├── docs/                     # Documentation
│   ├── api/                  # API reference
│   ├── architecture/         # Architecture docs
│   ├── deployment/           # Deployment guides
│   ├── design/               # Design documents
│   ├── development/          # Development guides
│   ├── reports/              # Reports and analysis
│   ├── requirements/         # Requirements specs
│   └ testing/                # Test documentation
├── scripts/                  # Utility scripts
│   ├── db/                   # Database scripts
│   └ dev/                    # Development scripts
│   └ ops/                    # Operations scripts
│   └ validation/             # Validation scripts
├── prompts/                  # LLM prompt templates
├── alembic/                  # Database migrations
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Docker configuration
├── Makefile                  # Build commands
└── VERSION.txt               # Version info
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
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for API and flows
- `tests/e2e/` - End-to-end workflow tests
- `docs/` - Organized documentation by category

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

**Skill registration flow:**
```python
# In app/skills/__init__.py
from app.skills.document_parse_skill import DocumentParseSkill

def register_all_skills(registry: SkillRegistry) -> None:
    registry.register(DocumentParseSkill)
    # ... other skills
```

**BaseSkill provides:**
- `user_id`, `chat_id`, `project_id` - Context properties
- `params` - Dict of parameters
- `get_param(key, default)` - Get single parameter
- `build_success_result()` / `build_error_result()` - Result builders

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

**API Entry Points:**
- `app/api/lark_webhook.py` - Receives messages from Lark (POST `/api/v1/lark/webhook`)
- `app/api/lark_callback.py` - Handles interactive card callbacks

Key message types: text, markdown, interactive_card, file, image (v1.3.0)

**LarkCardBuilder** (`app/integrations/lark/schemas.py`) for constructing interactive cards:
- `build_confirm_card()` - Confirmation dialogs
- `build_success_card()` - Success notifications
- `build_error_card()` - Error notifications
- `build_param_collect_card()` - Parameter collection forms

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
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` - Celery config (RabbitMQ)
- `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL_NAME` - LLM config

## Environment Requirements

- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- Redis 7+ for caching
- RabbitMQ 3.12+ for Celery task queue

## Pre-commit Hooks

The project uses pre-commit hooks for automated code quality checks:
- **ruff** - Fast Python linter with auto-fix
- **black** - Code formatter (line-length 100)
- **isort** - Import sorting (black profile)
- **mypy** - Type checking
- **bandit** - Security scanning
- **prettier** - YAML/JSON/Markdown formatting

Install hooks with: `make pre-commit-install` or `pre-commit install`

Hooks run automatically on commit. Block commits to master/main branch.

## Async Task Flow (Celery)

Celery tasks for background processing:
- `app/tasks/celery_app.py` - Celery app configuration
- `app/tasks/report_tasks.py` - Report generation tasks
- `app/tasks/tasks.py` - General async tasks

Task configuration:
- Task timeout: 1 hour (soft timeout: 55 min)
- Results expire: 24 hours
- Worker prefetch: 1 task
- Max tasks per worker child: 100

Start worker: `celery -A app.tasks.celery_app worker --loglevel=info`
Start beat: `celery -A app.tasks.celery_app beat --loglevel=info`

## Tech Stack

- Python 3.11, FastAPI, SQLAlchemy 2.x + Alembic, Pydantic v2
- Celery + RabbitMQ for async tasks
- PostgreSQL 15+ with pgvector extension
- Redis 7+ for caching
- pytest + pytest-asyncio for testing (559 tests, 80% coverage required)
- ruff + black + mypy for code quality

## Naming Conventions

- Skill names: snake_case English (e.g., `project_overview`, `document_parse`)
- Display names: Chinese (e.g., "项目总览查询", "文档智能解析")
- Domain models: PascalCase classes
- Database tables: lowercase with underscores
- Prompt templates: lowercase with underscores in `prompts/` directory