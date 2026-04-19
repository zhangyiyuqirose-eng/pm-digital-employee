# 项目经理数字员工系统 - 飞书集成文档

## 一、飞书集成概述

项目经理数字员工系统以**飞书**为唯一交互入口，通过飞书开放平台API实现消息接收、事件处理、卡片交互等功能。

### 集成方式
- **消息接收**：Webhook接收用户消息
- **事件订阅**：接收飞书各类事件通知
- **卡片交互**：消息卡片回调处理
- **消息发送**：主动发送消息到飞书

## 二、飞书开放平台配置

### 1. 应用创建
在飞书开放平台创建自建应用：

| 配置项 | 说明 |
|--------|------|
| AppID | 应用唯一标识 |
| AppSecret | 应用密钥（用于签名） |
| EncryptKey | 消息加密密钥 |
| VerificationToken | 消息验证令牌 |

### 2. 权限配置
需要申请的权限：

| 权限名称 | 权限范围 | 用途 |
|----------|----------|------|
| im:message:send_as_bot | 发送消息 | 消息推送 |
| contact:user:read | 获取用户信息 | 用户识别 |
| contact:department:read | 获取部门信息 | 组织架构同步 |

### 3. 事件订阅
订阅的事件类型：

| 事件类型 | 说明 | 处理逻辑 |
|----------|------|----------|
| im.message.receive_v1 | 接收消息 | 意图识别→Skill执行 |
| im.chat.member.leave_v1 | 群成员退出 | 更新群-项目绑定 |
| im.chat.member.join_v1 | 群成员加入 | 更新群-项目绑定 |

### 4. Webhook配置
配置Webhook接收地址：

```
GET/POST https://your-domain.com/lark/webhook/event
POST https://your-domain.com/lark/callback/card
```

## 三、签名验签机制

### 1. 签名验证流程

飞书发送请求时会携带签名，服务端需要验证签名确保请求合法性：

```python
class LarkSignature:
    def verify(self, signature: str, timestamp: str, nonce: str, body: str) -> bool:
        # 构建签名串
        sign_str = f"{timestamp}{nonce}{body}"
        
        # SHA256计算
        expected_sig = hmac.new(
            settings.lark_encrypt_key.encode(),
            sign_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # 常量时间比较
        return secrets.compare_digest(expected_sig, signature)
```

### 2. 消息加解密

飞书使用AES-256-GCM加密消息：

```python
class LarkCrypto:
    def decrypt(self, encrypt_msg: str) -> str:
        # Base64解码
        decoded_data = base64.b64decode(encrypt_msg)
        
        # 提取IV和加密数据
        iv = decoded_data[:12]
        ciphertext = decoded_data[12:-16]
        auth_tag = decoded_data[-16:]
        
        # AES解密
        cipher = AES.new(settings.lark_encrypt_key.encode(), AES.MODE_GCM, iv)
        plaintext = cipher.decrypt_and_verify(ciphertext, auth_tag)
        
        return plaintext.decode("utf-8")
```

### 3. 签名验证中间件

```python
@app.middleware("http")
async def verify_lark_signature(request: Request, call_next):
    if request.url.path.startswith("/lark/"):
        # 获取请求体
        body = await request.body()
        timestamp = request.headers.get("X-Lark-Request-Timestamp")
        nonce = request.headers.get("X-Lark-Request-Nonce")
        signature = request.headers.get("X-Lark-Signature")
        
        if not LarkSignature().verify(signature, timestamp, nonce, body.decode()):
            return JSONResponse(
                status_code=403,
                content={"error": "Invalid signature"},
            )
    
    return await call_next(request)
```

## 四、消息处理流程

### 1. 消息接收

```python
@app.post("/lark/webhook/event")
async def receive_message(request: Request):
    # 1. 获取请求体
    body = await request.json()
    
    # 2. 签名验证
    timestamp = request.headers.get("X-Lark-Request-Timestamp")
    nonce = request.headers.get("X-Lark-Request-Nonce")
    signature = request.headers.get("X-Lark-Signature")
    raw_body = (await request.body()).decode()
    
    if not LarkSignature().verify(signature, timestamp, nonce, raw_body):
        raise InvalidSignatureError()
    
    # 3. 解析消息
    event = body.get("event", {})
    msg_type = event.get("message", {}).get("msg_type")
    content = event.get("message", {}).get("content")
    chat_id = event.get("message", {}).get("chat_id")
    user_id = event.get("sender", {}).get("user_id")
    
    # 4. 幂等检查
    msg_id = event.get("message", {}).get("message_id")
    if not await idempotency_service.check_and_lock(msg_id):
        return {"msg": "success"}  # 已处理
    
    # 5. 处理消息
    result = await message_dispatch_service.dispatch(
        user_id=user_id,
        content=content,
        msg_type=msg_type,
        chat_id=chat_id,
    )
    
    # 6. 发送响应
    if result:
        await send_message(user_id, result)
    
    return {"msg": "success"}
```

