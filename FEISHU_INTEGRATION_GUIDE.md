# PM数字员工系统飞书对接说明手册

## 一、前置准备

### 1.1 服务器环境要求
- 服务器一台（Linux/Windows均可）
- 至少4GB内存，推荐8GB+
- 至少20GB磁盘空间
- 需要有公网IP或域名
- 端口8000需要对外开放（或通过反向代理）

### 1.2 本地开发环境要求
- Python 3.11+
- Docker 20.10+
- Docker Compose 2.0+

## 二、本地部署

### 2.1 下载代码包

```bash
# 方式1: 使用git克隆
git clone <仓库地址> pm-digital-employee
cd pm-digital-employee

# 或者直接上传下载的代码包
tar -xzf pm-digital-employee-v1.0.0.tar.gz
cd pm-digital-employee-v1.0.0
```

### 2.2 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装Python依赖
pip install -r requirements.txt
```

### 2.3 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env
vim .env  # 编辑环境变量文件
```

主要配置项：
```bash
# 应用配置
APP_NAME=PM Digital Employee
APP_ENV=production
APP_PORT=8000

# 数据库配置（可按需修改）
POSTGRES_USER=pm_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=pm_digital_employee

# Redis配置（可按需修改）
REDIS_URL=redis://:redis_password@redis:6379/0

# 飞书配置（需要填入真实值）
LARK_APP_ID=cli_abc123  # 飞书应用AppID
LARK_APP_SECRET=your_app_secret  # 飞书应用密钥
LARK_ENCRYPT_KEY=your_encrypt_key  # 事件加密密钥
LARK_VERIFICATION_TOKEN=your_verification_token  # 验证令牌
LARK_APP_ROOT_DOMAIN=https://open.feishu.cn

# LLM配置（可先使用mock模式）
LLM_PROVIDER=mock
LLM_MODEL_NAME=gpt-4
LLM_API_KEY=
LLM_API_BASE=
```

### 2.4 使用Docker部署

```bash
# 构建并启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

### 2.5 验证本地服务

```bash
# 检查健康状态
curl http://localhost:8000/health

# 预期返回
{"status": "healthy", "lark_configured": true}
```

## 三、飞书开放平台配置

### 3.1 创建自建应用

1. 登录飞书开放平台：https://open.feishu.cn/
2. 点击右上角「创建应用」
3. 选择「自建应用」
4. 填写应用信息：
   - 应用名称：PM数字员工
   - 应用描述：项目经理智能助手
   - 应用图标：可上传logo图片
   - 分类：企业效率
5. 点击「确定」

### 3.2 获取应用凭证

在应用详情页面，点击左侧菜单「凭证与版本」：
- 记录 `App ID` - 这是你的 `LARK_APP_ID`
- 记录 `App Secret` - 这是你的 `LARK_APP_SECRET`

### 3.3 配置机器人权限

1. 在左侧菜单点击「机器人」
2. 点击「添加机器人」
3. 配置机器人信息：
   - 机器人名称：PM数字员工
   - 机器人头像：上传logo图片
   - 机器人描述：项目经理智能助手，可查询项目状态、生成周报、更新任务进度等
4. 保存配置

### 3.4 配置事件订阅

1. 在左侧菜单点击「事件订阅」
2. 填写「请求网址」：`https://your-domain.com/lark/webhook/event`
   - 注意：需要将 `your-domain.com` 替换为你的实际域名
   - 必须使用HTTPS协议
3. 填写「加密钥」：生成一个32位随机字符串，作为 `LARK_ENCRYPT_KEY`
4. 填写「验证令牌」：生成一个32位随机字符串，作为 `LARK_VERIFICATION_TOKEN`
5. 点击「保存」

### 3.5 选择事件

在「事件与回调」区域：
1. 点击「添加事件」
2. 搜索并选择以下事件：
   - `im.message.receive_v1` - 接收消息事件
3. 点击「保存」

### 3.6 配置IP白名单（如果需要）

在「安全配置」区域：
1. 如果你的服务器IP固定，可以在「IP白名单」中添加
2. 如果IP不固定，建议配置应用级别的安全策略

### 3.7 配置用户权限

在左侧菜单点击「用户权限」：
1. 开通「获取用户信息」权限
2. 开通「发送消息」权限
3. 开通「获取群信息」权限

### 3.8 发布应用

在左侧菜单点击「版本发布」：
1. 点击「创建版本」
2. 填写版本信息
3. 上传应用截图
4. 提交审核（如果需要在应用商店发布）
5. 或者选择「部署到企业」供内部使用

