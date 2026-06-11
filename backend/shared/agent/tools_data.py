"""
计划一体化平台 - 数据模拟生成模块
提供报表生成、结果推演、根因分析所需的模拟数据
"""

import random
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


# ============================================================================
# 平台基础常量 - 模拟计划一体化平台的真实业务场景
# ============================================================================

PRODUCTION_LINES = ["冲压产线A", "焊接产线B", "涂装产线C", "总装产线D", "检测产线E"]
PRODUCTS = ["产品P1-底盘组件", "产品P2-发动机总成", "产品P3-变速器", "产品P4-车身焊接", "产品P5-电气模块"]
MATERIALS = [
    "钢板-S355J2", "铝合金-6061", "铜线-Φ2.5mm", "密封圈-NBR",
    "轴承-6205", "螺栓-M12", "液压油-HM46", "涂料-EP03",
    "电子元件-IC", "塑料粒子-PP"
]
DEPARTMENTS = ["计划调度部", "生产制造部", "采购供应部", "质量管理部", "仓储物流部"]
ORDER_STATUS = ["已完成", "进行中", "待排产", "延期"]
SHIFTS = ["白班(08:00-16:00)", "中班(16:00-24:00)", "夜班(00:00-08:00)"]


def _seed_from_date(date_str: str) -> None:
    """根据日期设置随机种子，保证同一天数据一致"""
    seed = sum(ord(c) for c in date_str)
    random.seed(seed)


def _fmt(value: float, unit: str = "") -> str:
    """格式化数值，自动加千分位"""
    if unit:
        return f"{value:,.1f}{unit}"
    return f"{value:,.1f}"


def _format_chart(chart_data: Dict[str, Any]) -> str:
    """将图表数据格式化为前端可解析的 <chart> 标签"""
    return f"<chart>{json.dumps(chart_data, ensure_ascii=False)}</chart>"


# ============================================================================
# 1. 报表生成 - 数据生成器
# ============================================================================

