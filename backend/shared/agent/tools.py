"""
Agent Tools Module - 计划一体化平台
提供三个核心工具：报表生成、结果推演、数据下沉(根因)
"""

import json
from typing import List, Dict, Any, Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from shared.utils.logger import get_logger
from .tools_data import (
    get_report_data,
    get_simulation_data,
    get_root_cause_data,
)

logger = get_logger("agent.tools")


# ============================================================================
# 辅助函数
# ============================================================================

def _format_chart(chart_data: Dict[str, Any]) -> str:
    """将图表数据格式化为前端可解析的 <chart> 标签"""
    return f"<chart>{json.dumps(chart_data, ensure_ascii=False)}</chart>"


def _format_table(headers: List[str], rows: List[List[str]]) -> str:
    """生成 Markdown 表格"""
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join(["------"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


# ============================================================================
# 1. 报表生成工具
# ============================================================================

class PlanReportInput(BaseModel):
    """计划报表生成输入参数"""
    report_type: str = Field(
        description="报表类型：计划执行报表、物料需求报表、产能分析报表、进度跟踪报表、质量分析报表"
    )
    start_date: Optional[str] = Field(default=None, description="开始日期，格式：YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="结束日期，格式：YYYY-MM-DD")
    dimensions: Optional[List[str]] = Field(default=None, description="分析维度，如：产线、产品、部门")
    metrics: Optional[List[str]] = Field(default=None, description="关注指标，如：达成率、利用率、合格率")


class PlanReportTool(BaseTool):
    """
    计划报表生成工具
    针对计划一体化平台生成：计划执行报表、物料需求报表、
    产能分析报表、进度跟踪报表、质量分析报表
    """

    name: str = "generate_plan_report"
    description: str = (
        "生成计划一体化平台相关报表，支持计划执行报表、物料需求报表、"
        "产能分析报表、进度跟踪报表、质量分析报表等类型。"
        "参数：report_type（必填，报表类型）、start_date（开始日期）、"
        "end_date（结束日期）、dimensions（维度）、metrics（指标）"
    )
    args_schema: Optional[Type[BaseModel]] = PlanReportInput

    # ── 公共方法 ──────────────────────────────────────────────

    def _run(
        self,
        report_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        dimensions: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
    ) -> str:
        return self._build_report(report_type, start_date, end_date, dimensions, metrics)

    async def _arun(
        self,
        report_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        dimensions: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
    ) -> str:
        return self._build_report(report_type, start_date, end_date, dimensions, metrics)

    # ── 核心逻辑 ──────────────────────────────────────────────

    def _build_report(
        self,
        report_type: str,
        start_date: Optional[str],
        end_date: Optional[str],
        dimensions: Optional[List[str]],
        metrics: Optional[List[str]],
    ) -> str:
        params = {
            "report_type": report_type, "start_date": start_date,
            "end_date": end_date, "dimensions": dimensions, "metrics": metrics,
        }
        logger.info(f"[Tool: {self.name}] Called with: {json.dumps(params, ensure_ascii=False, default=str)}")

        data = get_report_data(report_type, start_date, end_date, dimensions, metrics)

        lines = [f"## {data['report_type']}", ""]

        if start_date or end_date:
            lines.append(f"**时间范围**: {start_date or '不限'} ~ {end_date or '不限'}")
            lines.append("")

        if dimensions:
            lines.append(f"**分析维度**: {', '.join(dimensions)}")
            lines.append("")

        # 根据报表类型渲染不同内容
        dispatch = {
            "计划执行报表": self._render_execution,
            "物料需求报表": self._render_material,
            "产能分析报表": self._render_capacity,
            "进度跟踪报表": self._render_progress,
            "质量分析报表": self._render_quality,
        }
        render = dispatch.get(report_type, self._render_execution)
        lines.append(render(data))
        result = "\n".join(lines)
        logger.info(f"[Tool: {self.name}] Result ({len(result)} chars): {result[:300]}{'...' if len(result) > 300 else ''}")
        return result

    # ── 各报表渲染 ────────────────────────────────────────────

    def _render_execution(self, data: dict) -> str:
        summary = data["summary"]
        parts = [
            "### 总体概览",
            "",
            f"- 计划总产量：**{summary['total_plan_qty']:,.0f}** 件",
            f"- 实际总产量：**{summary['total_actual_qty']:,.0f}** 件",
            f"- 平均达成率：**{summary['avg_achievement_rate']}%**",
            "",
            "### 各产线执行明细",
            "",
        ]

        rows = []
        labels, values, rates = [], [], []
        for line in data["lines"]:
            rows.append([
                line["line_name"],
                f"{line['plan_qty']:,.0f}",
                f"{line['actual_qty']:,.0f}",
                f"{line['achievement_rate']}%",
                line["deviation_reason"],
            ])
            labels.append(line["line_name"].replace("产线", ""))
            values.append(line["actual_qty"])
            rates.append(line["achievement_rate"])

        parts.append(_format_table(
            ["产线", "计划产量", "实际产量", "达成率", "偏差原因"], rows
        ))

        parts.extend([
            "",
            _format_chart({
                "chartType": "bar",
                "title": "各产线计划 vs 实际产量",
                "labels": labels,
                "datasets": [
                    {"label": "计划产量", "data": [line["plan_qty"] for line in data["lines"]]},
                    {"label": "实际产量", "data": values},
                ],
            }),
        ])
        return "\n".join(parts)

    def _render_material(self, data: dict) -> str:
        parts = ["### 物料需求与库存", ""]
        rows, labels, demands, stocks = [], [], [], []
        for m in data["materials"]:
            status_icon = {"充足": "✅", "预警": "⚠️", "紧缺": "🔴"}.get(m["supply_status"], "")
            rows.append([
                m["material_name"], f"{m['demand_qty']:,}",
                f"{m['stock_qty']:,}", f"{m['gap_qty']:,}",
                f"{status_icon} {m['supply_status']}", m["supplier"],
            ])
            labels.append(m["material_name"][:6])
            demands.append(m["demand_qty"])
            stocks.append(m["stock_qty"])

        parts.append(_format_table(
            ["物料", "需求量", "库存量", "缺口", "状态", "供应商"], rows
        ))
        parts.extend([
            "",
            _format_chart({
                "chartType": "bar",
                "title": "物料需求 vs 库存对比",
                "labels": labels,
                "datasets": [
                    {"label": "需求量", "data": demands},
                    {"label": "库存量", "data": stocks},
                ],
            }),
        ])
        return "\n".join(parts)

    def _render_capacity(self, data: dict) -> str:
        parts = ["### 产能利用率分析", ""]
        rows, labels, utils = [], [], []
        for line in data["lines"]:
            rows.append([
                line["line_name"],
                f"{line['theoretical_capacity']:,}",
                f"{line['actual_output']:,}",
                f"{line['utilization_rate']}%",
                f"{line['oee_score']}%",
                line["is_bottleneck"],
            ])
            labels.append(line["line_name"].replace("产线", ""))
            utils.append(line["utilization_rate"])

        parts.append(_format_table(
            ["产线", "理论产能", "实际产出", "利用率", "OEE", "是否瓶颈"], rows
        ))
        parts.extend([
            "",
            _format_chart({
                "chartType": "bar",
                "title": "各产线利用率",
                "labels": labels,
                "datasets": [{"label": "利用率(%)", "data": utils}],
            }),
        ])
        return "\n".join(parts)

    def _render_progress(self, data: dict) -> str:
        parts = ["### 进度跟踪", ""]
        rows, labels, plans, actuals = [], [], [], []
        for p in data["projects"]:
            status_icon = {"正常": "✅", "轻微延期": "⚠️", "严重延期": "🔴", "提前": "🟢"}.get(p["status"], "")
            rows.append([
                p["project_name"], f"{p['plan_progress']}%", f"{p['actual_progress']}%",
                f"{p['deviation_days']:+.1f}天", f"{status_icon} {p['status']}", p["owner_dept"],
            ])
            labels.append(p["project_name"][-6:])
            plans.append(p["plan_progress"])
            actuals.append(p["actual_progress"])

        parts.append(_format_table(
            ["项目", "计划进度", "实际进度", "偏差", "状态", "责任部门"], rows
        ))
        parts.extend([
            "",
            _format_chart({
                "chartType": "bar",
                "title": "项目计划 vs 实际进度",
                "labels": labels,
                "datasets": [
                    {"label": "计划进度(%)", "data": plans},
                    {"label": "实际进度(%)", "data": actuals},
                ],
            }),
        ])
        return "\n".join(parts)

    def _render_quality(self, data: dict) -> str:
        parts = ["### 质量分析", ""]
        rows, labels, rates = [], [], []
        for line in data["lines"]:
            rows.append([
                line["line_name"], f"{line['inspected_qty']:,}",
                f"{line['passed_qty']:,}", f"{line['pass_rate']}%",
                line["major_defect"], str(line["defect_count"]),
            ])
            labels.append(line["line_name"].replace("产线", ""))
            rates.append(line["pass_rate"])

        parts.append(_format_table(
            ["产线", "抽检数", "合格数", "合格率", "主要缺陷", "缺陷数"], rows
        ))
        parts.extend([
            "",
            _format_chart({
                "chartType": "bar",
                "title": "各产线一次合格率",
                "labels": labels,
                "datasets": [{"label": "合格率(%)", "data": rates}],
            }),
        ])
        return "\n".join(parts)


# ============================================================================
# 2. 结果推演工具
# ============================================================================

class PlanSimulationInput(BaseModel):
    """计划结果推演输入参数"""
    scenario: str = Field(
        description="推演场景：产能调整、订单插单、物料延迟、资源调配"
    )
    variables: Optional[Dict[str, Any]] = Field(
        default=None,
        description="变量参数，如：{'产线': '涂装产线C', '调整类型': '增加班次', '调整量': 2} 或 "
                    "{'紧急订单数': 3} 或 {'物料': '钢板-S355J2', '延迟天数': 5} 或 "
                    "{'来源产线': '冲压产线A', '目标产线': '总装产线D', '调配比例': 20}"
    )


class PlanSimulationTool(BaseTool):
    """
    计划结果推演工具
    对计划一体化场景进行 what-if 分析：
    产能调整推演、订单插单推演、物料延迟推演、资源调配推演
    """

    name: str = "simulate_plan_scenario"
    description: str = (
        "进行计划场景推演和预测分析，支持产能调整、订单插单、物料延迟、资源调配等场景。"
        "参数：scenario（必填，推演场景描述）、variables（可选，变量参数字典）"
    )
    args_schema: Optional[Type[BaseModel]] = PlanSimulationInput

    # ── 公共方法 ──────────────────────────────────────────────

    def _run(self, scenario: str, variables: Optional[Dict[str, Any]] = None) -> str:
        return self._build_simulation(scenario, variables or {})

    async def _arun(self, scenario: str, variables: Optional[Dict[str, Any]] = None) -> str:
        return self._build_simulation(scenario, variables or {})

    # ── 核心逻辑 ──────────────────────────────────────────────

    def _build_simulation(self, scenario: str, variables: Dict[str, Any]) -> str:
        params = {"scenario": scenario, "variables": variables}
        logger.info(f"[Tool: {self.name}] Called with: {json.dumps(params, ensure_ascii=False, default=str)}")

        data = get_simulation_data(scenario, variables)

        lines = [
            f"## 🔮 {data['scenario']}",
            "",
            f"**推演场景**: {scenario}",
            "",
        ]

        sim_type = data.get("scenario", "")

        if "产能" in sim_type:
            lines.append(self._render_capacity_sim(data))
        elif "订单" in sim_type:
            lines.append(self._render_order_sim(data))
        elif "物料" in sim_type:
            lines.append(self._render_material_sim(data))
        elif "资源" in sim_type:
            lines.append(self._render_resource_sim(data))
        else:
            lines.append(self._render_capacity_sim(data))

        # 风险提示
        lines.extend([
            "",
            "### 风险提示",
            "",
            f"- {data.get('risk', '以上推演基于历史数据和假设条件，实际结果可能受多因素影响')}",
            "- 建议结合实时数据和多维度进行综合判断",
            "- 推演结果为模拟值，实际决策请参考实时系统数据",
        ])

        result = "\n".join(lines)
        logger.info(f"[Tool: {self.name}] Result ({len(result)} chars): {result[:300]}{'...' if len(result) > 300 else ''}")
        return result

    # ── 各场景渲染 ────────────────────────────────────────────

    def _render_capacity_sim(self, data: dict) -> str:
        base = data["base"]
        forecast = data["forecast"]
        impact_icon = {"正面": "📈", "负面": "📉", "无变化": "➡️"}.get(data["impact"], "")

        parts = [
            f"**目标产线**: {data['target_line']}",
            f"**调整措施**: {data['adjustment']}",
            "",
            "### 推演结果",
            "",
            _format_table(
                ["指标", "调整前", "调整后", "变化"],
                [
                    ["日产能(件)", f"{base['daily_capacity']:,.0f}", f"{forecast['daily_capacity']:,.0f}",
                     f"{forecast['capacity_change_pct']:+.1f}%"],
                    ["交付周期(天)", str(base['lead_time_days']), str(forecast['lead_time_days']),
                     f"{forecast['lead_time_days'] - base['lead_time_days']:+.1f}天"],
                ],
            ),
            "",
            f"**{impact_icon} 综合影响**: {data['impact']}",
            "",
            _format_chart({
                "chartType": "bar",
                "title": f"{data['target_line']} 产能调整对比",
                "labels": ["日产能", "交付周期"],
                "datasets": [
                    {"label": "调整前", "data": [base["daily_capacity"], base["lead_time_days"]]},
                    {"label": "调整后", "data": [forecast["daily_capacity"], forecast["lead_time_days"]]},
                ],
            }),
        ]
        return "\n".join(parts)

    def _render_order_sim(self, data: dict) -> str:
        parts = [
            f"**紧急订单数**: {data['urgent_orders']}",
            "",
            "### 推演结果",
            "",
        ]

        labels, on_time, affected = [], [], []
        for sc in data["scenarios"]:
            labels.append(sc["label"])
            on_time.append(sc["on_time_rate"])
            affected.append(sc["affected_orders"])

        rows = [[
            s["label"], f"{s['on_time_rate']}%",
            str(s["affected_orders"]), f"{s['avg_delay_days']}天"
        ] for s in data["scenarios"]]

        parts.append(_format_table(
            ["场景", "按时交付率", "受影响订单", "平均延迟"], rows
        ))
        parts.extend([
            "",
            f"**建议**: {data.get('recommendation', '请评估影响后决策')}",
            "",
            _format_chart({
                "chartType": "bar",
                "title": "插单前后按时交付率对比",
                "labels": labels,
                "datasets": [{"label": "按时交付率(%)", "data": on_time}],
            }),
        ])
        return "\n".join(parts)

    def _render_material_sim(self, data: dict) -> str:
        parts = [
            f"**关键物料**: {data['material']}",
            f"**延迟天数**: {data['delay_days']}天",
            f"**影响产线**: {data['affected_lines']}",
            f"**项目总体延迟**: {data['total_project_delay']}天",
            "",
            "### 级联影响分析",
            "",
        ]

        cascades = data.get("cascade_effects", [])
        rows = [[c["stage"], c["line"], f"{c['cumulative_delay_days']}天", c["impact_desc"]] for c in cascades]
        parts.append(_format_table(
            ["环节", "影响产线", "累计延迟", "影响描述"], rows
        ))

        labels = [c["line"] for c in cascades]
        delays = [c["cumulative_delay_days"] for c in cascades]

        parts.extend([
            "",
            f"** 应对建议**: {data.get('mitigation', '请评估供应链风险')}",
            "",
            _format_chart({
                "chartType": "line",
                "title": "物料延迟级联效应",
                "labels": labels,
                "datasets": [{"label": "累计延迟(天)", "data": delays, "fill": False}],
            }),
        ])
        return "\n".join(parts)

    def _render_resource_sim(self, data: dict) -> str:
        source = data["source_line"]
        target = data["target_line"]

        parts = [
            f"**来源产线**: {source}",
            f"**目标产线**: {target}",
            f"**调配比例**: {data['allocation_pct']}%",
            "",
            "### 调配前后对比",
            "",
        ]

        rows = [
            ["产线", "产能(件/天)", "利用率(%)", "状态"],
            [source, f"{data['before'][source]['capacity']:,.0f}",
             f"{data['before'][source]['utilization']}%", "调配前"],
            [source, f"{data['after'][source]['capacity']:,.0f}",
             f"{data['after'][source]['utilization']:.0f}%", "调配后"],
            [target, f"{data['before'][target]['capacity']:,.0f}",
             f"{data['before'][target]['utilization']}%", "调配前"],
            [target, f"{data['after'][target]['capacity']:,.0f}",
             f"{data['after'][target]['utilization']:.0f}%", "调配后"],
        ]

        parts.append(_format_table(
            ["产线", "产能(件/天)", "利用率(%)", "状态"],
            [r[0:4] for r in rows[1:]],  # skip header row
        ))

        parts.extend([
            "",
            f"**净收益评估**: {data.get('net_benefit', '请结合实际情况评估')}",
            "",
            _format_chart({
                "chartType": "bar",
                "title": "资源调配产能对比",
                "labels": [f"{source}(前)", f"{source}(后)", f"{target}(前)", f"{target}(后)"],
                "datasets": [{
                    "label": "产能(件/天)",
                    "data": [
                        data["before"][source]["capacity"],
                        data["after"][source]["capacity"],
                        data["before"][target]["capacity"],
                        data["after"][target]["capacity"],
                    ],
                }],
            }),
        ])
        return "\n".join(parts)


# ============================================================================
# 3. 数据下沉(根因分析)工具
# ============================================================================

class RootCauseInput(BaseModel):
    """根因分析输入参数"""
    problem: str = Field(
        description="问题描述，如：工期延误、产能瓶颈、物料短缺、质量波动、成本超预算"
    )
    indicators: Optional[List[str]] = Field(
        default=None,
        description="相关指标列表，如：['达成率', '利用率', '合格率', '交付准时率']"
    )


class RootCauseTool(BaseTool):
    """
    数据下沉(根因分析)工具
    对计划一体化平台的异常进行下钻分析：
    工期延误根因、产能瓶颈根因、物料短缺根因、质量波动根因、成本超预算根因
    """

    name: str = "analyze_root_cause"
    description: str = (
        "对计划一体化平台的业务问题进行数据下沉与根因分析，"
        "支持工期延误、产能瓶颈、物料短缺、质量波动、成本超预算等分析类型。"
        "参数：problem（必填，问题描述）、indicators（可选，相关指标）"
    )
    args_schema: Optional[Type[BaseModel]] = RootCauseInput

    # ── 公共方法 ──────────────────────────────────────────────

    def _run(self, problem: str, indicators: Optional[List[str]] = None) -> str:
        return self._build_analysis(problem, indicators)

    async def _arun(self, problem: str, indicators: Optional[List[str]] = None) -> str:
        return self._build_analysis(problem, indicators)

    # ── 核心逻辑 ──────────────────────────────────────────────

    def _build_analysis(self, problem: str, indicators: Optional[List[str]]) -> str:
        params = {"problem": problem, "indicators": indicators}
        logger.info(f"[Tool: {self.name}] Called with: {json.dumps(params, ensure_ascii=False, default=str)}")

        data = get_root_cause_data(problem, indicators)

        lines = [
            f"##{data['analysis_type']}",
            "",
            f"**问题描述**: {problem}",
        ]

        if indicators:
            lines.append(f"**关联指标**: {', '.join(indicators)}")

        lines.append("")

        analysis_type = data.get("analysis_type", "")

        if "工期" in analysis_type or "延期" in analysis_type:
            lines.append(self._render_delay_analysis(data))
        elif "瓶颈" in analysis_type:
            lines.append(self._render_bottleneck_analysis(data))
        elif "物料" in analysis_type:
            lines.append(self._render_shortage_analysis(data))
        elif "质量" in analysis_type:
            lines.append(self._render_quality_analysis(data))
        elif "成本" in analysis_type:
            lines.append(self._render_cost_analysis(data))
        else:
            lines.append(self._render_delay_analysis(data))

        result = "\n".join(lines)
        logger.info(f"[Tool: {self.name}] Result ({len(result)} chars): {result[:300]}{'...' if len(result) > 300 else ''}")
        return result

    # ── 各分析类型渲染 ────────────────────────────────────────

    def _render_delay_analysis(self, data: dict) -> str:
        parts = [
            "### 数据下钻：延迟贡献度分析",
            "",
        ]

        rows, labels, contributions = [], [], []
        for d in data["dimensions"]:
            rows.append([d["name"], f"{d['contribution']}%", d["detail"]])
            labels.append(d["name"])
            contributions.append(d["contribution"])

        parts.append(_format_table(
            ["影响维度", "贡献度", "详情"], rows
        ))

        parts.extend([
            "",
            f"**主要原因**: {data['primary_cause']}（贡献度 {data['primary_contribution']}%）",
            "",
            "### 改进建议",
            "",
        ])
        for i, rec in enumerate(data.get("recommendations", []), 1):
            parts.append(f"{i}. {rec}")

        parts.extend([
            "",
            _format_chart({
                "chartType": "pie",
                "title": "延迟原因贡献度分布",
                "labels": labels,
                "datasets": [{"label": "贡献度(%)", "data": contributions}],
            }),
        ])
        return "\n".join(parts)

    def _render_bottleneck_analysis(self, data: dict) -> str:
        parts = [
            f"**瓶颈产线**: {data['bottleneck_line']}（利用率 {data['bottleneck_utilization']}%）",
            "",
            "### 数据下钻：各产线利用率与排队情况",
            "",
        ]

        rows, labels, utils = [], [], []
        for line in data["line_details"]:
            marker = "瓶颈" if line["is_bottleneck"] else ""
            rows.append([
                f"{line['name']}{marker}", f"{line['utilization']}%",
                f"{line['queue_length']}批", f"{line['cycle_time']}min",
            ])
            labels.append(line["name"].replace("产线", ""))
            utils.append(line["utilization"])

        parts.append(_format_table(
            ["产线", "利用率", "排队批次", "节拍"], rows
        ))

        parts.extend([
            "",
            "### 根因定位",
            "",
        ])
        for i, cause in enumerate(data.get("root_causes", []), 1):
            parts.append(f"{i}. {cause}")

        parts.extend([
            "",
            "### 改进建议",
            "",
        ])
        for i, rec in enumerate(data.get("recommendations", []), 1):
            parts.append(f"{i}. {rec}")

        parts.extend([
            "",
            _format_chart({
                "chartType": "bar",
                "title": "各产线利用率对比",
                "labels": labels,
                "datasets": [{"label": "利用率(%)", "data": utils}],
            }),
        ])
        return "\n".join(parts)

    def _render_shortage_analysis(self, data: dict) -> str:
        parts = [
            f"**总缺料量**: {data['total_shortage_value']} 件",
            "",
            "### 数据下钻：缺料明细与根因",
            "",
        ]

        rows, labels, qtys = [], [], []
        for item in data["shortage_items"]:
            rows.append([
                item["material"], f"{item['shortage_qty']}",
                item["root_cause"], item["affected_lines"],
            ])
            labels.append(item["material"][:8])
            qtys.append(item["shortage_qty"])

        parts.append(_format_table(
            ["物料", "缺量", "根因", "影响产线"], rows
        ))

        parts.extend([
            "",
            "### 问题来源统计",
            "",
            f"- 供应商问题：{data['summary']['supplier_issue_count']} 项",
            f"- 质量问题：{data['summary']['quality_issue_count']} 项",
            f"- 物流问题：{data['summary']['logistics_issue_count']} 项",
            "",
            "### 改进建议",
            "",
        ])
        for i, rec in enumerate(data.get("recommendations", []), 1):
            parts.append(f"{i}. {rec}")

        parts.extend([
            "",
            _format_chart({
                "chartType": "pie",
                "title": "物料短缺分布",
                "labels": labels,
                "datasets": [{"label": "缺量(件)", "data": qtys}],
            }),
        ])
        return "\n".join(parts)

    def _render_quality_analysis(self, data: dict) -> str:
        parts = [
            f"**总缺陷数**: {data['total_defects']}",
            f"**主要缺陷**: {data['primary_defect']}（{data['primary_line']}）",
            "",
            "### 数据下钻：缺陷分布与根因",
            "",
        ]

        rows, labels, counts = [], [], []
        for d in data["defect_analysis"]:
            rows.append([
                d["defect_type"], str(d["count"]), f"{d['pct']}%",
                d["line"], d["root"],
            ])
            labels.append(d["defect_type"])
            counts.append(d["count"])

        parts.append(_format_table(
            ["缺陷类型", "数量", "占比", "产线", "根因"], rows
        ))

        parts.extend([
            "",
            "### 改进建议",
            "",
        ])
        for i, rec in enumerate(data.get("recommendations", []), 1):
            parts.append(f"{i}. {rec}")

        parts.extend([
            "",
            _format_chart({
                "chartType": "pie",
                "title": "缺陷类型分布",
                "labels": labels,
                "datasets": [{"label": "数量", "data": counts}],
            }),
        ])
        return "\n".join(parts)

    def _render_cost_analysis(self, data: dict) -> str:
        parts = [
            f"**总超支**: {data['total_overrun']}万元",
            f"**主要驱动因素**: {data['primary_cost_driver']}",
            "",
            "### 数据下钻：成本超支明细与根因",
            "",
        ]

        rows, labels, costs = [], [], []
        for c in data["cost_items"]:
            rows.append([
                c["item"], f"{c['overrun']}万", f"{c['pct']}%", c["root"],
            ])
            labels.append(c["item"])
            costs.append(c["overrun"])

        parts.append(_format_table(
            ["超支项", "金额", "占比", "根因"], rows
        ))

        parts.extend([
            "",
            "### 改进建议",
            "",
        ])
        for i, rec in enumerate(data.get("recommendations", []), 1):
            parts.append(f"{i}. {rec}")

        parts.extend([
            "",
            _format_chart({
                "chartType": "pie",
                "title": "成本超支构成",
                "labels": labels,
                "datasets": [{"label": "超支(万)", "data": costs}],
            }),
        ])
        return "\n".join(parts)


# ============================================================================
# 常量映射（供 prompt 使用）
# ============================================================================

REPORT_TYPE_MAP = {
    "计划执行报表": "各产线计划 vs 实际产量、达成率分析",
    "物料需求报表": "物料需求、库存、缺口及采购状态",
    "产能分析报表": "产能利用率、OEE、瓶颈识别",
    "进度跟踪报表": "项目/订单计划进度 vs 实际进度",
    "质量分析报表": "各产线抽检合格率、缺陷分布",
}

SIMULATION_TYPE_MAP = {
    "产能调整": "增加/减少产线或班次，推演对交期和产量的影响",
    "订单插单": "紧急订单插单对现有计划的影响评估",
    "物料延迟": "关键物料延迟到货的级联影响分析",
    "资源调配": "在不同产线间调配资源的效果推演",
}

RCA_TYPE_MAP = {
    "工期延误": "下钻分析各环节对工期延迟的贡献度",
    "产能瓶颈": "定位真正的产能瓶颈产线及根因",
    "物料短缺": "分析物料缺料的深层原因及影响范围",
    "质量波动": "下钻到具体工艺参数层面分析质量异常",
    "成本超预算": "逐项分析成本超支的构成及驱动因素",
}


# ============================================================================
# 工具列表导出
# ============================================================================

BASIC_TOOLS: List[BaseTool] = [
    PlanReportTool(),
    PlanSimulationTool(),
    RootCauseTool(),
]


def get_all_tools() -> List[BaseTool]:
    """获取所有可用工具"""
    return BASIC_TOOLS
