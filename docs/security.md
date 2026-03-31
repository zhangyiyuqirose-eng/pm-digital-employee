# 项目经理数字员工系统 - 安全合规文档

## 一、安全架构概述

本系统遵循金融级安全标准，采用多层次安全防护策略，确保数据安全、用户隐私和系统稳定性。

### 安全设计原则
1. **默认拒绝**：所有权限检查采用"默认拒绝，显式允许"
2. **项目隔离**：所有数据查询强制携带project_id，防止跨项目数据泄露
3. **最小权限**：用户只能访问其授权范围内的数据和功能
4. **审计留痕**：所有操作记录审计日志，可追溯可审计
5. **内容安全**：输入输出内容经过安全检测和合规校验

## 二、安全模块设计

### 1. 输入校验模块（InputValidator）

#### SQL注入防护
```python
SQL_INJECTION_PATTERNS = [
    r"(?i)(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b)",
    r"(?i)(\b(UNION|JOIN)\b.*\b(SELECT|FROM)\b)",
    r"(--|#|/\*|\*/)",
    r"(?i)(\b(OR|AND)\b.*=)",
]
```

#### XSS防护
```python
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe",
]
```

#### 输入净化
```python
def sanitize_input(input_string: str, max_length: int = 10000) -> str:
    # 截断长度
    sanitized = input_string[:max_length]
    # 移除危险字符
    sanitized = re.sub(r"<[^>]*>", "", sanitized)
    return sanitized
```

### 2. 数据脱敏模块（DataMasker）

#### 脱敏规则
| 数据类型 | 脱敏规则 | 示例 |
|----------|----------|------|
| 手机号 | 保留前3后4 | 138****5678 |
| 身份证 | 保留前6后4 | 123456****3456 |
| 银行卡 | 保留前4后4 | 1234****5678 |
| 邮箱 | 保留前2字符 | te***@example.com |

#### 自动脱敏
```python
def auto_mask(text: str) -> str:
    # 自动识别并脱敏文本中的敏感信息
    result = text
    result = phone_pattern.sub(lambda m: mask_phone(m.group()), result)
    result = id_pattern.sub(lambda m: mask_id_card(m.group()), result)
    return result
```

### 3. 内容合规检查模块（ContentComplianceChecker）

#### 敏感词检测
- 政治敏感词
- 违禁词
- 行业特定敏感词

```python
def check(content: str) -> Dict[str, Any]:
    violations = []
    for word in SENSITIVE_WORDS:
        if word in content:
            violations.append(f"包含敏感词: {word}")
    return {
        "is_compliant": len(violations) == 0,
        "violations": violations,
    }
```

### 4. 提示词注入防护模块（PromptInjectionGuard）

#### 注入模式检测
```python
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+(instructions?|prompts?)",
    r"(show|reveal|display)\s+(your|the)\s+(prompt|instructions?)",
    r"(you\s+are|act\s+as|pretend)",
    r"(bypass|override|disable)\s+(restrictions?|filters?)",
]
```

#### 风险等级
- **Low**：未检测到注入模式
- **Medium**：检测到可疑模式
- **High**：检测到明确注入尝试

## 三、权限控制设计

### 1. 项目级隔离

#### Repository层强制过滤
```python
class TaskRepository(BaseRepository):
    async def find_by_project(
        self,
        project_id: str,
        status: Optional[str] = None,
    ) -> List[Task]:
        # 强制project_id过滤
        query = select(Task).where(Task.project_id == project_id)
        if status:
            query = query.where(Task.status == status)
        return await self.session.execute(query)
```

#### Service层权限校验
```python
class TaskService:
    async def get_task(
        self,
        task_id: str,
        user_id: str,
        project_id: str,
    ) -> Task:
        # 权限校验
        if not await self.access_control.check_project_access(
            user_id, project_id, "read"
        ):
            raise PermissionDeniedError()
        
        # 数据隔离
        return await self.task_repo.get_by_id(task_id, project_id)
```

### 2. 角色权限矩阵