class ReportDataGenerator:
    """报表数据生成器 - 计划一体化场景"""

    @staticmethod
    def generate_plan_execution_report(start_date: str, end_date: str) -> Dict[str, Any]:
        """
        生成计划执行报表数据
        包含各产线的：计划产量、实际产量、达成率、偏差分析
        """
        _seed_from_date(start_date)
        data = {
            "report_type": "计划执行报表",
            "period": f"{start_date} ~ {end_date}",
            "summary": {
                "total_plan_qty": 0,
                "total_actual_qty": 0,
                "avg_achievement_rate": 0.0,
            },
            "lines": [],
        }

        for line in PRODUCTION_LINES:
            plan_qty = random.randint(800, 2000)
            deviation_pct = random.uniform(-15, 10)
            actual_qty = plan_qty * (1 + deviation_pct / 100)

            data["summary"]["total_plan_qty"] += plan_qty
            data["summary"]["total_actual_qty"] += actual_qty

            data["lines"].append({
                "line_name": line,
                "plan_qty": round(plan_qty, 0),
                "actual_qty": round(actual_qty, 0),
                "achievement_rate": round(100 + deviation_pct, 1),
                "deviation_reason": _get_deviation_reason(deviation_pct, line),
            })

        data["summary"]["avg_achievement_rate"] = round(
            data["summary"]["total_actual_qty"] / data["summary"]["total_plan_qty"] * 100, 1
        )
        return data

    @staticmethod
    def generate_material_requirement_report(start_date: str, end_date: str) -> Dict[str, Any]:
        """
        生成物料需求报表数据
        包含各物料的：需求量、库存量、缺口、采购状态
        """
        _seed_from_date(start_date)
        data = {
            "report_type": "物料需求报表",
            "period": f"{start_date} ~ {end_date}",
            "materials": [],
        }

        for mat in MATERIALS:
            demand = random.randint(500, 5000)
            stock = random.randint(200, 4000)
            gap = max(0, demand - stock)

            status = "充足"
            if gap > demand * 0.3:
                status = "紧缺"
            elif gap > 0:
                status = "预警"

            data["materials"].append({
                "material_name": mat,
                "demand_qty": demand,
                "stock_qty": stock,
                "gap_qty": gap,
                "supply_status": status,
                "supplier": f"供应商-{chr(65 + random.randint(0, 4))}",
            })

        return data

    @staticmethod
    def generate_capacity_report(start_date: str, end_date: str) -> Dict[str, Any]:
        """
        生成产能利用率报表数据
        包含各产线的：理论产能、实际产出、利用率、空闲产能
        """
        _seed_from_date(start_date)
        data = {
            "report_type": "产能分析报表",
            "period": f"{start_date} ~ {end_date}",
            "lines": [],
        }

        for line in PRODUCTION_LINES:
            theo_cap = random.randint(2000, 5000)
            util_rate = random.uniform(60, 98)
            actual_output = theo_cap * util_rate / 100

            bottleneck = "否"
            if util_rate > 90:
                bottleneck = "是（接近满负荷）"

            data["lines"].append({
                "line_name": line,
                "theoretical_capacity": theo_cap,
                "actual_output": round(actual_output, 0),
                "utilization_rate": round(util_rate, 1),
                "idle_capacity": round(theo_cap - actual_output, 0),
                "oee_score": round(random.uniform(70, 95), 1),
                "is_bottleneck": bottleneck,
            })

        return data

    @staticmethod
    def generate_progress_report(start_date: str, end_date: str) -> Dict[str, Any]:
        """
        生成进度跟踪报表数据
        包含各订单/任务的：计划进度、实际进度、偏差天数
        """
        _seed_from_date(start_date)
        projects = [
            "订单#2024-PL-001 底盘装配",
            "订单#2024-PL-002 发动机组装",
            "订单#2024-PL-003 变速器加工",
            "订单#2024-PL-004 车身焊接",
            "订单#2024-PL-005 电气调试",
            "订单#2024-PL-006 整车总装",
        ]

        data = {
            "report_type": "进度跟踪报表",
            "period": f"{start_date} ~ {end_date}",
            "projects": [],
        }

        for proj in projects:
            plan_progress = random.uniform(60, 100)
            deviation = random.uniform(-20, 15)
            actual_progress = min(100, max(0, plan_progress + deviation))

            status = "正常"
            if deviation < -10:
                status = "严重延期"
            elif deviation < -5:
                status = "轻微延期"
            elif deviation > 5:
                status = "提前"

            data["projects"].append({
                "project_name": proj,
                "plan_progress": round(plan_progress, 1),
                "actual_progress": round(actual_progress, 1),
                "deviation_days": round(deviation, 1),
                "status": status,
                "owner_dept": random.choice(DEPARTMENTS),
            })

        return data

    @staticmethod
    def generate_quality_report(start_date: str, end_date: str) -> Dict[str, Any]:
        """
        生成质量分析报表数据
        包含各产线的：抽检数、合格数、合格率、主要缺陷类型
        """
        _seed_from_date(start_date)
        data = {
            "report_type": "质量分析报表",
            "period": f"{start_date} ~ {end_date}",
            "lines": [],
        }

        defects = ["尺寸超差", "表面缺陷", "装配不良", "电气故障", "密封不严"]

        for line in PRODUCTION_LINES:
            inspected = random.randint(500, 2000)
            pass_rate = random.uniform(92, 99.5)
            passed = int(inspected * pass_rate / 100)

            data["lines"].append({
                "line_name": line,
                "inspected_qty": inspected,
                "passed_qty": passed,
                "pass_rate": round(pass_rate, 2),
                "major_defect": random.choice(defects),
                "defect_count": inspected - passed,
            })

        return data


def _get_deviation_reason(deviation_pct: float, line: str) -> str:
    """根据偏差情况生成原因描述"""
    if deviation_pct < -10:
        return random.choice(["设备故障停机", "物料供应延迟", "人员不足"])
    elif deviation_pct < -5:
        return random.choice(["换线耗时", "来料检验延长", "工艺调整"])
    elif deviation_pct > 5:
        return random.choice(["加班赶工", "效率提升", "工艺优化"])
    else:
        return "正常执行"


# ============================================================================
# 2. 结果推演 - 数据生成器
# ============================================================================

