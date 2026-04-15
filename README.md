# 项目经理数字员工（PM Digital Employee）

## 项目简介

项目经理数字员工系统是一个基于**飞书**的项目管理智能助手，服务于国有大型银行科技子公司项目管理部。通过自然语言交互，帮助项目经理完成日常事务性工作，提升工作效率。

**飞书作为唯一用户交互入口。**

## 核心功能

### 一期MVP功能列表

1. **项目总览查询** - 查询项目整体状态、进度、里程碑、风险、成本
2. **项目周报生成** - 自动汇总本周任务进展、下周计划、风险状态
3. **WBS自动生成** - 根据项目信息生成工作分解结构
4. **任务进度更新** - 更新任务进度、状态、备注
5. **风险识别与预警** - 识别项目风险、发出预警提示
6. **成本监控** - 对比预算与实际支出、预警超支风险
7. **制度规范答疑** - 基于RAG回答项目管理规章制度问题
8. **项目情况咨询** - 回答项目具体情况相关问题
9. **会议纪要生成** - 根据会议内容生成结构化纪要
10. **预立项/立项材料合规初审** - 审核材料合规性

## 技术架构

### 9层分层架构

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
│ 8. 集成适配层    │ 项目管理、财务、DevOps、OA、飞书适配器      │
├─────────────────────────────────────────────────────────────────┤
│ 9. 数据层        │ PostgreSQL、Redis、pgvector、Celery         │
└─────────────────────────────────────────────────────────────────┘
```

### 技术栈

- **语言**: Python 3.11
- **Web框架**: FastAPI
- **ORM**: SQLAlchemy 2.x + Alembic
- **数据校验**: Pydantic v2
- **异步任务**: Celery + RabbitMQ
- **缓存**: Redis
- **数据库**: PostgreSQL（含pgvector）
- **测试**: pytest + pytest-asyncio
- **代码质量**: ruff + black + mypy
- **交互入口**: 飞书（Feishu）

## 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- RabbitMQ 3.12+

### 本地开发

```bash
# 克隆代码
git clone <repository_url>
cd pm_digital_employee

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，配置数据库、Redis、飞书等参数

# 初始化数据库
alembic upgrade head

# 启动开发服务器
python -m app.main
```

### Docker部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

## 项目结构

```
pm_digital_employee/
├── app/
│   ├── api/                    # API接口层
│   ├── core/                   # 核心配置
│   ├── domain/                 # 领域模型
│   ├── db/                     # 数据库
│   ├── repositories/           # 数据访问层
│   ├── services/               # 业务服务层
│   ├── orchestrator/           # 编排层
│   ├── skills/                 # Skill插件
│   ├── ai/                     # AI能力层
│   ├── rag/                    # RAG检索
│   ├── integrations/           # 第三方集成（含飞书）
│   ├── security/               # 安全模块
│   ├── tasks/                  # 异步任务
│   └── main.py                 # 入口文件
├── alembic/                    # 数据库迁移
├── tests/                      # 测试代码
├── docs/                       # 文档
└── pyproject.toml              # 项目配置
```

## 配置说明

### 环境变量

主要环境变量参见 `.env.example` 文件：

- `APP_ENV`: 运行环境（development/staging/production）
- `DATABASE_URL`: PostgreSQL连接串
- `REDIS_URL`: Redis连接串
- `FEISHU_APP_ID`: 飞书应用AppID
- `FEISHU_APP_SECRET`: 飞书应用AppSecret
- `FEISHU_ENCRYPT_KEY`: 飞书加密密钥
- `FEISHU_VERIFICATION_TOKEN`: 飞书验证令牌
- `LLM_API_KEY`: LLM API密钥

### 飞书配置

1. 创建飞书自建应用
2. 配置回调URL，设置Webhook URL
3. 开通所需权限（消息、用户信息、群信息等）
4. 配置IP白名单
5. 获取AppID、AppSecret、EncryptKey、VerificationToken

## 安全合规

- 项目级数据隔离
- 基于角色的权限控制
- 完整的审计日志
- 输入校验与SQL注入防护
- 敏感数据脱敏
- LLM输出安全检查
- API限流与并发控制

## 测试

```bash
# 运行所有测试
pytest

# 运行带覆盖率的测试
pytest --cov=app tests/

# 运行特定测试
pytest tests/test_main.py -v
```

## 文档

- [架构设计文档](docs/architecture.md)
- [安全合规文档](docs/security.md)
- [飞书集成指南](docs/feishu_integration.md)
- [Skill开发指南](docs/skill_development_guide.md)
- [API参考文档](docs/api_reference.md)

## 许可证

内部项目，仅供授权使用。