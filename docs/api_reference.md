# 项目经理数字员工系统 - API文档

## 一、API概述

### 基础信息
- 基础URL：`https://your-domain.com`
- API版本：v1
- 认证方式：Bearer Token（飞书API）

### 通用响应格式

```json
{
    "success": true,
    "data": {...},
    "message": "操作成功",
    "trace_id": "uuid"
}
```

### 错误响应格式

```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述"
    },
    "trace_id": "uuid"
}
```

## 二、健康检查接口

### GET /health
健康检查接口

**响应示例**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-03-31T10:00:00Z"
}
```

### GET /ready
就绪检查接口

**响应示例**
```json
{
    "status": "ready",
    "checks": {
        "database": "ok",
        "redis": "ok",
        "rabbitmq": "ok"
    }
}
```

### GET /live
存活检查接口

**响应示例**
```json
{
    "status": "alive"
}
```

## 三、飞书Webhook接口

### POST /lark/webhook/message
接收飞书消息

**请求头**
```
X-Lark-Request-Timestamp: timestamp
X-Lark-Request-Nonce: nonce
X-Lark-Signature: signature
```

**请求体**
```json
{
    "schema": "2.0",
    "header": {
        "event_id": "event_uuid",
        "event_type": "im.message.receive_v1",
        "create_time": "1234567890",
        "token": "verification_token",
        "app_id": "cli_xxx"
    },
    "event": {
        "sender": {
            "sender_id": {
                "open_id": "ou_xxx",
                "user_id": "user_xxx"
            }
        },
        "message": {
            "message_id": "msg_xxx",
            "content": "{\"text\":\"消息内容\"}",
            "message_type": "text",
            "create_time": "1234567890"
        }
    }
}
```

**响应**
```json
{
    "status": "ok"
}
```

### POST /lark/webhook/event
接收飞书事件

**请求体**
```json
{
    "schema": "2.0",
    "header": {...},
    "event": {...}
}
```

### POST /lark/callback/card
接收飞书卡片回调

**请求体**
```json
{
    "open_id": "ou_xxx",
    "token": "xxx",
    "action": {
        "value": {
            "action_type": "approve",
            "project_id": "project_xxx"
        }
    }
}
```

### POST /lark/url_verification
飞书URL校验

**请求体**
```json
{
    "challenge": "challenge_token",
    "token": "verification_token",
    "type": "url_verification"
}
```

**响应**
```json
{
    "challenge": "challenge_token"
}
```

## 四、项目API

### GET /api/v1/projects/{project_id}/overview
获取项目总览

**权限要求**
- project:read

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | string | 是 | 项目ID |

**响应示例**
```json
{
    "success": true,
    "data": {
        "project_id": "project_xxx",
        "name": "测试项目",
        "status": "进行中",
        "progress": 60,
        "start_date": "2026-01-01",
        "end_date": "2026-06-30",
        "pm": {
            "user_id": "user_xxx",
            "name": "张三"
        },
        "milestones": [
            {
                "id": "milestone_xxx",
                "name": "阶段1完成",
                "due_date": "2026-03-31",
                "status": "completed"
            }
        ],
        "statistics": {
            "total_tasks": 50,
            "completed_tasks": 30,
            "in_progress_tasks": 15,
            "pending_tasks": 5
        }
    }
}
```

### GET /api/v1/projects/{project_id}/tasks
获取任务列表

**权限要求**
- project:read

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | string | 是 | 项目ID |
| status | string | 否 | 任务状态筛选 |
| page | int | 否 | 页码 |
| size | int | 否 | 每页数量 |

**响应示例**
```json
{
    "success": true,
    "data": {
        "tasks": [
            {
                "id": "task_xxx",
                "name": "任务名称",
                "status": "in_progress",
                "progress": 50,
                "assignee": {
                    "user_id": "user_xxx",
                    "name": "张三"
                },
                "due_date": "2026-04-15"
            }
        ],
        "total": 50,
        "page": 1,
        "size": 10
    }
}
```

### PUT /api/v1/projects/{project_id}/tasks/{task_id}
更新任务

**权限要求**
- task:write

**请求体**
```json
{
    "status": "completed",
    "progress": 100,
    "actual_hours": 8
}
```

**响应示例**
```json
{
    "success": true,
    "data": {
        "task_id": "task_xxx",
        "status": "completed",
        "updated_at": "2026-03-31T10:00:00Z"
    }
}
```

### GET /api/v1/projects/{project_id}/risks
获取风险列表

**权限要求**
- project:read

**响应示例**
```json
{
    "success": true,
    "data": {
        "risks": [
            {
                "id": "risk_xxx",
                "level": "high",
                "description": "进度延迟风险",
                "status": "open",
                "owner": {
                    "user_id": "user_xxx",
                    "name": "张三"
                },
                "created_at": "2026-03-20T10:00:00Z"
            }
        ]
    }
}
```

### GET /api/v1/projects/{project_id}/costs
获取成本监控数据

**权限要求**
- cost:read

**响应示例**
```json
{
    "success": true,
    "data": {
        "budget": {
            "total": 1000000,
            "by_category": {
                "人力": 600000,
                "设备": 200000,
                "其他": 200000
            }
        },
        "actual": {
            "total": 450000,
            "by_category": {
                "人力": 300000,
                "设备": 100000,
                "其他": 50000
            }
        },
        "utilization_rate": 0.45,
        "remaining_budget": 550000
    }
}
```

## 五、管理API

### GET /api/v1/admin/skills
获取Skill列表

**权限要求**
- admin

**响应示例**
```json
{
    "success": true,
    "data": {
        "skills": [
            {
                "skill_name": "project_overview",
                "display_name": "项目总览",
                "description": "查看项目整体状态",
                "enabled": true
            }
        ]
    }
}
```

### GET /api/v1/admin/users
获取用户列表

**权限要求**
- admin

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| size | int | 否 | 每页数量 |

### POST /api/v1/admin/projects
创建项目

**权限要求**
- admin

**请求体**
```json
{
    "name": "新项目名称",
    "description": "项目描述",
    "pm_id": "user_xxx",
    "start_date": "2026-01-01",
    "end_date": "2026-06-30"
}
```

## 六、审计API

### GET /api/v1/audit/logs
获取审计日志

**权限要求**
- auditor

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 否 | 用户ID筛选 |
| project_id | string | 否 | 项目ID筛选 |
| action | string | 否 | 操作类型筛选 |
| start_time | string | 否 | 开始时间 |
| end_time | string | 否 | 结束时间 |
| page | int | 否 | 页码 |
| size | int | 否 | 每页数量 |

**响应示例**
```json
{
    "success": true,
    "data": {
        "logs": [
            {
                "id": "log_xxx",
                "user_id": "user_xxx",
                "project_id": "project_xxx",
                "action": "task_update",
                "resource": "task",
                "timestamp": "2026-03-31T10:00:00Z",
                "details": {
                    "task_id": "task_xxx",
                    "changes": {
                        "status": "completed"
                    }
                }
            }
        ],
        "total": 100,
        "page": 1,
        "size": 20
    }
}
```

## 七、错误码说明

| 错误码 | 说明 |
|--------|------|
| INVALID_REQUEST | 请求参数错误 |
| UNAUTHORIZED | 未授权 |
| PERMISSION_DENIED | 权限不足 |
| RESOURCE_NOT_FOUND | 资源不存在 |
| INTERNAL_ERROR | 内部错误 |
| LARK_SIGNATURE_INVALID | 飞书签名验证失败 |
| IDEMPOTENT_CHECK_FAILED | 幂等检查失败 |
| LLM_ERROR | LLM调用错误 |
| RAG_NO_ANSWER | RAG无答案 |
| TASK_TIMEOUT | 任务超时 |

## 八、API调用示例

### Python示例

```python
import httpx

async def get_project_overview(project_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://your-domain.com/api/v1/projects/{project_id}/overview",
            headers={"Authorization": "Bearer token"},
        )
        return response.json()
```

### cURL示例

```bash
curl -X GET \
  https://your-domain.com/api/v1/projects/project_xxx/overview \
  -H "Authorization: Bearer token"
```