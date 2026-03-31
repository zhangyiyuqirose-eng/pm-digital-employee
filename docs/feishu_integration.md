# 项目经理数字员工系统 - 飞书集成文档

## 一、飞书集成概述

项目经理数字员工系统以飞书为唯一交互入口，通过飞书开放平台API实现消息接收、事件处理、卡片交互等功能。

### 集成方式
- **消息接收**：Webhook接收用户消息
- **事件订阅**：接收飞书各类事件通知
- **卡片交互**：交互式卡片回调处理
- **消息发送**：主动发送消息到飞书

## 二、飞书开放平台配置

### 1. 应用创建
在飞书开放平台创建企业自建应用：

| 配置项 | 说明 |
|--------|------|
| App ID | 应用唯一标识 |
| App Secret | 应用密钥（用于签名） |
| Verification Token | 事件验证令牌 |
| Encrypt Key | 消息加密密钥（可选） |

### 2. 权限配置
需要申请的权限：

| 权限名称 | 权限范围 | 用途 |
|----------|----------|------|
| im:message | 接收和发送消息 | 消息交互 |
| im:message:send_as_bot | 以机器人身份发送消息 | 主动发消息 |
| contact:user.base:readonly | 获取用户基本信息 | 用户识别 |
| contact:user.id:readonly | 获取用户ID | 用户绑定 |

### 3. 事件订阅
订阅的事件类型：

| 事件类型 | 说明 | 处理逻辑 |
|----------|------|----------|
| im.message.receive_v1 | 接收消息 | 意图识别→Skill执行 |
| im.message.message_read_v1 | 消息已读 | 更新已读状态 |

### 4. Webhook配置
配置Webhook接收地址：

```
POST https://your-domain.com/lark/webhook/message
POST https://your-domain.com/lark/webhook/event
POST https://your-domain.com/lark/callback/card
POST https://your-domain.com/lark/url_verification
```

## 三、签名验签机制

### 1. 签名验证流程

飞书发送请求时会携带签名，服务端需要验证签名确保请求合法性：

```python
class LarkSignature:
    def verify(self, headers: Dict[str, str], body: bytes) -> bool:
        timestamp = headers.get("X-Lark-Request-Timestamp")
        nonce = headers.get("X-Lark-Request-Nonce")
        signature = headers.get("X-Lark-Signature")
        
        # 时间戳校验（防止重放攻击）
        now = int(time.time())
        if abs(now - int(timestamp)) > 300:
            return False
        
        # 构建签名串
        sign_str = timestamp + nonce + self.app_secret + body.decode()
        
        # SHA256计算
        expected_sig = hashlib.sha256(sign_str.encode()).hexdigest()
        
        return signature == expected_sig
```

### 2. 签名验证中间件

```python
@app.middleware("http")
async def verify_lark_signature(request: Request, call_next):
    if request.url.path.startswith("/lark/"):
        headers = dict(request.headers)
        body = await request.body()
        
        if not LarkSignature().verify(headers, body):
            return JSONResponse(
                status_code=403,
                content={"error": "Invalid signature"},
            )
    
    return await call_next(request)
```

## 四、消息处理流程

### 1. 消息接收

```python
@app.post("/lark/webhook/message")
async def receive_message(request: Request):
    # 1. 签名验证
    headers = dict(request.headers)
    body = await request.body()
    
    if not verify_signature(headers, body):
        raise InvalidSignatureError()
    
    # 2. 解析消息
    payload = await request.json()
    message = parse_message_payload(payload)
    
    # 3. 幂等检查
    event_id = payload["header"]["event_id"]
    if not await idempotency_service.check_and_lock(event_id):
        return {"status": "duplicate"}
    
    # 4. 处理消息
    result = await message_dispatch_service.dispatch(
        user_id=message.user_id,
        chat_id=message.chat_id,
        content=message.content,
        message_type=message.message_type,
    )
    
    # 5. 发送响应
    await send_message(chat_id, result)
    
    return {"status": "ok"}
```

### 2. 消息类型处理

| 消息类型 | 处理方式 |
|----------|----------|
| text | 直接文本处理 |
| image | OCR识别后处理 |
| file | 文件解析后处理 |
| post | 富文本解析 |
| interactive | 卡片回调处理 |

## 五、卡片交互设计

### 1. 卡片模板示例