class SimulationDataGenerator:
    """结果推演数据生成器 - 计划一体化场景"""

    @staticmethod
    def simulate_capacity_change(variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        产能调整推演
        模拟增加/减少产线或班次对交期、产量的影响
        变量：target_line（产线）、adjustment_type（增/减）、adjustment_value（调整量）
        """
        line = variables.get("产线", random.choice(PRODUCTION_LINES))
        adj_type = variables.get("调整类型", "增加班次")
        adj_value = variables.get("调整量", 1)

        base_capacity = 1500
        base_lead_time = 15  # 天

        if adj_type == "增加班次":
            new_capacity = base_capacity * (1 + adj_value * 0.3)
            new_lead_time = max(5, base_lead_time - adj_value * 2)
            impact = "正面"
        elif adj_type == "增加产线":
            new_capacity = base_capacity * (1 + adj_value * 1.0)
            new_lead_time = max(3, base_lead_time - adj_value * 5)
            impact = "正面"
        elif adj_type == "减少班次":
            new_capacity = base_capacity * max(0.3, 1 - adj_value * 0.3)
            new_lead_time = base_lead_time + adj_value * 3
            impact = "负面"
        else:
            new_capacity = base_capacity
            new_lead_time = base_lead_time
            impact = "无变化"

        return {
            "scenario": "产能调整推演",
            "target_line": line,
            "adjustment": f"{adj_type} × {adj_value}",
            "base": {
                "daily_capacity": base_capacity,
                "lead_time_days": base_lead_time,
            },
            "forecast": {
                "daily_capacity": round(new_capacity, 0),
                "lead_time_days": round(new_lead_time, 1),
                "capacity_change_pct": round((new_capacity / base_capacity - 1) * 100, 1),
            },
            "impact": impact,
            "risk": _get_simulation_risk(impact),
        }

    @staticmethod
    def simulate_order_priority(variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        订单优先级/插单推演
        模拟紧急插单对现有计划的影响
        变量：priority（优先级）、urgent_count（紧急订单数）
        """
        urgent_count = variables.get("紧急订单数", 2)
        current_orders = 10
        base_completion_rate = 90

        # 插单后影响
        new_completion_rate = max(50, base_completion_rate - urgent_count * 5)
        affected_orders = min(urgent_count * 3, current_orders)

        scenarios = [
            {
                "label": f"插{urgent_count}单后",
                "on_time_rate": new_completion_rate,
                "affected_orders": affected_orders,
                "avg_delay_days": round(urgent_count * 2.5, 1),
            },
            {
                "label": "当前状态",
                "on_time_rate": base_completion_rate,
                "affected_orders": 0,
                "avg_delay_days": 0.5,
            },
        ]

        return {
            "scenario": "订单优先级推演",
            "urgent_orders": urgent_count,
            "scenarios": scenarios,
            "recommendation": _get_order_recommendation(urgent_count),
        }

    @staticmethod
    def simulate_material_delay(variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        物料供应延迟推演
        模拟关键物料延迟到货对生产的影响
        变量：material（物料名）、delay_days（延迟天数）
        """
        material = variables.get("物料", random.choice(MATERIALS))
        delay_days = variables.get("延迟天数", 3)

        affected_lines = random.sample(PRODUCTION_LINES, k=min(3, len(PRODUCTION_LINES)))
        affected_lines_str = "、".join(affected_lines)

        # 级联影响
        cascade = []
        cumulative_delay = delay_days
        for i, line in enumerate(affected_lines):
            cascade.append({
                "stage": f"第{i+1}环节",
                "line": line,
                "cumulative_delay_days": round(cumulative_delay, 1),
                "impact_desc": f"因物料{material}延迟，{line}计划延后{cumulative_delay:.1f}天",
            })
            cumulative_delay += random.uniform(1, 2)

        total_delay = round(cumulative_delay, 1)

        return {
            "scenario": "物料供应延迟推演",
            "material": material,
            "delay_days": delay_days,
            "affected_lines": affected_lines_str,
            "total_project_delay": total_delay,
            "cascade_effects": cascade,
            "mitigation": _get_mitigation_suggestions(delay_days),
        }

    @staticmethod
    def simulate_resource_reallocation(variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        资源重新分配推演
        模拟将资源从A产线调配到B产线的效果
        变量：source_line（来源产线）、target_line（目标产线）、allocation_pct（调配比例）
        """
        source = variables.get("来源产线", PRODUCTION_LINES[0])
        target = variables.get("目标产线", PRODUCTION_LINES[-1])
        alloc_pct = variables.get("调配比例", 20)

        source_before = {"capacity": 1200, "utilization": 75}
        target_before = {"capacity": 1000, "utilization": 88}

        source_after = {
            "capacity": round(1200 * (1 - alloc_pct / 100), 0),
            "utilization": min(100, 75 * 1200 / (1200 * (1 - alloc_pct / 100))),
        }
        target_after = {
            "capacity": round(1000 * (1 + alloc_pct / 100), 0),
            "utilization": max(50, 88 * 1000 / (1000 * (1 + alloc_pct / 100))),
        }

        return {
            "scenario": "资源重新分配推演",
            "source_line": source,
            "target_line": target,
            "allocation_pct": alloc_pct,
            "before": {
                source: source_before,
                target: target_before,
            },
            "after": {
                source: source_after,
                target: target_after,
            },
            "net_benefit": _evaluate_reallocation(source_before, target_before, source_after, target_after, alloc_pct),
        }


def _get_simulation_risk(impact: str) -> str:
    if impact == "正面":
        return "需关注人员调配和物料供应能否跟上产能增长"
    elif impact == "负面":
        return "订单交付存在延期风险，建议提前与客户沟通"
    return "当前调整影响较小"


def _get_order_recommendation(urgent_count: int) -> str:
    if urgent_count >= 5:
        return "插单量过大，建议评估部分订单外协或延期非关键订单"
    elif urgent_count >= 3:
        return "建议优先保障紧急订单，对非紧急订单重新排期"
    else:
        return "可正常消化，建议预留10%产能应对突发"


def _get_mitigation_suggestions(delay_days: float) -> str:
    if delay_days > 7:
        return "建议启用备选供应商、调整生产序列、增加加班"
    elif delay_days > 3:
        return "建议调整后续工序排程、启用安全库存"
    return "当前库存可缓冲，建议密切跟踪物流"


def _evaluate_reallocation(
    src_before: dict, tgt_before: dict,
    src_after: dict, tgt_after: dict, alloc_pct: float
) -> str:
    """评估资源调配的净收益"""
    src_util_change = src_after["utilization"] - src_before["utilization"]
    tgt_util_change = tgt_after["utilization"] - tgt_before["utilization"]
    if tgt_util_change > 5 and src_util_change < 10:
        return f"正向收益：目标产线利用率提升，来源产线仍有裕度"
    elif tgt_util_change < -5:
        return f"不推荐：目标产线负载未降低，调配效果有限"
    return f"建议小幅试调：{alloc_pct}%调配比例基本合理"


# ============================================================================
# 3. 数据下沉(根因) - 数据生成器
# ============================================================================

class RootCauseDataGenerator:
    """数据下沉/根因分析数据生成器 - 计划一体化场景"""

    @staticmethod
    def analyze_delay_root_cause(problem: str, indicators: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        工期延误根因分析
        通过数据下钻分析各环节的延迟贡献度
        """
        dimensions = [
            {"name": "物料到货延迟", "contribution": 35.6, "detail": "关键物料钢板-S355J2延迟3天到货"},
            {"name": "设备故障停机", "contribution": 28.3, "detail": "冲压产线A设备故障，停机16小时"},
            {"name": "人员不足", "contribution": 18.2, "detail": "焊接班组请假3人，产能下降40%"},
            {"name": "工艺变更", "contribution": 10.5, "detail": "产品P3工艺临时变更，增加调试时间"},
            {"name": "质检返工", "contribution": 7.4, "detail": "涂装一次合格率下降，返工增加"},
        ]

        return {
            "problem": problem,
            "analysis_type": "工期延误根因分析",
            "dimensions": dimensions,
            "primary_cause": dimensions[0]["name"],
            "primary_contribution": dimensions[0]["contribution"],
            "recommendations": [
                "建立关键物料安全库存制度，阈值设为7天用量",
                "实施设备预防性维护计划，降低非计划停机",
                "优化人员备份机制，关键岗位设置AB角",
            ],
        }

    @staticmethod
    def analyze_capacity_bottleneck(problem: str, indicators: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        产能瓶颈根因分析
        数据下钻定位真正的产能瓶颈环节
        """
        line_data = [
            {"name": "涂装产线C", "utilization": 97.5, "queue_length": 48, "cycle_time": 22.5, "is_bottleneck": True},
            {"name": "总装产线D", "utilization": 89.2, "queue_length": 32, "cycle_time": 18.0, "is_bottleneck": False},
            {"name": "焊接产线B", "utilization": 82.1, "queue_length": 15, "cycle_time": 14.2, "is_bottleneck": False},
            {"name": "冲压产线A", "utilization": 71.8, "queue_length": 8, "cycle_time": 10.5, "is_bottleneck": False},
            {"name": "检测产线E", "utilization": 65.4, "queue_length": 5, "cycle_time": 8.0, "is_bottleneck": False},
        ]

        bottleneck_line = [l for l in line_data if l["is_bottleneck"]][0]

        return {
            "problem": problem,
            "analysis_type": "产能瓶颈根因分析",
            "bottleneck_line": bottleneck_line["name"],
            "bottleneck_utilization": bottleneck_line["utilization"],
            "line_details": line_data,
            "root_causes": [
                "涂装工艺节拍长，为全流程最慢环节",
                "前道工序（焊接）产出堆积，造成在制品积压",
                "设备老化导致异常停机率高于其他产线",
            ],
            "recommendations": [
                "对涂装产线C进行工艺优化，目标降低节拍至18min",
                "增设涂装缓冲区，缓解前道工序积压",
                "评估涂装设备升级或增加并行工位方案",
            ],
        }

    @staticmethod
    def analyze_material_shortage(problem: str, indicators: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        物料短缺根因分析
        数据下钻分析缺料的根本原因
        """
        shortage_detail = [
            {"material": "钢板-S355J2", "shortage_qty": 1200, "root_cause": "供应商产能不足，交付延迟5天",
             "affected_lines": "冲压产线A、焊接产线B"},
            {"material": "电子元件-IC", "shortage_qty": 850, "root_cause": "国际市场缺货，采购周期延长",
             "affected_lines": "检测产线E"},
            {"material": "密封圈-NBR", "shortage_qty": 500, "root_cause": "质量不合格批次退货，补货中",
             "affected_lines": "总装产线D"},
        ]

        return {
            "problem": problem,
            "analysis_type": "物料短缺根因分析",
            "shortage_items": shortage_detail,
            "total_shortage_value": sum(s["shortage_qty"] for s in shortage_detail),
            "summary": {
                "supplier_issue_count": 2,
                "quality_issue_count": 1,
                "logistics_issue_count": 0,
            },
            "recommendations": [
                "开发第二供应商，降低单源供应风险",
                "建立关键物料安全库存，按ABC分类设定阈值",
                "加强来料检验流程，避免不合格批次流入产线",
            ],
        }

    @staticmethod
    def analyze_quality_fluctuation(problem: str, indicators: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        质量波动根因分析
        下钻到具体工艺/参数层面分析质量异常
        """
        defect_data = [
            {"defect_type": "尺寸超差", "count": 156, "pct": 42.3, "line": "焊接产线B", "root": "焊机参数偏移"},
            {"defect_type": "表面缺陷", "count": 98, "pct": 26.6, "line": "涂装产线C", "root": "喷涂压力波动"},
            {"defect_type": "装配不良", "count": 67, "pct": 18.2, "line": "总装产线D", "root": "扭矩工具未校准"},
            {"defect_type": "密封不严", "count": 48, "pct": 13.0, "line": "总装产线D", "root": "密封圈批次异常"},
        ]

        return {
            "problem": problem,
            "analysis_type": "质量波动根因分析",
            "defect_analysis": defect_data,
            "primary_defect": defect_data[0]["defect_type"],
            "primary_line": defect_data[0]["line"],
            "total_defects": sum(d["count"] for d in defect_data),
            "recommendations": [
                f"立即校准{defect_data[0]['line']}设备参数，重点检查{defect_data[0]['root']}",
                "实施SPC（统计过程控制），对关键工艺参数实时监控",
                "对密封圈批次进行全检，追溯供应商质量问题",
            ],
        }

    @staticmethod
    def analyze_cost_overrun(problem: str, indicators: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        成本超预算根因分析
        """
        cost_breakdown = [
            {"item": "原材料涨价", "overrun": 28.5, "pct": 38.2, "root": "上游钢材市场价格上涨15%"},
            {"item": "加班费用", "overrun": 18.2, "pct": 24.4, "root": "赶工导致加班工时增加40%"},
            {"item": "维修费用", "overrun": 12.8, "pct": 17.2, "root": "涂装产线C老化，维修频次增加"},
            {"item": "物流费用", "overrun": 8.5, "pct": 11.4, "root": "紧急空运补货增加运输成本"},
            {"item": "质量返工", "overrun": 6.6, "pct": 8.8, "root": "一次合格率下降，返工材料损耗"},
        ]

        return {
            "problem": problem,
            "analysis_type": "成本超预算根因分析",
            "cost_items": cost_breakdown,
            "total_overrun": sum(c["overrun"] for c in cost_breakdown),
            "primary_cost_driver": cost_breakdown[0]["item"],
            "recommendations": [
                "与核心供应商签订长期协议锁定价格",
                "优化排产减少加班需求，评估自动化方案",
                "制定老旧设备更新计划，降低维修频次",
            ],
        }


# ============================================================================
# 工厂方法 - 统一入口
# ============================================================================

def get_report_data(report_type: str, start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    dimensions: Optional[List[str]] = None,
                    metrics: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    报表数据统一获取入口
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    gen = ReportDataGenerator()

    report_map = {
        "计划执行报表": gen.generate_plan_execution_report,
        "物料需求报表": gen.generate_material_requirement_report,
        "产能分析报表": gen.generate_capacity_report,
        "进度跟踪报表": gen.generate_progress_report,
        "质量分析报表": gen.generate_quality_report,
    }

    if report_type in report_map:
        return report_map[report_type](start_date, end_date)

    # 默认返回计划执行报表
    return gen.generate_plan_execution_report(start_date, end_date)


def get_simulation_data(scenario: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    推演数据统一获取入口
    """
    if not variables:
        variables = {}

    sim = SimulationDataGenerator()

    sim_map = {
        "产能调整": sim.simulate_capacity_change,
        "订单插单": sim.simulate_order_priority,
        "物料延迟": sim.simulate_material_delay,
        "资源调配": sim.simulate_resource_reallocation,
    }

    # 关键词匹配
    if "产能" in scenario or "班次" in scenario or "产线" in scenario:
        return sim.simulate_capacity_change(variables)
    elif "订单" in scenario or "插单" in scenario or "优先级" in scenario:
        return sim.simulate_order_priority(variables)
    elif "物料" in scenario or "供应" in scenario or "延迟" in scenario:
        return sim.simulate_material_delay(variables)
    elif "资源" in scenario or "调配" in scenario or "分配" in scenario:
        return sim.simulate_resource_reallocation(variables)

    return sim.simulate_capacity_change(variables)


def get_root_cause_data(problem: str, indicators: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    根因分析数据统一获取入口
    """
    rca = RootCauseDataGenerator()

    if "工期" in problem or "延期" in problem or "交期" in problem or "进度" in problem:
        return rca.analyze_delay_root_cause(problem, indicators)
    elif "产能" in problem or "瓶颈" in problem:
        return rca.analyze_capacity_bottleneck(problem, indicators)
    elif "物料" in problem or "缺料" in problem or "短缺" in problem or "供应" in problem:
        return rca.analyze_material_shortage(problem, indicators)
    elif "质量" in problem or "缺陷" in problem or "合格" in problem:
        return rca.analyze_quality_fluctuation(problem, indicators)
    elif "成本" in problem or "费用" in problem or "预算" in problem:
        return rca.analyze_cost_overrun(problem, indicators)

    return rca.analyze_delay_root_cause(problem, indicators)