## 四、服务器配置

### 4.1 配置HTTPS（生产环境必需）

推荐使用Nginx反向代理：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;  # 替换为你的域名

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

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 4.2 验证回调URL

确保飞书能够成功访问你的回调URL：

```bash
# 在服务器上测试
curl -v https://your-domain.com/lark/webhook/event

# 应返回405 Method Not Allowed或其他HTTP状态码（而不是连接超时）
```

### 4.3 更新环境变量

更新 `.env` 文件中的飞书配置：

```bash
LARK_APP_ID=你的AppID
LARK_APP_SECRET=你的AppSecret
LARK_ENCRYPT_KEY=你的加密密钥
LARK_VERIFICATION_TOKEN=你的验证令牌
```

### 4.4 重启服务

```bash
# 重启Docker服务
docker-compose restart

# 或者重新构建并启动
docker-compose down
docker-compose up -d
```

## 五、飞书应用配置验证

### 5.1 测试事件订阅验证

1. 回到飞书开放平台的「事件订阅」页面
2. 点击「验证」按钮
3. 系统会向你的回调URL发送验证请求
4. 如果配置正确，应该看到验证成功的提示

### 5.2 发送测试消息

在飞书客户端中：
1. 打开机器人聊天窗口
2. 发送消息：`项目总览`
3. 等待机器人回复

## 六、功能测试

### 6.1 主要功能测试

1. **项目总览查询**
   - 消息：`项目总览`
   - 预期：返回项目整体状态、进度、里程碑、风险、成本等信息

2. **项目周报生成**
   - 消息：`生成本周周报`
   - 预期：自动生成并发送项目周报

3. **WBS自动生成**
   - 消息：`生成WBS`
   - 预期：根据项目信息生成工作分解结构

4. **任务进度更新**
   - 消息：`更新任务进度 任务ID 完成百分比`
   - 预期：更新指定任务的进度

5. **风险识别与预警**
   - 消息：`项目风险预警`
   - 预期：识别并展示项目风险信息

### 6.2 错误排查

如果功能不能正常工作，检查以下方面：

1. **服务状态**
   ```bash
   # 检查服务是否运行
   docker-compose ps
   
   # 查看日志
   docker-compose logs app
   ```

2. **网络连通性**
   ```bash
   # 检查端口是否开放
   netstat -tlnp | grep 8000
   
   # 检查域名解析
   nslookup your-domain.com
   ```

3. **SSL证书**
   ```bash
   # 检查SSL证书是否有效
   openssl s_client -connect your-domain.com:443
   ```

4. **防火墙配置**
   - 确保端口80和443对外开放
   - 确保服务器安全组允许相应端口访问

## 七、常见问题解答

### Q1: 事件订阅验证失败怎么办？
A: 检查：
1. 域名是否正确指向服务器
2. HTTPS证书是否有效
3. 端口8000上的服务是否正常运行
4. 飞书配置中的验证令牌和加密密钥是否与服务器配置一致

### Q2: 机器人不回复消息怎么办？
A: 检查：
1. 是否正确配置了 `im.message.receive_v1` 事件
2. 服务日志中是否有错误信息
3. 飞书机器人权限是否足够

### Q3: 如何更换LLM提供商？
A: 修改 `.env` 文件中的LLM配置：
```bash
# OpenAI
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key
LLM_API_BASE=https://api.openai.com/v1

# Azure OpenAI
LLM_PROVIDER=azure
LLM_API_KEY=your_azure_api_key
LLM_API_BASE=your_azure_endpoint
```

### Q4: 如何添加新项目？
A: 通过API或数据库直接添加项目记录，然后配置群-项目绑定关系。

## 八、日常运维

### 8.1 查看日志
```bash
# 查看应用日志
docker-compose logs -f app

# 查看最近100行日志
docker-compose logs --tail=100 app
```

### 8.2 备份数据
```bash
# 备份数据库
docker-compose exec postgres pg_dump -U pm_user pm_digital_employee > backup_$(date +%Y%m%d).sql

# 备份Redis
docker-compose exec redis redis-cli BGSAVE
```

### 8.3 更新系统
```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build --no-cache

# 重启服务
docker-compose up -d
```

通过以上步骤，您应该能够在飞书上成功部署和使用PM数字员工系统。如遇到问题，请检查配置文件和日志信息，确保所有配置项都正确设置。