# PM Digital Employee 部署包清单
# 版本: v1.0.0
# 日期: 2026-03-31
# 飞书版

## 一、部署包文件清单

### 核心配置文件
```
docker-compose.yml      # Docker服务编排配置
Dockerfile              # 多阶段构建镜像
.env.example            # 环境变量模板（需复制为.env并修改）
requirements.txt        # Python依赖清单
pyproject.toml          # 项目配置
```

### 部署脚本
```
deploy.sh               # 一键部署脚本（安装Docker、启动服务）
update.sh               # 代码更新部署脚本
manage.sh               # 服务管理脚本（start/stop/restart/logs/status）
package.sh              # 打包脚本（创建部署压缩包）
```

### 文档
```
README.md               # 项目说明文档
DEPLOYMENT.md           # 详细部署指南
docs/QUICK_START.md     # 快速启动指南
docs/lark_integration.md  # 飞书集成手册
docs/architecture.md    # 架构设计文档
docs/security.md        # 安全合规文档
docs/skill_development_guide.md  # Skill开发指南
docs/api_reference.md   # API参考文档
```

### 数据库相关
```
scripts/init_pgvector.sql   # pgvector扩展初始化
alembic.ini                 # Alembic迁移配置
alembic/                    # 数据库迁移脚本目录
```

### 应用代码
```
app/
├── main.py                     # FastAPI入口
├── api/
│   ├── router.py               # 路由注册
│   ├── health.py               # 健康检查接口
│   ├── lark_webhook.py        # 飞书消息Webhook
│   ├── lark_callback.py       # 飞书卡片回调
│   └── deps.py                 # 依赖注入
├── core/
│   ├── config.py               # Pydantic配置
│   ├── logging.py              # 结构化日志
│   ├── security.py             # 安全工具
│   ├── exceptions.py           # 异常定义
│   ├── middleware.py           # 中间件
│   └── dependencies.py         # 依赖注入
├── domain/
│   ├── base.py                 # SQLAlchemy基类
│   ├── enums.py                # 枚举定义
│   └── models/                 # ORM模型
│       ├── user.py
│       ├── project.py
│       ├── task.py
│       ├── cost.py
│       ├── risk.py
│       ├── document.py
│       └── ...
├── db/
│   ├── session.py              # 数据库会话
│   └── init.py                 # 初始化
├── repositories/               # 数据访问层
├── services/                   # 业务服务层
├── orchestrator/               # 编排层
├── skills/                     # Skill插件层
├── ai/                         # AI能力层
├── rag/                        # RAG检索层
├── integrations/
│   ├── lark/                  # 飞书集成
│   │   ├── client.py           # API客户端
│   │   ├── signature.py        # 签名验签
│   │   ├── schemas.py          # 数据模型
│   │   ├── service.py          # 业务服务
│   ├── project_system/         # 项目管理系统适配
│   ├── finance_system/         # 财务系统适配
│   └── devops_system/          # DevOps系统适配
├── security/                   # 安全模块
├── tasks/                      # 异步任务
├── events/                     # 事件总线
├── presentation/               # 展示层
│   ├── cards/                  # 飞书卡片
│   └── renderers.py            # 结果渲染器
└── utils/                      # 工具类
```

### Prompt模板
```
prompts/
├── intent_recognition.md
├── weekly_report.md
├── wbs_generation.md
├── risk_analysis.md
├── compliance_review.md
└── meeting_minutes.md
```

### 测试代码
```
tests/
├── test_health.py
├── test_models.py
├── test_access_control.py
├── test_orchestrator.py
├── test_skills.py
├── test_lark_webhook.py
└── ...
```

---

## 二、部署包使用流程

### 1. 上传到服务器
```bash
scp pm-digital-employee-v1.0.0.tar.gz user@server:/opt/
```

### 2. 解压并配置
```bash
cd /opt
tar -xzf pm-digital-employee-v1.0.0.tar.gz
cd pm-digital-employee-v1.0.0
cp .env.example .env
vim .env  # 配置飞书参数
```

### 3. 一键部署
```bash
./deploy.sh
```

### 4. 验证服务
```bash
./manage.sh status
curl http://localhost:8000/health
```

### 5. 配置飞书回调
在飞书开放平台配置：
- URL: https://your-domain.com/lark/webhook/event
- Token: 与.env中一致
- EncodingAESKey: 与.env中一致

---

## 三、飞书配置参数

| 参数 | 说明 | 获取方式 |
|------|------|----------|
| LARK_APP_ID | 应用ID | 飞书开放平台 > 应用管理 |
| LARK_APP_ID | 飞书应用AppID | 飞书开放平台应用详情 |
| LARK_APP_SECRET | 飞书应用密钥 | 飞书开放平台应用详情 |
| LARK_ENCRYPT_KEY | 事件加密密钥 | 配置事件订阅时设置 |
| LARK_VERIFICATION_TOKEN | 验证令牌 | 配置事件订阅时设置 |

---

## 四、服务端口

| 端口 | 服务 | 说明 |
|------|------|------|
| 8000 | FastAPI | 应用服务（对外） |
| 5432 | PostgreSQL | 数据库（仅内部） |
| 6379 | Redis | 缓存（仅内部） |
| 5672 | RabbitMQ | 消息队列（仅内部） |
| 15672 | RabbitMQ Management | 管理界面（仅内部） |

---

## 五、运维命令

| 命令 | 说明 |
|------|------|
| ./manage.sh start | 启动服务 |
| ./manage.sh stop | 停止服务 |
| ./manage.sh restart | 重启服务 |
| ./manage.sh logs | 查看日志 |
| ./manage.sh status | 查看状态 |
| ./manage.sh build | 重新构建镜像 |
| ./update.sh | 更新部署 |

---

**打包时间:** 2026-03-31  
**版本:** v1.0.0  
**交互入口:** 飞书（Lark）