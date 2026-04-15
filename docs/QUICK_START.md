# PM Digital Employee 快速启动指南

## 项目经理数字员工系统 - 飞书版

---

## 一、系统概述

本系统为国有大型银行科技子公司项目管理部设计的AI数字员工，以飞书为唯一用户交互入口，提供10项核心项目管理功能。

### 核心功能
1. 项目总览查询
2. 项目周报生成
3. WBS自动生成
4. 任务进度更新
5. 风险识别与预警
6. 成本监控
7. 项目制度规范答疑（RAG）
8. 项目情况咨询
9. 会议纪要生成
10. 预立项/立项材料合规初审

---

## 二、环境要求

### 服务器配置
| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 20GB | 50GB+ |
| 系统 | CentOS 7+/Ubuntu 18.04+ | CentOS 8+/Ubuntu 20.04+ |

### 软件要求
- Docker 20.10+
- Docker Compose 2.0+
- Git

### 网络要求
- 公网IP或域名（用于飞书回调）
- HTTPS（生产环境必须）

---

## 三、快速部署流程

### 步骤1：上传代码包

```bash
# 使用scp上传到服务器
scp pm-digital-employee-v1.0.0.tar.gz user@server:/opt/
```

### 步骤2：解压代码包

```bash
ssh user@server
cd /opt
tar -xzf pm-digital-employee-v1.0.0.tar.gz
cd pm-digital-employee-v1.0.0
```

### 步骤3：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
vim .env
```

**必须修改的配置项：**
```bash
# 飞书配置（必填）
LARK_APP_ID=您的应用AppID
LARK_APP_SECRET=您的应用Secret
LARK_ENCRYPT_KEY=您的加密密钥
LARK_VERIFICATION_TOKEN=您的验证令牌

# 数据库密码（建议修改）
POSTGRES_PASSWORD=新密码
REDIS_PASSWORD=新密码
RABBITMQ_PASSWORD=新密码
```

### 步骤4：一键部署

```bash
# 执行一键部署脚本
./deploy.sh
```

部署脚本将自动完成：
- 安装Docker和Docker Compose
- 构建应用镜像
- 启动所有服务（PostgreSQL、Redis、RabbitMQ、App、Celery）

### 步骤5：验证部署

```bash
# 查看服务状态
./manage.sh status

# 健康检查
curl http://localhost:8000/health

# 查看日志
./manage.sh logs app
```

---

## 四、飞书配置

### 4.1 获取飞书参数

1. 登录飞书开放平台：https://open.feishu.cn/

2. **创建应用**
   - 点击「创建应用」
   - 选择「自建应用」
   - 填写应用名称：PM数字员工
   - 上传应用Logo
   - 进入应用详情页获取AppID和AppSecret

3. **配置回调**
   - 在应用详情页找到「事件订阅」
   - 填写请求网址：`https://your-domain.com/lark/webhook/event`
   - 设置Verification Token和Encrypt Key（需与.env中一致）
   - 订阅事件：im.message.receive_v1（消息接收事件）
   - 点击保存并发布

4. **配置权限**
   - 在「权限管理」中添加所需权限：
     - im:message:send_as_bot（发送消息给用户）
     - contact:user:read（获取用户信息）

### 4.2 设置可信域名

1. 在「凭证与基础信息」中配置应用域名
2. 添加服务器域名作为可信域名

### 4.3 设置可见范围

1. 在应用管理页面设置应用可见范围
2. 添加项目管理部成员
3. 选择对应部门

---

## 五、HTTPS配置（生产环境）

使用Nginx反向代理配置HTTPS：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 六、常用运维命令

| 操作 | 命令 |
|------|------|
| 启动服务 | `./manage.sh start` |
| 停止服务 | `./manage.sh stop` |
| 重启服务 | `./manage.sh restart` |
| 查看日志 | `./manage.sh logs` |
| 查看应用日志 | `./manage.sh logs app` |
| 查看状态 | `./manage.sh status` |
| 更新部署 | `./update.sh` |
| 进入容器 | `docker-compose exec app bash` |

---

## 七、故障排查

### 服务无法启动

```bash
# 检查容器状态
docker-compose ps

# 查看错误日志
docker-compose logs app

# 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 飞书回调失败

```bash
# 1. 检查服务是否可访问
curl http://localhost:8000/health

# 2. 检查飞书配置
cat .env | grep LARK

# 3. 查看回调日志
docker-compose logs app | grep lark

# 4. 验证签名配置是否一致
```

### 数据库连接失败

```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 查看数据库日志
docker-compose logs postgres
```

---

## 八、访问地址

| 资源 | 地址 |
|------|------|
| 健康检查 | http://localhost:8000/health |
| API文档 | http://localhost:8000/docs |
| ReDoc文档 | http://localhost:8000/redoc |
| 飞书回调 | https://your-domain.com/lark/webhook/event |
| RabbitMQ管理 | http://localhost:15672 |

---

## 九、下一步操作

1. 配置飞书开放平台的回调URL
2. 在飞书中添加机器人到项目群
3. 测试发送消息验证功能
4. 配置项目-群绑定关系

---

**详细部署文档：** DEPLOYMENT.md  
**飞书集成：** docs/lark_integration.md  
**版本信息：** VERSION.txt

---

**文档版本：** v1.0.0  
**更新日期：** 2026-03-31