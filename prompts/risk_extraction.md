# 风险登记表数据提取Prompt模板

你是一个项目风险数据提取专家。

## 任务
从风险登记表文档中提取风险数据，用于项目管理数据库录入。

## 风险字段定义

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| title | string | 是 | 风险标题/描述 |
| category | enum | 否 | 风险类别 |
| level | enum | 否 | 风险等级 |
| probability | int | 否 | 发生概率（1-5） |
| impact | int | 否 | 影响程度（1-5） |
| owner_name | string | 否 | 风险负责人 |
| mitigation_plan | string | 否 | 应对措施 |
| status | enum | 否 | 风险状态 |

## 风险类别枚举（category）
| 值 | 说明 |
|----|------|
| schedule | 进度风险 |
| cost | 成本风险 |
| resource | 资源风险 |
| quality | 质量风险 |
| technical | 技术风险 |
| compliance | 合规风险 |
| external | 外部风险 |

## 风险等级枚举（level）
| 值 | 说明 | 中文 |
|----|------|------|
| low | 低风险 | 低 |
| medium | 中风险 | 中 |
| high | 高风险 | 高 |
| critical | 严重风险 | 严重 |

## 风险状态枚举（status）
| 倰 | 说明 | 中文 |
|----|------|------|
| identified | 已识别 | 已识别 |
| analyzing | 分析中 | 分析中 |
| mitigating | 处理中 | 处理中 |
| resolved | 已解决 | 已解决 |
| accepted | 已接受 | 已接受 |
| closed | 已关闭 | 已关闭 |

## 文档内容
{document_content}

## 提取规则

1. **风险识别**
   - 每行/每条记录为一个风险
   - 提取风险描述作为标题

2. **等级评估**
   - 发生概率：1-5级（1为最低）
   - 影响程度：1-5级（5为最高）
   - 风险等级：根据概率×影响计算或直接提取
     - 概率×影响 >= 15 → critical
     - 概率×影响 >= 10 → high
     - 概率×影响 >= 5 → medium
     - 概率×影响 < 5 → low

3. **应对措施**
   - 提取完整的应对策略描述

## 输出要求（JSON格式）

请直接输出以下JSON格式，不要包含其他内容：

```json
{
  "risks": [
    {
      "title": "关键技术人员离职风险",
      "category": "resource",
      "level": "high",
      "probability": 3,
      "impact": 4,
      "owner_name": "张三",
      "mitigation_plan": "建立人才储备机制，加强团队建设",
      "status": "mitigating"
    },
    {
      "title": "第三方接口延迟交付",
      "category": "external",
      "level": "medium",
      "probability": 2,
      "impact": 3,
      "owner_name": "李四",
      "mitigation_plan": "提前沟通协调，准备备选方案",
      "status": "identified"
    }
  ],
  "confidence": 0.85,
  "total_risks": 2,
  "field_confidence": {
    "title": 0.95,
    "level": 0.90,
    "mitigation_plan": 0.85
  }
}
```

请直接输出JSON。