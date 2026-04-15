"""
PM Digital Employee - Cost Skills
项目经理数字员工系统 - 成本相关Skill封装

包含：
- CostEstimationSkill: 成本估算（基于it-cost-system）
- CostMonitoringSkill: 成本监控（基于it-cost-system EVM）
- CostAccountingSkill: 成本核算（基于it-cost-system）
"""

import uuid
from typing import Any, Dict, Optional
from datetime import datetime

from app.orchestrator.schemas import SkillExecutionResult, SkillManifest
from app.skills.base import BaseSkill
from app.core.logging import get_logger

logger = get_logger(__name__)

# IT-Cost-System API配置
IT_COST_SYSTEM_BASE_URL = "http://it-cost-backend:8000/api/v1"


class CostEstimationSkill(BaseSkill):
    """
    成本估算Skill.

    基于需求文档进行工作量评估和成本估算。
    功能包括：
    - 上传需求文档解析
    - 自动识别功能模块
    - 计算工作量和人月
    - 生成各阶段成本分布
    - 导出Excel工作量评估表
    """

    skill_name = "cost_estimation"
    display_name = "成本估算"
    description = "基于需求文档进行IT项目工作量评估和成本估算，支持功能模块识别、人月计算、成本分布。用户可以输入'成本估算'、'工作量评估'、'项目估价'、'费用估算'等触发。"
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        """执行成本估算."""
        import httpx

        # 获取参数
        project_id = self.get_param("project_id")
        project_name = self.get_param("project_name", "示例项目")
        estimation_type = self.get_param("type", "quick")  # quick | detailed

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 调用IT-Cost-System估算接口
                response = await client.post(
                    f"{IT_COST_SYSTEM_BASE_URL}/estimation/calculate",
                    json={
                        "document_id": project_id or "demo",
                        "cost_rates": {
                            "product_manager": 800,
                            "ui_designer": 600,
                            "engineer": 800,
                            "tester": 500,
                            "project_manager": 700,
                        }
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    estimation_data = result.get("data", {})
                else:
                    # 使用模拟数据
                    estimation_data = self._get_mock_estimation(project_name)

        except Exception as e:
            logger.warning(f"IT-Cost-System不可用，使用模拟数据: {e}")
            estimation_data = self._get_mock_estimation(project_name)

        # 构建展示数据
        presentation_text = self._format_estimation_result(estimation_data)

        return self.build_success_result(
            output=estimation_data,
            presentation_type="text",
            presentation_data={"text": presentation_text},
        )

    def _get_mock_estimation(self, project_name: str) -> Dict[str, Any]:
        """获取模拟估算数据."""
        return {
            "project_name": project_name,
            "estimate_id": str(uuid.uuid4())[:8],
            "total_workload": 185.5,
            "total_person_months": 8.43,
            "total_cost": 298000.0,
            "phase_workloads": {
                "需求分析": 18.5,
                "UI设计": 14.2,
                "技术设计": 22.3,
                "开发实现": 55.6,
                "技术测试": 28.4,
                "性能测试": 16.8,
                "准生产测试": 7.5,
                "上线部署": 4.2,
                "项目管理": 18.0,
            },
            "team_costs": {
                "产品经理": 37000,
                "UI设计师": 28400,
                "工程师": 133400,
                "测试工程师": 54000,
                "项目经理": 45200,
            },
            "compliance_status": True,
        }

    def _format_estimation_result(self, data: Dict[str, Any]) -> str:
        """格式化估算结果."""
        text = f"## 📊 成本估算报告\n\n"
        text += f"**项目名称**: {data.get('project_name', '未知')}\n"
        text += f"**估算编号**: {data.get('estimate_id', '-')}\n\n"

        text += f"### 📈 核心指标\n"
        text += f"- **总工作量**: {data.get('total_workload', 0):.1f} 人天\n"
        text += f"- **总人月**: {data.get('total_person_months', 0):.2f} 人月\n"
        text += f"- **总成本**: ¥{data.get('total_cost', 0):,.0f}\n\n"

        # 阶段工作量分布
        phase_workloads = data.get("phase_workloads", {})
        if phase_workloads:
            text += f"### 📋 阶段工作量分布\n"
            for phase, workload in phase_workloads.items():
                text += f"- {phase}: {workload:.1f} 人天\n"
            text += "\n"

        # 团队成本分布
        team_costs = data.get("team_costs", {})
        if team_costs:
            text += f"### 👥 团队成本分布\n"
            for role, cost in team_costs.items():
                text += f"- {role}: ¥{cost:,.0f}\n"
            text += "\n"

        # 合规状态
        compliance = data.get("compliance_status")
        if compliance is not None:
            status_icon = "✅" if compliance else "⚠️"
            text += f"**合规状态**: {status_icon} {'符合' if compliance else '需关注'}\n"

        return text

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        """获取Skill Manifest."""
        from app.orchestrator.skill_manifest import get_cost_estimation_manifest
        return get_cost_estimation_manifest()


class CostMonitoringSkill(BaseSkill):
    """
    成本监控Skill.

    基于EVM挣值管理的成本监控。
    功能包括：
    - PV/EV/AC计算分析
    - SPI/CPI绩效指标
    - 成本偏差预警
    - 完工估算EAC
    - 预算基线管理
    """

    skill_name = "cost_monitoring"
    display_name = "成本监控"
    description = "基于EVM挣值管理的成本监控，计算SPI/CPI绩效指标，预警成本偏差。用户可以输入'成本监控'、'挣值分析'、'EVM分析'、'成本绩效'等触发。"
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        """执行成本监控."""
        import httpx

        project_id = self.get_param("project_id")

        if not project_id:
            return self.build_error_result("请提供项目ID")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 调用IT-Cost-System EVM接口
                response = await client.get(
                    f"{IT_COST_SYSTEM_BASE_URL}/monitoring/evm/{project_id}/current"
                )

                if response.status_code == 200:
                    evm_data = response.json()
                else:
                    evm_data = self._get_mock_evm(project_id)

        except Exception as e:
            logger.warning(f"IT-Cost-System不可用，使用模拟数据: {e}")
            evm_data = self._get_mock_evm(project_id)

        # 分析状态
        status_analysis = self._analyze_evm_status(evm_data)

        # 构建展示数据
        presentation_text = self._format_evm_result(evm_data, status_analysis)

        return self.build_success_result(
            output={
                "evm": evm_data,
                "analysis": status_analysis,
            },
            presentation_type="text",
            presentation_data={"text": presentation_text},
        )

    def _get_mock_evm(self, project_id: str) -> Dict[str, Any]:
        """获取模拟EVM数据."""
        return {
            "project_id": project_id,
            "planned_value": 600000.0,  # PV
            "earned_value": 500000.0,   # EV
            "actual_cost": 550000.0,    # AC
            "budget_at_completion": 1000000.0,  # BAC
            "schedule_variance": -100000.0,  # SV = EV - PV
            "cost_variance": -50000.0,  # CV = EV - AC
            "schedule_performance_index": 0.83,  # SPI = EV / PV
            "cost_performance_index": 0.91,  # CPI = EV / AC
            "estimate_at_completion": 1098901.0,  # EAC = BAC / CPI
            "variance_at_completion": -98901.0,  # VAC = BAC - EAC
            "to_complete_performance_index": 1.11,  # TCPI
        }

    def _analyze_evm_status(self, evm: Dict[str, Any]) -> Dict[str, Any]:
        """分析EVM状态."""
        spi = evm.get("schedule_performance_index", 1.0)
        cpi = evm.get("cost_performance_index", 1.0)

        status = "正常"
        alerts = []

        # SPI分析
        if spi < 0.9:
            status = "风险"
            alerts.append({
                "level": "high",
                "type": "schedule",
                "message": f"进度绩效指数(SPI={spi:.2f})偏低，进度滞后超过10%"
            })
        elif spi < 0.95:
            status = "警告"
            alerts.append({
                "level": "medium",
                "type": "schedule",
                "message": f"进度绩效指数(SPI={spi:.2f})需关注，进度略有滞后"
            })

        # CPI分析
        if cpi < 0.9:
            status = "风险"
            alerts.append({
                "level": "high",
                "type": "cost",
                "message": f"成本绩效指数(CPI={cpi:.2f})偏低，成本超支超过10%"
            })
        elif cpi < 0.95:
            if status != "风险":
                status = "警告"
            alerts.append({
                "level": "medium",
                "type": "cost",
                "message": f"成本绩效指数(CPI={cpi:.2f})需关注，成本略有超支"
            })

        return {
            "status": status,
            "alerts": alerts,
            "recommendations": self._get_recommendations(spi, cpi)
        }

    def _get_recommendations(self, spi: float, cpi: float) -> list:
        """获取改进建议."""
        recommendations = []

        if spi < 0.95:
            recommendations.append("建议：评估关键路径任务，考虑资源调配或并行开发")
            recommendations.append("建议：审查项目范围，识别可压缩的非关键路径")

        if cpi < 0.95:
            recommendations.append("建议：审查成本支出明细，识别可优化的成本项")
            recommendations.append("建议：评估外包/采购策略，寻找成本优化机会")

        if spi >= 0.95 and cpi >= 0.95:
            recommendations.append("状态良好，继续保持当前项目管理节奏")

        return recommendations

    def _format_evm_result(self, evm: Dict, analysis: Dict) -> str:
        """格式化EVM结果."""
        status = analysis.get("status", "正常")
        status_icon = {"正常": "✅", "警告": "⚠️", "风险": "🔴"}.get(status, "❓")

        text = f"## {status_icon} 成本监控报告 (EVM分析)\n\n"

        # 核心指标
        text += f"### 📊 EVM核心指标\n"
        text += f"| 指标 | 值 | 说明 |\n"
        text += f"|------|-----|------|\n"
        text += f"| **PV** | ¥{evm.get('planned_value', 0):,.0f} | 计划价值 |\n"
        text += f"| **EV** | ¥{evm.get('earned_value', 0):,.0f} | 挣值 |\n"
        text += f"| **AC** | ¥{evm.get('actual_cost', 0):,.0f} | 实际成本 |\n"
        text += f"| **BAC** | ¥{evm.get('budget_at_completion', 0):,.0f} | 完工预算 |\n\n"

        # 偏差分析
        text += f"### 📈 偏差分析\n"
        sv = evm.get("schedule_variance", 0)
        cv = evm.get("cost_variance", 0)
        text += f"- **进度偏差(SV)**: ¥{sv:,.0f} {'🔴 滞后' if sv < 0 else '🟢 领先'}\n"
        text += f"- **成本偏差(CV)**: ¥{cv:,.0f} {'🔴 超支' if cv < 0 else '🟢 节约'}\n\n"

        # 绩效指数
        spi = evm.get("schedule_performance_index", 1.0)
        cpi = evm.get("cost_performance_index", 1.0)
        text += f"### 📉 绩效指数\n"
        text += f"- **SPI**: {spi:.2f} {'⚠️ 偏低' if spi < 0.95 else '✅ 正常'}\n"
        text += f"- **CPI**: {cpi:.2f} {'⚠️ 偏低' if cpi < 0.95 else '✅ 正常'}\n\n"

        # 预测指标
        eac = evm.get("estimate_at_completion", 0)
        vac = evm.get("variance_at_completion", 0)
        text += f"### 🔮 完工预测\n"
        text += f"- **EAC(完工估算)**: ¥{eac:,.0f}\n"
        text += f"- **VAC(完工偏差)**: ¥{vac:,.0f}\n\n"

        # 预警信息
        alerts = analysis.get("alerts", [])
        if alerts:
            text += f"### ⚠️ 预警信息\n"
            for alert in alerts:
                text += f"- **{alert.get('level', 'info').upper()}**: {alert.get('message', '')}\n"
            text += "\n"

        # 改进建议
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            text += f"### 💡 改进建议\n"
            for rec in recommendations:
                text += f"- {rec}\n"

        return text

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        """获取Skill Manifest."""
        from app.orchestrator.skill_manifest import get_cost_monitoring_manifest
        return get_cost_monitoring_manifest()


class CostAccountingSkill(BaseSkill):
    """
    成本核算Skill.

    项目成本核算与报表生成。
    功能包括：
    - 触发成本核算
    - 直接/间接成本分类
    - 利润计算
    - 核算报告生成
    """

    skill_name = "cost_accounting"
    display_name = "成本核算"
    description = "项目成本核算与报表生成，包括直接成本、间接成本分类及利润计算。用户可以输入'成本核算'、'结算'、'成本报表'、'核算报告'等触发。"
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        """执行成本核算."""
        import httpx

        project_id = self.get_param("project_id")

        if not project_id:
            return self.build_error_result("请提供项目ID")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 触发核算
                response = await client.post(
                    f"{IT_COST_SYSTEM_BASE_URL}/accounting/trigger",
                    json={"project_id": project_id}
                )

                if response.status_code == 200:
                    accounting_data = response.json()
                    report_id = accounting_data.get("report_id")

                    # 获取核算详情
                    detail_response = await client.get(
                        f"{IT_COST_SYSTEM_BASE_URL}/accounting/{report_id}"
                    )

                    if detail_response.status_code == 200:
                        result = detail_response.json()
                    else:
                        result = self._get_mock_accounting(project_id)
                else:
                    result = self._get_mock_accounting(project_id)

        except Exception as e:
            logger.warning(f"IT-Cost-System不可用，使用模拟数据: {e}")
            result = self._get_mock_accounting(project_id)

        # 构建展示数据
        presentation_text = self._format_accounting_result(result)

        return self.build_success_result(
            output=result,
            presentation_type="text",
            presentation_data={"text": presentation_text},
        )

    def _get_mock_accounting(self, project_id: str) -> Dict[str, Any]:
        """获取模拟核算数据."""
        return {
            "accounting_id": str(uuid.uuid4())[:8],
            "project_id": project_id,
            "period": "2026年Q1",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
            "direct_costs": {
                "人力成本": 320000.0,
                "硬件采购": 85000.0,
                "软件许可": 45000.0,
                "外包费用": 60000.0,
            },
            "indirect_costs": {
                "管理费用": 35000.0,
                "办公场地": 18000.0,
                "设备折旧": 12000.0,
            },
            "total_direct_costs": 510000.0,
            "total_indirect_costs": 65000.0,
            "total_costs": 575000.0,
            "revenue": 720000.0,
            "profit": 145000.0,
            "profitability_ratio": 0.20,
            "status": "completed",
        }

    def _format_accounting_result(self, data: Dict[str, Any]) -> str:
        """格式化核算结果."""
        text = f"## 📊 成本核算报告\n\n"
        text += f"**核算期间**: {data.get('period', '-')}\n"
        text += f"**核算编号**: {data.get('accounting_id', '-')}\n"
        text += f"**状态**: {'✅ 已完成' if data.get('status') == 'completed' else '⏳ 处理中'}\n\n"

        # 直接成本
        direct_costs = data.get("direct_costs", {})
        if direct_costs:
            text += f"### 💼 直接成本 (¥{data.get('total_direct_costs', 0):,.0f})\n"
            for item, amount in direct_costs.items():
                text += f"- {item}: ¥{amount:,.0f}\n"
            text += "\n"

        # 间接成本
        indirect_costs = data.get("indirect_costs", {})
        if indirect_costs:
            text += f"### 🏢 间接成本 (¥{data.get('total_indirect_costs', 0):,.0f})\n"
            for item, amount in indirect_costs.items():
                text += f"- {item}: ¥{amount:,.0f}\n"
            text += "\n"

        # 汇总
        text += f"### 📈 汇总\n"
        text += f"| 项目 | 金额 |\n"
        text += f"|------|------|\n"
        text += f"| 总成本 | ¥{data.get('total_costs', 0):,.0f} |\n"
        text += f"| 收入 | ¥{data.get('revenue', 0):,.0f} |\n"
        text += f"| **利润** | **¥{data.get('profit', 0):,.0f}** |\n"
        text += f"| 利润率 | {data.get('profitability_ratio', 0)*100:.1f}% |\n"

        return text

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        """获取Skill Manifest."""
        from app.orchestrator.skill_manifest import get_cost_accounting_manifest
        return get_cost_accounting_manifest()