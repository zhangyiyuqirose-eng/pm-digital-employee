# PM Digital Employee 部署指南

## 项目经理数字员工系统 - 飞书版

---

## 目录

1. [环境要求](#一环境要求)
2. [快速部署](#二快速部署)
3. [手动部署](#三手动部署)
4. [配置说明](#四配置说明)
5. [飞书配置](#五飞书配置)
6. [运维管理](#六运维管理)
7. [故障排查](#七故障排查)

---

## 一、环境要求

### 1.1 服务器要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 20GB | 50GB+ |
| 系统 | CentOS 7+ / Ubuntu 18.04+ | CentOS 8+ / Ubuntu 20.04+ |

### 1.2 软件要求

- Docker 20.10+
- Docker Compose 2.0+
- Git

### 1.3 网络要求

- 服务端口：8000（可配置）
- 公网访问：需要公网IP或域名
- HTTPS：生产环境必须使用HTTPS

---

## 二、快速部署

### 2.1 一键部署（推荐）

```bash
# 1. 克隆或上传代码到服务器
git clone <repository_url> /opt/pm-digital-employee
cd /opt/pm-digital-employee

# 2. 赋予执行权限
chmod +x deploy.sh update.sh manage.sh

# 3. 执行一键部署
./deploy.sh
```

### 2.2 配置飞书参数

```bash
# 编辑环境变量文件
vim .env

# 修改以下配置项：
# LARK_APP_ID=您的飞书应用AppID
# LARK_APP_SECRET=您的飞书应用Secret
# LARK_ENCRYPT_KEY=您设置的加密密钥
# LARK_VERIFICATION_TOKEN=您设置的验证令牌
```

### 2.3 重启服务

```bash
./manage.sh restart
```

---

## 三、手动部署

### 3.1 安装 Docker

```bash
# CentOS
yum install -y yum-utils
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum install -y docker-ce docker-ce-cli containerd.io
systemctl start docker
systemctl enable docker

# Ubuntu
apt-get update
apt-get install -y docker.io
systemctl start docker
systemctl enable docker
```

### 3.2 安装 Docker Compose

```bash
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 3.3 准备项目文件

```bash
# 创建项目目录
mkdir -p /opt/pm-digital-employee
cd /opt/pm-digital-employee

# 上传代码包（使用 scp 或其他方式）
# scp -r ./pm-digital-employee/* user@server:/opt/pm-digital-employee/

# 或者克隆代码
git clone <repository_url> .
```

### 3.4 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置
vim .env
```

### 3.5 启动服务

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f app
```

---

## 四、配置说明

### 4.1 环境变量说明

```bash
# 应用配置
APP_NAME=PM Digital Employee        # 应用名称
APP_ENV=production                  # 环境：development/production
APP_PORT=8000                       # 服务端口

# 数据库配置
POSTGRES_USER=pm_user               # 数据库用户
POSTGRES_PASSWORD=your_password     # 数据库密码（请修改）
POSTGRES_DB=pm_digital_employee     # 数据库名称
DATABASE_URL=postgresql+asyncpg://pm_user:your_password@postgres:5432/pm_digital_employee

# Redis配置
REDIS_URL=redis://:redis_password@redis:6379/0

# 飞书配置（必须配置）
LARK_APP_ID=                      # 飞书应用AppID
LARK_APP_SECRET=                  # 飞书应用Secret
LARK_ENCRYPT_KEY=                 # 事件加密密钥
LARK_VERIFICATION_TOKEN=          # 验证令牌

# LLM配置
LLM_PROVIDER=openai                 # LLM提供商
LLM_MODEL_NAME=gpt-4                # 模型名称
LLM_API_KEY=                        # API密钥
LLM_API_BASE=                       # API地址
```

### 4.2 端口配置

默认端口映射：
- 8000：FastAPI应用
- 5432：PostgreSQL（仅容器内部）
- 6379：Redis（仅容器内部）
- 5672：RabbitMQ（仅容器内部）

修改端口：
```yaml
# 编辑 docker-compose.yml
services:
  app:
    ports:
      - "你的端口:8000"
```

---

## 五、飞书配置

### 5.1 获取飞书参数

1. 登录飞书开放平台：https://open.feishu.cn/

2. 获取企业ID
   - 点击「我的企业」
   - 复制「企业ID」

3. 创建应用
   - 点击「应用管理」→「创建应用」
   - 填写应用信息
   - 获取 AgentID 和 Secret

4. 配置回调
   - 在应用详情页找到「设置API接收」
   - 填写URL：`https://your-domain.com/lark/webhook/event`
   - 设置Token和EncodingAESKey

### 5.2 回调URL配置

确保您的服务可以通过公网访问：

```bash
# 测试回调URL是否可访问
curl https://your-domain.com/health

# 应返回
{"status": "healthy", "lark_configured": true}
```

### 5.3 配置HTTPS（生产环境必须）

使用Nginx反向代理：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 六、运维管理

### 6.1 服务管理脚本

```bash
# 启动服务
./manage.sh start

# 停止服务
./manage.sh stop

# 重启服务
./manage.sh restart

# 查看日志
./manage.sh logs
./manage.sh logs app

# 查看状态
./manage.sh status

# 重新构建
./manage.sh build
```

### 6.2 更新部署

```bash
# 拉取最新代码并重新部署
./update.sh
```

### 6.3 查看日志

```bash
# 查看所有日志
docker-compose logs

# 实时查看应用日志
docker-compose logs -f app

# 查看最近100行日志
docker-compose logs --tail=100 app
```

### 6.4 数据备份

```bash
# 备份数据库
docker-compose exec postgres pg_dump -U pm_user pm_digital_employee > backup_$(date +%Y%m%d).sql

# 备份Redis
docker-compose exec redis redis-cli BGSAVE
```

### 6.5 数据恢复

```bash
# 恢复数据库
cat backup.sql | docker-compose exec -T postgres psql -U pm_user pm_digital_employee
```

---

## 七、故障排查

### 7.1 服务无法启动

```bash
# 检查容器状态
docker-compose ps

# 查看错误日志
docker-compose logs app

# 检查端口占用
netstat -tlnp | grep 8000

# 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 7.2 数据库连接失败

```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 检查数据库日志
docker-compose logs postgres

# 重置数据库（警告：会清空数据）
docker-compose down -v
docker-compose up -d
```

### 7.3 飞书回调失败

```bash
# 1. 检查服务是否可访问
curl http://localhost:8000/health

# 2. 检查飞书配置
cat .env | grep LARK

# 3. 查看回调日志
docker-compose logs app | grep lark

# 4. 检查签名验证
# 确保 Token 和 Encrypt Key 与飞书后台一致
```

### 7.4 内存不足

```bash
# 查看内存使用
docker stats

# 清理未使用的资源
docker system prune -a

# 重启服务
docker-compose restart
```

---

## 八、常用命令速查

| 操作 | 命令 |
|------|------|
| 启动服务 | `./manage.sh start` |
| 停止服务 | `./manage.sh stop` |
| 重启服务 | `./manage.sh restart` |
| 查看日志 | `./manage.sh logs` |
| 查看状态 | `./manage.sh status` |
| 更新部署 | `./update.sh` |
| 进入容器 | `docker-compose exec app bash` |
| 查看容器 | `docker-compose ps` |
| 清理资源 | `docker system prune -a` |

---

## 九、联系支持

如遇问题，请检查：
1. 服务日志
2. 飞书管理后台配置
3. 网络连通性
4. 配置文件正确性

---

**文档版本：** v1.0.0  
**更新日期：** 2026-03-31