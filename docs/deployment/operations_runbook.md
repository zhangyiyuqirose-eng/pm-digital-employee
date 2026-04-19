# 项目经理数字员工系统 - 运维手册

## 一、系统部署

### 1. 环境准备

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.11+ | 运行环境 |
| PostgreSQL | 15+ | 主数据库 |
| Redis | 7+ | 缓存/会话 |
| RabbitMQ | 3+ | 消息队列 |
| Docker | 20+ | 容器化部署 |

### 2. Docker Compose部署

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: pm_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: pm_digital_employee
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pm_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  rabbitmq:
    image: rabbitmq:3-management
    environment:
      RABBITMQ_DEFAULT_USER: pm_user
      RABBITMQ_DEFAULT_PASS: ${MQ_PASSWORD}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

  app:
    build: .
    environment:
      DATABASE_URL: postgresql+asyncpg://pm_user:${DB_PASSWORD}@postgres:5432/pm_digital_employee
      REDIS_URL: redis://redis:6379/0
      RABBITMQ_URL: amqp://pm_user:${MQ_PASSWORD}@rabbitmq:5672/
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"

  celery_worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://pm_user:${DB_PASSWORD}@postgres:5432/pm_digital_employee
      REDIS_URL: redis://redis:6379/0
      RABBITMQ_URL: amqp://pm_user:${MQ_PASSWORD}@rabbitmq:5672/
    depends_on:
      - postgres
      - redis
      - rabbitmq

  celery_beat:
    build: .
    command: celery -A app.tasks.celery_app beat --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://pm_user:${DB_PASSWORD}@postgres:5432/pm_digital_employee
      REDIS_URL: redis://redis:6379/0
      RABBITMQ_URL: amqp://pm_user:${MQ_PASSWORD}@rabbitmq:5672/
    depends_on:
      - postgres
      - redis
      - rabbitmq

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:
```

### 3. 启动命令

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down
```

## 二、数据库管理

### 1. 数据库迁移

```bash
# 生成迁移脚本
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history
```

### 2. 数据库备份

```bash
# 手动备份
docker exec postgres pg_dump -U pm_user pm_digital_employee > backup.sql

# 定时备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec postgres pg_dump -U pm_user pm_digital_employee > /backup/pm_$DATE.sql
find /backup -name "pm_*.sql" -mtime +30 -delete
```

### 3. 数据库恢复

```bash
# 恢复数据
docker exec -i postgres psql -U pm_user pm_digital_employee < backup.sql
```

## 三、监控与告警

### 1. 健康检查

```bash
# 应用健康检查
curl http://localhost:8000/health

# 数据库健康检查
docker exec postgres pg_isready -U pm_user

# Redis健康检查
docker exec redis redis-cli ping

# RabbitMQ健康检查
docker exec rabbitmq rabbitmqctl status
```

### 2. Prometheus指标

应用暴露以下指标：

| 指标名称 | 说明 |
|----------|------|
| http_requests_total | HTTP请求总数 |
| http_request_duration_seconds | 请求耗时 |
| skill_executions_total | Skill执行总数 |
| skill_execution_duration_seconds | Skill执行耗时 |
| llm_calls_total | LLM调用总数 |
| llm_call_duration_seconds | LLM调用耗时 |
| rag_queries_total | RAG查询总数 |

### 3. 日志监控

```bash
# 应用日志
docker-compose logs -f app

# Celery日志
docker-compose logs -f celery_worker

# 错误日志过滤
docker-compose logs app | grep ERROR
```

### 4. 告警配置

建议配置以下告警：

| 告警类型 | 条件 | 优先级 |
|----------|------|--------|
| 服务宕机 | health check失败 | P0 |
| 高延迟 | API响应>5s | P1 |
| 高错误率 | 错误率>5% | P1 |
| 数据库连接失败 | 连接池耗尽 | P0 |
| Redis连接失败 | 连接超时 | P1 |
| Celery任务堆积 | 待处理任务>1000 | P2 |

## 四、性能调优

### 1. 应用层调优

```python
# gunicorn配置
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
timeout = 30
keepalive = 2
```

### 2. 数据库调优

```sql
-- PostgreSQL配置优化
shared_buffers = 256MB
effective_cache_size = 1GB
max_connections = 100
work_mem = 4MB
```

### 3. Redis调优

```conf
# Redis配置优化
maxmemory 1gb
maxmemory-policy allkeys-lru
timeout 300
```

### 4. Celery调优

```python
# Celery配置优化
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_BROKER_POOL_LIMIT = 10
```

## 五、故障排查

### 1. 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 服务无法启动 | 配置错误 | 检查环境变量 |
| 数据库连接失败 | 连接池耗尽 | 增加连接数 |
| API响应超时 | LLM调用慢 | 异步执行 |
| Celery任务不执行 | Worker未启动 | 检查Worker状态 |
| Redis连接失败 | 内存不足 | 增加内存 |

### 2. 日志分析

```bash
# 查找错误日志
grep -r "ERROR" /var/log/pm/

# 查找特定trace_id
grep "trace_id=xxx" /var/log/pm/

# 统计错误类型
grep "ERROR" /var/log/pm/ | awk '{print $5}' | sort | uniq -c
```

### 3. 性能分析

```bash
# API性能分析
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# 数据库查询分析
docker exec postgres psql -U pm_user -d pm_digital_employee -c "SELECT * FROM pg_stat_activity;"
```

## 六、安全运维

### 1. 访问控制

- 限制API访问IP
- 配置防火墙规则
- 启用HTTPS

### 2. 密钥管理

- 使用环境变量存储密钥
- 定期更换密钥
- 密钥加密存储

### 3. 数据安全

- 数据库访问控制
- 日志脱敏
- 定期数据备份

### 4. 安全审计

- 定期审计日志
- 权限审计
- 安全漏洞扫描

## 七、版本升级

### 1. 升级流程

```bash
# 1. 备份数据
./scripts/backup_database.sh

# 2. 拉取新版本
git pull origin main

# 3. 更新依赖
pip install -r requirements.txt

# 4. 数据库迁移
alembic upgrade head

# 5. 重启服务
docker-compose restart app
```

### 2. 回滚流程

```bash
# 1. 停止服务
docker-compose stop app

# 2. 回滚代码
git checkout previous_version

# 3. 回滚数据库
alembic downgrade -1

# 4. 恢复数据备份
./scripts/restore_database.sh backup_file.sql

# 5. 重启服务
docker-compose start app
```

## 八、日常运维任务

### 1. 每日任务
- 检查服务健康状态
- 查看错误日志
- 监控资源使用

### 2. 每周任务
- 清理过期数据
- 检查Celery任务堆积
- 审计日志分析

### 3. 每月任务
- 数据库备份清理
- 性能报告分析
- 安全审计报告