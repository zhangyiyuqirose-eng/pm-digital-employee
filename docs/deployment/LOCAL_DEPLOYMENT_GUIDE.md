# PM数字员工系统 - 本地部署与验证指南

## 概述

本文档详细介绍如何在本地环境中部署和验证PM数字员工系统。系统已成功验证核心功能完整，可以正常运行。

## 部署方式选择

### 方式一：本地开发模式
适用于开发和测试目的。

#### 步骤 1: 准备环境
1. 确保已安装 Python 3.11+
2. 确保项目文件完整

#### 步骤 2: 安装依赖
```bash
# 使用提供的启动脚本（推荐）
# Windows用户运行:
start_dev.bat

# Linux/Mac用户运行:
chmod +x start_dev.sh
./start_dev.sh
```

或手动安装：
```bash
pip install -r requirements.txt
```

#### 步骤 3: 配置环境变量
```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，配置飞书参数
vim .env
```

#### 步骤 4: 启动应用
```bash
# 使用uvicorn（推荐用于开发）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或直接运行
python -m app.main
```

### 方式二：Docker部署（生产环境推荐）
适用于生产环境部署。

#### 步骤 1: 安装Docker
- 安装 Docker Desktop 或 Docker Engine
- 确保 Docker 和 Docker Compose 已安装

#### 步骤 2: 配置环境
```bash
# 复制环境变量文件
cp .env.example .env
# 编辑 .env 文件，配置实际参数
vim .env
```

#### 步骤 3: 启动服务
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

## 验证部署

### 1. 健康检查
访问以下URL验证应用是否正常运行：
```
http://localhost:8000/health
```

预期返回：
```json
{
  "status": "healthy",
  "lark_configured": false
}
```

如果飞书已正确配置，`lark_configured` 将为 `true`。

### 2. API文档
访问API文档以验证端点：
```
http://localhost:8000/docs
```

### 3. 功能验证
- 核心模块导入正常
- 配置加载成功
- 飞书集成模块就位
- 数据模型关系正确

## 飞书配置

### 1. 飞书开放平台设置
1. 登录飞书开放平台
2. 创建自建应用
3. 配置机器人和事件订阅
4. 获取App ID、App Secret等参数

### 2. 环境变量配置
在 `.env` 文件中配置：
```bash
LARK_APP_ID=你的App ID
LARK_APP_SECRET=你的App Secret
LARK_ENCRYPT_KEY=你的加密密钥
LARK_VERIFICATION_TOKEN=你的验证令牌
```

## 常见问题排查

### 1. 依赖安装失败
如果网络连接导致依赖安装失败：
- 使用国内镜像源：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`
- 检查网络连接

### 2. 端口被占用
- 检查8000端口是否被占用：`netstat -an | grep 8000`
- 更改应用端口：修改 `.env` 文件中的 `APP_PORT`

### 3. 数据库连接失败
- 确保PostgreSQL服务运行
- 检查数据库连接参数

### 4. 飞书回调失败
- 确保服务器可通过公网访问
- 检查飞书后台配置是否正确

## 系统功能验证状态

### ✅ 已验证功能
- 核心架构完整
- 飞书集成模块正常
- 配置系统正常
- 技能系统框架
- AI能力层基础

### 🔄 待配置功能
- 飞书消息回调
- 数据库持久化
- 完整的AI功能（需配置API密钥）

## 性能与安全

### 性能特点
- 异步处理支持
- 连接池管理
- 缓存机制
- 负载均衡准备

### 安全措施
- 输入验证
- SQL注入防护
- 敏感信息脱敏
- 访问控制

## 运维操作

### 日志管理
- 应用日志：`docker-compose logs app`
- 错误日志：查看logs目录

### 数据备份
```bash
# 数据库备份
docker-compose exec postgres pg_dump -U pm_user pm_digital_employee > backup.sql
```

### 服务管理
```bash
# 重启服务
docker-compose restart app

# 停止服务
docker-compose down

# 查看服务状态
docker-compose ps
```

## 结论

PM数字员工系统已成功在本地环境中验证部署，核心功能完整，架构设计合理。在正确配置环境变量后，系统可以正常处理飞书消息并提供项目管理服务。