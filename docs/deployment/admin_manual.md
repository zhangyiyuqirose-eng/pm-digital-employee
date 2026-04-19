# 项目经理数字员工系统 - 管理员手册

## 一、系统管理概述

### 管理员角色
- **系统管理员**：负责系统配置、用户管理、权限分配
- **项目管理员**：负责项目创建、成员分配、Skill配置
- **审计管理员**：负责审计日志查看、合规检查

### 管理入口
通过飞书管理后台或API接口进行管理操作。

## 二、用户管理

### 1. 用户列表查看

**API接口**
```
GET /api/v1/admin/users
```

**返回内容**
- 用户ID
- 飞书ID
- 姓名
- 部门
- 角色
- 项目列表

### 2. 用户权限分配

为用户分配项目角色：

| 角色 | 权限范围 |
|------|----------|
| admin | 系统管理员，全权限 |
| project_manager | 项目经理，项目内全权限 |
| pm | 项目管理员，项目内管理权限 |
| tech_lead | 技术负责人，项目内技术权限 |
| member | 成员，项目内基本权限 |
| auditor | 审计员，审计日志查看权限 |

**操作示例**
```
POST /api/v1/admin/users/{user_id}/roles
{
    "project_id": "project_xxx",
    "role": "pm"
}
```

### 3. 用户导入

从飞书同步用户信息：
```
POST /api/v1/admin/users/sync
```

## 三、项目管理

### 1. 项目创建

**API接口**
```
POST /api/v1/admin/projects
{
    "name": "项目名称",
    "description": "项目描述",
    "pm_id": "user_xxx",
    "start_date": "2026-01-01",
    "end_date": "2026-06-30"
}
```

### 2. 项目列表管理

**查看项目列表**
```
GET /api/v1/admin/projects
```

**更新项目信息**
```
PUT /api/v1/admin/projects/{project_id}
{
    "name": "新项目名称",
    "end_date": "2026-12-31"
}
```

### 3. 群-项目绑定

将飞书群与项目绑定：

**创建绑定**
```
POST /api/v1/admin/bindings
{
    "chat_id": "chat_xxx",
    "project_id": "project_xxx",
    "bind_type": "primary"
}
```

**绑定类型**
- primary：主绑定，群消息默认关联此项目
- secondary：次绑定，群可关联多个项目

### 4. 项目成员管理

**添加成员**
```
POST /api/v1/admin/projects/{project_id}/members
{
    "user_id": "user_xxx",
    "role": "member"
}
```

**移除成员**
```
DELETE /api/v1/admin/projects/{project_id}/members/{user_id}
```

## 四、Skill管理

### 1. Skill列表查看

**API接口**
```
GET /api/v1/admin/skills
```

**返回内容**
| Skill名称 | 显示名称 | 描述 | 默认启用 |
|-----------|----------|------|----------|
| project_overview | 项目总览 | 查看项目整体状态 | 是 |
| weekly_report | 周报生成 | 自动生成周报 | 是 |
| wbs_generation | WBS生成 | 生成工作分解结构 | 是 |
| task_update | 任务更新 | 更新任务进度 | 是 |
| risk_alert | 风险预警 | 风险识别和预警 | 是 |
| cost_monitor | 成本监控 | 成本执行监控 | 是 |
| policy_qa | 制度答疑 | 制度规范问答 | 是 |
| project_query | 项目查询 | 项目信息查询 | 是 |
| meeting_minutes | 会议纪要 | 生成会议纪要 | 是 |
| compliance_review | 合规初审 | 材料合规检查 | 是 |

### 2. 项目Skill开关

为项目启用/禁用特定Skill：

**查看项目Skill配置**
```
GET /api/v1/admin/projects/{project_id}/skills
```

**更新Skill配置**
```
PUT /api/v1/admin/projects/{project_id}/skills/{skill_name}
{
    "enabled": true
}
```

### 3. Skill权限配置

每个Skill有默认权限要求，可在manifest中查看：

```json
{
    "skill_name": "weekly_report",
    "allowed_roles": ["project_manager", "pm", "tech_lead"],
    "required_permissions": [
        {"resource": "project", "action": "read"}
    ]
}
```

## 五、知识库管理

### 1. 知识库文档管理

**上传文档**
```
POST /api/v1/admin/knowledge/documents
{
    "title": "项目管理制度",
    "content": "制度内容...",
    "scope_type": "global",
    "tags": ["制度", "管理"]
}
```

