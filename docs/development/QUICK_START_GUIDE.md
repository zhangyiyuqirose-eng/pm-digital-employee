# PM数字员工系统 - 快速启动指南

## 准备工作

确保您已完成以下准备工作：
- 服务器或本地开发环境已准备
- Python 3.11+ 已安装
- 网络连接正常（用于安装依赖）

## 第一步：环境配置

```bash
# 1. 复制环境变量配置
cp .env.example .env

# 2. 编辑配置文件
vim .env  # 或使用您喜欢的编辑器
```

## 第二步：安装依赖

```bash
# 1. 安装Python依赖
pip install -r requirements.txt

# 如果遇到网络问题，可使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

## 第三步：配置飞书应用

在飞书开放平台完成以下配置：
1. 创建自建应用
2. 配置机器人和事件订阅
3. 设置回调URL：`https://your-domain.com/lark/webhook/event`
4. 获取并填写以下参数到 `.env` 文件：

```bash
LARK_APP_ID=你的飞书应用ID
LARK_APP_SECRET=你的飞书应用密钥
LARK_ENCRYPT_KEY=你的加密密钥
LARK_VERIFICATION_TOKEN=你的验证令牌
```

## 第四步：启动服务

### 开发模式
```bash
# 直接启动
python -m app.main

# 或使用uvicorn（推荐）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 生产模式
```bash
# 使用Docker启动
docker-compose up -d
```

## 第五步：验证部署

访问以下URL验证部署：
- 健康检查：`http://localhost:8000/health`
- API文档：`http://localhost:8000/docs`

## 系统功能使用

### 1. 项目管理功能
在飞书中与机器人对话，例如：
- "项目总览" - 查看项目整体状态
- "生成周报" - 自动生成项目周报
- "WBS生成" - 生成工作分解结构

### 2. AI助手功能
- 询问项目相关信息
- 请求任务进度更新
- 获取风险预警

### 3. 飞书集成
- 个人消息：一对一交互
- 群消息：团队协作

## 故障排查

### 常见问题
1. **依赖安装失败**：检查网络连接，使用国内镜像源
2. **端口被占用**：修改 `.env` 中的 `APP_PORT`
3. **飞书回调失败**：确认服务器公网可达，检查配置参数

### 查看日志
```bash
# Docker模式
docker-compose logs -f app

# 开发模式
# 日志将直接输出到终端
```

## 后续配置

### 性能调优
- 调整 worker 数量：`APP_WORKERS` 参数
- 配置数据库连接池
- 调整缓存策略

### 安全配置
- 定期更换密钥
- 配置访问控制
- 启用日志审计

### 监控配置
- 配置监控指标收集
- 设置告警规则
- 定期备份数据

## 附录：文件说明

- `start_dev.bat` - Windows启动脚本
- `start_dev.sh` - Linux/Mac启动脚本
- `docker-compose.yml` - Docker部署配置
- `requirements.txt` - Python依赖清单
- `DEPLOYMENT_VALIDATION_SUMMARY.md` - 部署验证报告

## 支持与反馈

如遇到问题，请检查：
1. 部署验证报告
2. 应用日志
3. 飞书后台配置
4. 网络连通性
5. 配置文件正确性

系统现已准备就绪，祝您使用愉快！