# PM Digital Employee - 项目经理数字员工系统

<div align="center">

**国有大型银行科技子公司项目管理部智能助理系统**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 项目简介

项目经理数字员工（PM Digital Employee）是面向国有大型银行科技子公司项目管理部的智能助理系统。系统以飞书为唯一用户交互入口，通过AI能力帮助项目经理完成项目管理主责主业相关任务，实现：

- 🎯 **释放项目经理30%+事务性工作**
- 📊 **统一项目管理规范**
- ⚠️ **实现风险前置预警**
- 🔒 **全流程符合金融监管与合规要求**

## ✨ 核心功能（一期MVP）

| 序号 | 功能 | 说明 |
|------|------|------|
| 1 | 项目总览查询 | 一键获取项目核心指标概览 |
| 2 | 项目周报生成 | 自动汇总项目进展生成周报 |
| 3 | WBS自动生成 | 基于需求自动生成工作分解结构 |
| 4 | 任务进度更新 | 便捷更新任务完成状态 |
| 5 | 风险识别与预警 | 智能识别项目风险并预警 |
| 6 | 成本监控 | 实时监控项目成本执行情况 |
| 7 | 制度规范答疑 | RAG驱动的项目管理制度问答 |
| 8 | 项目情况咨询 | 智能查询项目相关信息 |
| 9 | 会议纪要生成 | 自动生成会议纪要文档 |
| 10 | 合规审核 | 预立项/立项材料合规初审 |

## 🏗️ 技术架构

### 9层分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 接入层        │ 飞书 Bot Webhook、Callback、File Upload       │
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

### 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 语言 | Python | 3.11 |
| Web框架 | FastAPI | 0.115+ |
| ORM | SQLAlchemy | 2.x |
| 数据库 | PostgreSQL | 16 (含pgvector) |
| 缓存 | Redis | 7.4 |
| 消息队列 | RabbitMQ | 4.0 |
| 异步任务 | Celery | 5.4 |
| 数据校验 | Pydantic | v2 |
| 测试框架 | pytest | 8.x |
| 容器化 | Docker Compose | - |

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Docker & Docker Compose
- Git

### 1. 克隆项目

```bash
git clone <repository_url>
cd pm_digital_employee
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（必须修改以下配置）
# - APP_SECRET_KEY: 应用密钥
# - POSTGRES_PASSWORD: 数据库密码
# - REDIS_PASSWORD: Redis密码
# - RABBITMQ_PASSWORD: RabbitMQ密码
# - LARK_APP_ID: 飞书应用ID
# - LARK_APP_SECRET: 飞书应用密钥
vim .env
```

### 3. 一键启动

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

### 4. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| API文档 | http://localhost:8000/docs | Swagger UI |
| ReDoc文档 | http://localhost:8000/redoc | ReDoc |
| 健康检查 | http://localhost:8000/health | 探活接口 |
| RabbitMQ管理 | http://localhost:15672 | 管理界面 |

### 5. 本地开发

```bash
# 安装依赖
pip install -e ".[dev]"

# 启动开发服务器
uvicorn app.main:app --reload

# 运行测试
pytest

# 代码格式化
black app/
ruff check app/

# 类型检查
mypy app/
```

## 📁 项目结构

```
pm_digital_employee/
├── app/
│   ├── api/                 # 接口层
│   ├── core/                # 核心配置
│   ├── domain/              # 领域模型
│   ├── db/                  # 数据库层
│   ├── repositories/        # 数据访问层
│   ├── services/            # 业务服务层
│   ├── orchestrator/        # 编排层
│   ├── skills/              # Skill插件层
│   ├── ai/                  # AI能力层
│   ├── rag/                 # RAG检索层
│   ├── integrations/        # 第三方集成
│   ├── agents/              # 多Agent层
│   ├── tasks/               # 异步任务
│   ├── events/              # 事件总线
│   ├── presentation/        # 展示层
│   ├── security/            # 安全模块
│   ├── tests/               # 测试代码
│   └── main.py              # 应用入口
├── alembic/                 # 数据库迁移
├── scripts/                 # 运维脚本
├── docs/                    # 文档目录
├── prompts/                 # Prompt模板
├── docker-compose.yml       # Docker配置
├── Dockerfile               # 容器构建
├── pyproject.toml           # 项目配置
└── README.md                # 项目说明
```

## 🔒 安全特性

- **项目级强隔离**: 用户只能访问自己参与的项目数据
- **全流程审计**: 所有操作记录审计日志，留存6个月以上
- **权限感知RAG**: 检索全链路权限过滤，无权限知识不可召回
- **提示词注入防护**: 检测并拦截提示词注入攻击
- **敏感信息脱敏**: 输出内容自动脱敏敏感字段
- **飞书事件验签**: 所有飞书事件严格验签

## 📖 飞书应用配置

### 1. 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 配置应用权限

### 2. 必需权限列表

```
# 消息权限
im:message
im:message:send_as_bot
im:message:group_at_msg

# 用户权限
contact:user.base:readonly
contact:user.department_id:readonly

# 群权限
im:chat:readonly
im:chat.member:readonly

# 文件权限
drive:drive:readonly
drive:file:upload

# 日历权限
calendar:calendar:readonly

# 任务权限
task:task:readonly
task:task:write
```

### 3. 配置事件订阅

- 事件订阅地址: `https://your-domain/lark/webhook/message`
- 消息卡片回调地址: `https://your-domain/lark/callback/card`

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行指定测试
pytest app/tests/test_health.py -v

# 生成覆盖率报告
pytest --cov=app --cov-report=html

# 运行安全测试
pytest -m security
```

## 📚 文档

- [架构设计文档](docs/architecture.md)
- [安全合规文档](docs/security.md)
- [飞书集成手册](docs/feishu_integration.md)
- [Skill开发指南](docs/skill_development_guide.md)
- [运维操作手册](docs/operations_runbook.md)
- [API接口文档](docs/api_reference.md)

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

- 项目团队: PM Digital Employee Team
- 技术支持: support@example.com

---

<div align="center">

**⚠️ 注意: 本系统运行在内网环境，所有数据需符合金融行业安全合规要求**

</div>