| 角色 | 项目访问 | 任务管理 | 成本查看 | 风险管理 | 系统管理 |
|------|----------|----------|----------|----------|----------|
| admin | 全部 | 全部 | 全部 | 全部 | 全部 |
| project_manager | 所属项目 | 所属项目 | 所属项目 | 所属项目 | 无 |
| pm | 所属项目 | 所属项目 | 所属项目 | 所属项目 | 无 |
| tech_lead | 所属项目 | 所属项目 | 无 | 所属项目 | 无 |
| member | 所属项目 | 本人任务 | 无 | 无 | 无 |
| auditor | 全部 | 无 | 全部 | 全部 | 无 |

### 3. Skill权限校验

```python
class SkillRegistry:
    def get_available_skills(
        self,
        user_role: str,
        project_permissions: List[str],
    ) -> List[BaseSkill]:
        available = []
        for skill in self._skills.values():
            manifest = skill.get_manifest()
            # 检查角色权限
            if user_role in manifest["allowed_roles"]:
                # 检查功能权限
                if self._check_permissions(
                    manifest["required_permissions"],
                    project_permissions,
                ):
                    available.append(skill)
        return available
```

## 四、飞书安全集成

### 1. 签名验签

```python
class LarkSignature:
    def verify(
        self,
        headers: Dict[str, str],
        body: bytes,
    ) -> bool:
        timestamp = headers["X-Lark-Request-Timestamp"]
        nonce = headers["X-Lark-Request-Nonce"]
        signature = headers["X-Lark-Signature"]
        
        # 构建签名串
        sign_str = f"{timestamp}{nonce}{self.app_secret}{body.decode()}"
        
        # 计算签名
        expected_sig = sha256(sign_str.encode()).hexdigest()
        
        return signature == expected_sig
```

### 2. 幂等控制

```python
class IdempotencyService:
    async def check_and_lock(
        self,
        event_id: str,
        ttl: int = 3600,
    ) -> bool:
        # Redis SETNX实现幂等锁
        key = f"idempotent:{event_id}"
        result = await self.redis.set(key, "1", nx=True, ex=ttl)
        return result is not None
```

### 3. URL校验

```python
@app.post("/lark/url_verification")
async def url_verification(request: Request):
    data = await request.json()
    if data["token"] != settings.LARK_VERIFICATION_TOKEN:
        raise InvalidTokenError()
    return {"challenge": data["challenge"]}
```

## 五、审计日志设计

### 1. 审计日志字段

| 字段 | 说明 | 示例 |
|------|------|------|
| id | 日志ID | uuid |
| user_id | 操作用户 | user_123 |
| project_id | 项目ID | project_001 |
| action | 操作类型 | task_update |
| resource | 资源类型 | task |
| trace_id | 追踪ID | trace_uuid |
| ip_address | IP地址 | 192.168.1.1 |
| timestamp | 时间戳 | 2026-03-31T10:00:00Z |
| details | 详细信息 | JSON |

### 2. 审计记录示例

```python
async def log_audit(
    user_id: str,
    project_id: str,
    action: str,
    resource: str,
    details: Dict[str, Any],
):
    await AuditLogRepository.create({
        "user_id": user_id,
        "project_id": project_id,
        "action": action,
        "resource": resource,
        "trace_id": get_trace_id(),
        "details": details,
        "timestamp": datetime.now(timezone.utc),
    })
```

## 六、数据安全要求

### 1. 数据存储安全
- PostgreSQL数据库加密存储
- Redis缓存数据不持久化敏感信息
- 日志文件不含敏感数据

### 2. 数据传输安全
- HTTPS加密传输
- API签名验证
- 内部服务通信加密

### 3. 数据备份安全
- 定期备份
- 备份加密
- 异地存储

## 七、合规要求

### 1. 金融合规
- 符合《银行业金融机构数据治理指引》
- 符合《个人信息保护法》要求
- 符合《网络安全法》要求

### 2. 数据分类分级
- 一级数据：公开数据
- 二级数据：内部数据
- 三级数据：敏感数据
- 四级数据：核心数据

### 3. 数据生命周期管理
- 数据采集：最小必要原则
- 数据存储：分类分级存储
- 数据使用：授权使用
- 数据销毁：安全销毁

## 八、安全运维要求

### 1. 安全监控
- 异常访问监控
- 敏感操作监控
- 系统漏洞扫描

### 2. 安全响应
- 安全事件响应流程
- 数据泄露应急预案
- 系统恢复预案

### 3. 安全审计
- 定期安全审计
- 权限审计
- 日志审计