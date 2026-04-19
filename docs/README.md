# PM Digital Employee - Documentation Index

## Directory Structure

```
docs/
├── api/                    # API文档
│   └── api_reference.md    # API接口参考
│
├── architecture/           # 架构文档
│   ├── architecture.md     # 系统架构说明
│   └── security.md         # 安全架构设计
│
├── deployment/             # 部署运维文档
│   ├── operations_runbook.md       # 运维手册
│   ├── GitHub-Actions配置说明.md   # CI/CD配置
│   ├── user_manual.md             # 用户操作手册
│   ├── admin_manual.md            # 管理员手册
│   ├── wecom_integration.md       # 企业微信集成
│   └── 企业微信操作手册.md          # 企业微信操作指南
│
├── development/            # 开发文档
│   ├── skill_development_guide.md  # Skill开发指南
│   └── QUICK_START.md             # 快速开始
│
├── requirements/           # 需求规格文档
│   ├── 国有大行科技子公司项目管理数字员工需求规格说明书.md
│   ├── 项目管理部数字员工-PM机器人需求规格说明书与实施方案.md
│   ├── PM机器人需求规格说明书与实施方案-0418.md
│   ├── PM机器人系统-ClaudeCode开发提示词集（专业架构师版）-0418.md
│   └── 文档分析与Claude开发指令体系.md
│
├── testing/                # 测试文档
│   ├── 测试方案.md         # 测试方案
│   ├── 测试报告.md         # 测试报告
│   ├── 联调测试报告.md     # 联调测试报告
│   └── 自动化测试报告.md   # 自动化测试报告
│
└── reports/                # 分析报告
    ├── 项目代码分析报告.md
    ├── 对比分析报告.md
    ├── 优化调整方案报告.md
    ├── 项目代码分析优化提示词.md
    └── 项目代码深度分析报告.md
```

## Quick Links

### For Developers

- [快速开始](development/QUICK_START.md) - 项目启动指南
- [Skill开发指南](development/skill_development_guide.md) - 如何开发新的Skill
- [系统架构](architecture/architecture.md) - 了解系统整体架构
- [API参考](api/api_reference.md) - API接口文档

### For DevOps

- [运维手册](deployment/operations_runbook.md) - 日常运维操作
- [CI/CD配置](deployment/GitHub-Actions配置说明.md) - 自动化部署配置
- [健康检查脚本](../scripts/health_check.sh) - 服务状态检查

### For Users

- [用户操作手册](deployment/user_manual.md) - 系统使用指南
- [管理员手册](deployment/admin_manual.md) - 系统管理操作

### For Testing

- [测试方案](testing/测试方案.md) - 测试策略
- [自动化测试报告](testing/自动化测试报告.md) - 自动化测试结果

### Reference Documents

- [需求规格说明书](requirements/国有大行科技子公司项目管理数字员工需求规格说明书.md) - 原始需求文档
- [Claude开发提示词集](requirements/PM机器人系统-ClaudeCode开发提示词集（专业架构师版）-0418.md) - 开发标准参考