### 2. 消息类型处理

| 消息类型 | 处理方式 |
|----------|----------|
| text | 直接文本处理 |
| image | 图片下载后处理 |
| post | 富文本处理 |

## 五、卡片交互设计

### 1. 消息卡片示例

```json
{
  "config": {
    "wide_screen_mode": true,
    "enable_forward": true
  },
  "elements": [
    {
      "tag": "div",
      "text": {
        "tag": "lark_md",
        "content": "**项目周报**\n测试项目"
      }
    },
    {
      "tag": "div",
      "text": {
        "tag": "plain_text",
        "content": "项目进度：60%"
      }
    },
    {
      "tag": "action",
      "actions": [
        {
          "tag": "button",
          "text": {
            "tag": "plain_text",
            "content": "查看详情"
          },
          "type": "primary",
          "url": "https://example.com/project/123"
        }
      ]
    }
  ]
}
```

### 2. 按钮交互卡片

```json
{
  "config": {
    "wide_screen_mode": true
  },
  "header": {
    "template": "blue",
    "title": {
      "tag": "plain_text",
      "content": "请确认您的意图"
    }
  },
  "elements": [
    {
      "tag": "div",
      "text": {
        "tag": "lark_md",
        "content": "检测到您可能想要：项目周报"
      }
    },
    {
      "tag": "action",
      "actions": [
        {
          "tag": "button",
          "text": {
            "tag": "plain_text",
            "content": "确认执行"
          },
          "type": "primary"
        },
        {
          "tag": "button",
          "text": {
            "tag": "plain_text",
            "content": "取消"
          },
          "type": "default"
        }
      ]
    }
  ]
}
```

### 3. 卡片回调处理

```python
@app.post("/lark/callback/card")
async def handle_card_callback(request: Request):
    payload = await request.json()
    
    action_type = payload.get("action", {}).get("action_name", "")
    action_value = payload.get("action", {}).get("option", "")
    
    if action_type == "confirm":
        await handle_confirm(action_value)
    elif action_type == "cancel":
        await handle_cancel()
    
    return {"code": 0, "msg": "success"}
```

## 六、消息发送接口

### 1. 发送文本消息

```python
async def send_text_message(
    user_id: str,
    content: str,
) -> dict:
    return await lark_client.im.message.create(
        receive_id_type="user_id",
        body={
            "receive_id": user_id,
            "msg_type": "text",
            "content": json.dumps({"text": content}),
        },
    )
```

### 2. 发送富文本消息

```python
async def send_post_message(
    user_id: str,
    title: str,
    content: str,
) -> dict:
    return await lark_client.im.message.create(
        receive_id_type="user_id",
        body={
            "receive_id": user_id,
            "msg_type": "post",
            "content": json.dumps({
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": [[{"tag": "text", "text": content}]]
                    }
                }
            }),
        },
    )
```

### 3. 发送卡片消息

```python
async def send_interactive_card(
    user_id: str,
    card_content: dict,
) -> dict:
    return await lark_client.im.message.create(
        receive_id_type="user_id",
        body={
            "receive_id": user_id,
            "msg_type": "interactive",
            "content": json.dumps(card_content),
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
    is_active: bool   # 绑定是否有效
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
| 99991661 | access_token无效 | 刷新token |
| 99991663 | access_token过期 | 重新获取token |
| 300003 | 参数错误 | 校验参数 |

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
            if e.code in (99991661, 99991663):
                await refresh_access_token()
            if i < max_retries - 1:
                await asyncio.sleep(delay * (i + 1))
            else:
                raise
```

## 九、飞书集成最佳实践

### 1. 响应时效要求
飞书回调要求5秒内返回，超时会重试：
- 快速响应200状态码
- 长耗时任务异步执行
- 使用Celery处理耗时任务

### 2. 幂等处理
飞书可能重复发送事件：
- 使用message_id作为幂等键
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