**scope_type说明**
- global：全局知识，所有用户可访问
- project：项目知识，仅项目成员可访问
- department：部门知识，仅部门成员可访问

### 2. 知识库索引

文档上传后需要建立向量索引：

**手动触发索引**
```
POST /api/v1/admin/knowledge/index
{
    "document_ids": ["doc_xxx", "doc_yyy"]
}
```

**索引状态查看**
```
GET /api/v1/admin/knowledge/index/status
```

### 3. 知识库导入脚本

使用脚本批量导入知识库：

```bash
python scripts/import_knowledge.py \
    --source /path/to/documents \
    --scope global
```

## 六、审计管理

### 1. 审计日志查看

**API接口**
```
GET /api/v1/audit/logs
```

**查询参数**
| 参数 | 说明 |
|------|------|
| user_id | 用户ID筛选 |
| project_id | 项目ID筛选 |
| action | 操作类型筛选 |
| start_time | 开始时间 |
| end_time | 结束时间 |

### 2. 审计日志导出

**导出日志**
```
GET /api/v1/audit/logs/export
```

### 3. 审计报告生成

定期生成审计报告：
```
POST /api/v1/audit/reports/generate
{
    "period": "monthly",
    "start_date": "2026-03-01",
    "end_date": "2026-03-31"
}
```

## 七、系统配置

### 1. 飞书应用配置

配置飞书应用信息：

| 配置项 | 说明 |
|--------|------|
| APP_ID | 飞书应用ID |
| APP_SECRET | 飞书应用密钥 |
| VERIFICATION_TOKEN | 事件验证令牌 |

### 2. LLM配置

配置LLM Provider：

| Provider | 配置项 |
|----------|--------|
| OpenAI | API_KEY, BASE_URL |
| Azure | API_KEY, ENDPOINT |
| 智谱AI | API_KEY |
| 通义千问 | API_KEY |

### 3. 系统参数配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| MAX_INPUT_LENGTH | 输入最大长度 | 10000 |
| LLM_TIMEOUT | LLM调用超时 | 30s |
| RAG_TOP_K | RAG检索数量 | 5 |
| SESSION_TIMEOUT | 会话超时时间 | 3600s |

## 八、监控管理

### 1. 系统监控

**健康检查**
```
GET /health
GET /ready
GET /live
```

**监控指标**
- API请求量
- API响应时间
- Skill执行次数
- LLM调用次数
- RAG查询次数

### 2. 告警配置

配置告警规则：

| 告警类型 | 条件 | 通知方式 |
|----------|------|----------|
| 服务异常 | health失败 | 飞书消息 |
| 高延迟 | 响应>5s | 飞书消息 |
| 高错误率 | 错误率>5% | 飞书消息 |

### 3. 日志查看

查看系统日志：
```bash
docker-compose logs -f app
```

## 九、数据管理

### 1. 数据备份

**手动备份**
```bash
./scripts/backup_database.sh
```

**定时备份**
配置定时任务，每日凌晨自动备份。

### 2. 数据恢复

**恢复数据**
```bash
./scripts/restore_database.sh backup_file.sql
```

### 3. 数据清理

**清理过期数据**
```
POST /api/v1/admin/data/cleanup
{
    "type": "audit_logs",
    "before_date": "2026-01-01"
}
```

## 十、运维脚本

### 可用脚本

| 脚本 | 说明 |
|------|------|
| bootstrap.sh | 一键初始化 |
| health_check.sh | 健康检查 |
| backup_database.sh | 数据库备份 |
| run_tests.sh | 运行测试 |
| lint.sh | 代码检查 |
| format.sh | 代码格式化 |

### 一键初始化

```bash
./scripts/bootstrap.sh
```

初始化内容：
- 数据库创建
- 表结构迁移
- 基础数据导入
- 知识库索引

## 十一、故障处理

### 1. 常见问题排查

| 问题 | 排查步骤 |
|------|----------|
| 服务无法启动 | 检查配置、日志 |
| 飞书消息不响应 | 检查Webhook、签名 |
| LLM调用失败 | 检查API Key、网络 |
| RAG无答案 | 检查知识库、索引 |

### 2. 日志分析

```bash
# 查找错误日志
grep ERROR /var/log/pm/*.log

# 查找特定trace
grep trace_id=xxx /var/log/pm/*.log
```

### 3. 紧急处理

**重启服务**
```bash
docker-compose restart app
```

**回滚版本**
```bash
git checkout previous_version
docker-compose build
docker-compose up -d
```