```json
{
  "type": "template",
  "data": {
    "template_id": "AAqk218N",
    "template_variable": {
      "title": "项目周报",
      "project_name": "测试项目",
      "status": "进行中",
      "progress": "60%",
      "risks": [
        {"level": "high", "desc": "进度延迟风险"}
      ]
    }
  }
}
```

### 2. 卡片回调处理

```python
@app.post("/lark/callback/card")
async def handle_card_callback(request: Request):
    payload = await request.json()
    
    action = payload["action"]["value"]
    action_type = action["action_type"]
    
    if action_type == "approve":
        await handle_approval(action["approval_id"])
    elif action_type == "view_detail":
        await send_detail_card(action["project_id"])
    
    return {"status": "ok"}
```

### 3. 卡片类型

| 卡片类型 | 用途 | 示例场景 |
|----------|------|----------|
| ProjectOverviewCard | 项目总览 | 查看项目状态 |
| RiskAlertCard | 风险预警 | 显示风险详情 |
| WeeklyReportCard | 周报展示 | 展示周报内容 |
| ClarificationCard | 澄清确认 | 多轮补参 |
| TaskUpdateCard | 任务更新 | 更新任务进度 |
| ApprovalStatusCard | 审批状态 | 显示审批流程 |

## 六、消息发送接口

### 1. 发送文本消息

```python
async def send_text_message(
    receive_id: str,
    receive_type: str,
    content: str,
) -> dict:
    return await lark_client.post(
        "/im/v1/messages",
        params={
            "receive_id_type": receive_type,
        },
        json={
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": content}),
        },
    )
```

### 2. 发送卡片消息

```python
async def send_card_message(
    receive_id: str,
    receive_type: str,
    card_content: dict,
) -> dict:
    return await lark_client.post(
        "/im/v1/messages",
        params={
            "receive_id_type": receive_type,
        },
        json={
            "receive_id": receive_id,
            "msg_type": "interactive",
            "content": json.dumps(card_content),
        },
    )
```

### 3. 发送文件消息

```python
async def send_file_message(
    receive_id: str,
    receive_type: str,
    file_key: str,
    file_name: str,
) -> dict:
    return await lark_client.post(
        "/im/v1/messages",
        params={
            "receive_id_type": receive_type,
        },
        json={
            "receive_id": receive_id,
            "msg_type": "file",
            "content": json.dumps({
                "file_key": file_key,
                "file_name": file_name,
            }),
        },
    )
```

## 七、群-项目绑定机制

### 1. 绑定逻辑

飞书群与项目建立绑定关系，群内消息自动关联到对应项目：

```python
class GroupProjectBinding:
    chat_id: str      # 飞书群ID
    project_id: str   # 项目ID
    bind_type: str    # primary/secondary
```

### 2. 消息处理时的项目识别

```python
async def resolve_project_context(
    user_id: str,
    chat_id: str,
) -> str:
    # 群消息：通过群绑定获取项目
    if chat_id:
        binding = await group_binding_repo.get_by_chat_id(chat_id)
        if binding:
            return binding.project_id
    
    # 单聊：通过用户默认项目获取
    default_project = await user_repo.get_default_project(user_id)
    if default_project:
        return default_project
    
    # 需要用户指定项目
    return None
```

## 八、错误处理与重试

### 1. 飞书API错误码

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| 99991663 | token过期 | 刷新token |
| 99991664 | token无效 | 重新获取token |
| 99991400 | 参数错误 | 校验参数 |

### 2. 重试策略

```python
async def call_with_retry(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
):
    for i in range(max_retries):
        try:
            return await func()
        except LarkAPIError as e:
            if e.code == TOKEN_EXPIRED:
                await refresh_token()
            if i < max_retries - 1:
                await asyncio.sleep(delay * (i + 1))
            else:
                raise
```

## 九、飞书集成最佳实践

### 1. 响应时效要求
飞书回调要求1秒内返回，超时会重试：
- 快速响应200状态码
- 长耗时任务异步执行
- 使用Celery处理耗时任务

### 2. 幂等处理
飞书可能重复发送事件：
- 使用event_id作为幂等键
- Redis存储处理状态
- TTL设置为1小时

### 3. 用户隐私保护
- 不存储用户敏感信息
- 消息内容加密存储
- 数据脱敏展示

### 4. 监控与告警
- Webhook响应时间监控
- 消息处理成功率监控
- API调用失败告警