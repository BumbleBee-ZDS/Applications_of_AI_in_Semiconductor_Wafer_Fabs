"""
FabCapacityAgent - 产能规划页面

职责:
  1) 未来 7/14/30 天产能预测 (含置信区间)
  2) What-If 情景对比 (Baseline / 加设备 / 调OEE / PM优化 / 新产品 / 组合)
  3) 自定义情景构建器
  4) 蒙特卡洛风险评估
"""

import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime as dt

from utils.ui_components import init_page, dark_chart_layout
from utils.helpers import get_logger, safe_round, to_pct, process_cn_name
from utils.constants import (
    ALL_PROCESSES,
    PROCESS_NAME_CN,
    CHART_PALETTE,
)
from services.predictor import Predictor
from services.what_if_simulator import WhatIfSimulator, ScenarioConfig

logger = get_logger("PagePlanning", level="INFO")

init_page("产能规划", icon="🎯", subtitle="Forecast / What-If / Monte Carlo")


# =============================================================================
# 数据加载
# =============================================================================

@st.cache_data(ttl=300, show_spinner="正在生成产能预测...")
def run_forecast(horizon: int, history: int, use_llm: bool) -> dict:
    """运行产能预测,返回 ForecastResult 序列化字典。"""
    pred = Predictor()
    fr = pred.forecast_output(
        horizon_days=horizon,
        history_days=history,
        target="output_wafers",
        product_type="ALL",
        use_llm=use_llm,
    )
    return {
        "target": fr.target,
        "horizon_days": fr.horizon_days,
        "method": fr.method,
        "history_dates": [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in fr.history_dates],
        "history_values": list(fr.history_values),
        "future_dates": [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in fr.future_dates],
        "predicted": list(fr.predicted),
        "lower_ci": list(fr.lower_ci),
        "upper_ci": list(fr.upper_ci),
        "mape": fr.mape,
        "used_llm": fr.used_llm,
    }


@st.cache_data(ttl=300, show_spinner="正在运行 What-If 仿真...")
def run_what_if() -> dict:
    """运行所有预设 What-If 场景对比。"""
    ws = WhatIfSimulator()
    scenarios = ws.preset_scenarios()
    df = ws.compare_scenarios(scenarios)

    # 同时跑 baseline 单独取数值
    baseline = ws.run_baseline()
    return {
        "df": df.to_dict(orient="records"),
        "baseline_wafers": baseline.total_effective_wafers_per_week,
        "baseline_oee": baseline.overall_oee,
    }


# =============================================================================
# 顶部控制栏
# =============================================================================

tab_main1, tab_main2, tab_main3 = st.tabs([
    "📈 产能预测", "🎯 What-If 仿真", "🛠 自定义情景",
])

# =============================================================================
# Tab 1: 产能预测
# =============================================================================

with tab_main1:
    st.markdown("### 📈 未来产能预测")

    col_p1, col_p2, col_p3 = st.columns([2, 2, 1])
    with col_p1:
        horizon = st.select_slider("预测天数", options=[7, 14, 30, 60], value=7)
    with col_p2:
        history = st.select_slider("历史窗口 (天)", options=[30, 60, 90, 120], value=60)
    with col_p3:
        use_llm = st.checkbox("启用 LLM 增强", value=False)

    if st.button("▶ 生成预测", key="btn_forecast", use_container_width=True):
        st.cache_data.clear()

    fc = run_forecast(horizon, history, use_llm)

    # KPI
    total_pred = sum(fc["predicted"]) if fc["predicted"] else 0
    avg_pred = total_pred / len(fc["predicted"]) if fc["predicted"] else 0
    mape = fc.get("mape", 0)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric(f"未来 {horizon} 天预测总量", f"{int(total_pred):,} 片")
    with c2: st.metric("日均预测", f"{int(avg_pred):,} 片/天")
    with c3: st.metric("预测方法", fc.get("method", "N/A"))
    with c4:
        mape_str = f"{safe_round(mape*100, 2)}%" if mape else "N/A"
        st.metric("MAPE 误差", mape_str)

    if fc.get("used_llm"):
        st.success("✓ 已启用 LLM 增强 (DeepSeek/Qwen)")
    else:
        st.info("ℹ️ 使用本地统计模型 (移动平均 + 线性回归)")

    # 预测图 (历史 + 预测 + CI)
    fig = go.Figure()

    # 历史
    fig.add_trace(go.Scatter(
        x=fc["history_dates"], y=fc["history_values"],
        name="历史实际", mode="lines+markers",
        line=dict(color=CHART_PALETTE[0], width=2),
        marker=dict(size=5),
    ))

    # 预测
    fig.add_trace(go.Scatter(
        x=fc["future_dates"], y=fc["predicted"],
        name="预测值", mode="lines+markers",
        line=dict(color=CHART_PALETTE[1], width=2.5, dash="dash"),
        marker=dict(size=7),
    ))

    # 置信区间
    if fc["upper_ci"] and fc["lower_ci"]:
        fig.add_trace(go.Scatter(
            x=fc["future_dates"] + fc["future_dates"][::-1],
            y=fc["upper_ci"] + fc["lower_ci"][::-1],
            fill="toself", fillcolor="rgba(255,107,157,0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            name="95% 置信区间",
            hoverinfo="skip",
        ))

    fig.update_layout(
        title=f"日产出预测 (未来 {horizon} 天)",
        xaxis_title="日期", yaxis_title="日产出 (片)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    dark_chart_layout(fig, height=450)
    st.plotly_chart(fig, use_container_width=True)

    # 预测明细表
    pred_df = pd.DataFrame({
        "日期": fc["future_dates"],
        "预测产出(片)": [int(v) for v in fc["predicted"]],
        "下界(片)": [int(v) for v in fc["lower_ci"]] if fc["lower_ci"] else ["-"] * len(fc["predicted"]),
        "上界(片)": [int(v) for v in fc["upper_ci"]] if fc["upper_ci"] else ["-"] * len(fc["predicted"]),
    })
    st.dataframe(pred_df, use_container_width=True, hide_index=True)

# =============================================================================
# Tab 2: What-If 仿真
# =============================================================================

with tab_main2:
    st.markdown("### 🎯 What-If 情景仿真对比")

    if st.button("▶ 重新运行仿真", key="btn_whatif"):
        st.cache_data.clear()
        st.rerun()

    wi = run_what_if()
    df_scenarios = pd.DataFrame(wi["df"])
    baseline_wafers = wi["baseline_wafers"]

    if df_scenarios.empty:
        st.info("What-If 仿真无结果")
    else:
        # KPI
        best = df_scenarios.loc[df_scenarios["delta_wafers_per_week"].idxmax()] if "delta_wafers_per_week" in df_scenarios.columns else None
        worst = df_scenarios.loc[df_scenarios["delta_wafers_per_week"].idxmin()] if "delta_wafers_per_week" in df_scenarios.columns else None

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Baseline 周产能", f"{int(baseline_wafers):,} 片")
        with c2:
            if best is not None:
                st.metric("最佳情景", f"{best['name']}", delta=f"+{int(best['delta_wafers_per_week']):,} 片")
        with c3:
            if worst is not None:
                st.metric("最差情景", f"{worst['name']}", delta=f"{int(worst['delta_wafers_per_week']):+,} 片", delta_color="inverse")
        with c4: st.metric("情景总数", f"{len(df_scenarios)}")

        # 产能对比图
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_scenarios["name"],
            y=df_scenarios["total_effective_wafers_per_week"],
            name="周有效产能",
            marker_color=[CHART_PALETTE[0] if name == "Baseline" else CHART_PALETTE[1] for name in df_scenarios["name"]],
            text=df_scenarios["total_effective_wafers_per_week"].apply(lambda v: f"{int(v):,}"),
            textposition="outside",
        ))
        fig.update_layout(
            title="各情景周有效产能对比",
            xaxis_title="情景", yaxis_title="周产能 (片)",
        )
        dark_chart_layout(fig, height=420)
        st.plotly_chart(fig, use_container_width=True)

        # Delta 百分比图
        if "delta_pct" in df_scenarios.columns:
            fig2 = go.Figure()
            colors = [CHART_PALETTE[3] if v >= 0 else CHART_PALETTE[5] for v in df_scenarios["delta_pct"]]
            fig2.add_trace(go.Bar(
                x=df_scenarios["name"],
                y=df_scenarios["delta_pct"] * 100,
                marker_color=colors,
                text=df_scenarios["delta_pct"].apply(lambda v: f"{safe_round(v*100, 2)}%"),
                textposition="outside",
            ))
            fig2.update_layout(
                title="各情景相对 Baseline 的产能变化 (%)",
                xaxis_title="情景", yaxis_title="Δ 产能 (%)",
            )
            dark_chart_layout(fig2, height=380)
            st.plotly_chart(fig2, use_container_width=True)

        # 蒙特卡洛风险图 (P5/P50/P95)
        if all(c in df_scenarios.columns for c in ["mc_p5", "mc_p50", "mc_p95"]):
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=df_scenarios["name"], y=df_scenarios["mc_p95"],
                name="P95 (乐观)", marker_color=CHART_PALETTE[3],
            ))
            fig3.add_trace(go.Bar(
                x=df_scenarios["name"], y=df_scenarios["mc_p50"],
                name="P50 (中位)", marker_color=CHART_PALETTE[0],
            ))
            fig3.add_trace(go.Bar(
                x=df_scenarios["name"], y=df_scenarios["mc_p5"],
                name="P5 (悲观)", marker_color=CHART_PALETTE[5],
            ))
            fig3.update_layout(
                title="蒙特卡洛风险评估 (P5/P50/P95)",
                barmode="group",
                xaxis_title="情景", yaxis_title="周产能 (片)",
            )
            dark_chart_layout(fig3, height=420)
            st.plotly_chart(fig3, use_container_width=True)

        # 明细表
        st.markdown("#### 📋 情景明细表")
        show_cols = [c for c in [
            "name", "total_effective_wafers_per_week", "delta_wafers_per_week",
            "delta_pct", "overall_oee", "mc_p50", "mc_std", "risk_level",
        ] if c in df_scenarios.columns]
        df_show = df_scenarios[show_cols].copy()
        # 重命名
        rename_map = {
            "name": "情景",
            "total_effective_wafers_per_week": "周有效产能(片)",
            "delta_wafers_per_week": "Δ产能(片)",
            "delta_pct": "Δ%",
            "overall_oee": "OEE",
            "mc_p50": "MC P50",
            "mc_std": "MC 标准差",
            "risk_level": "风险等级",
        }
        df_show = df_show.rename(columns=rename_map)
        # 格式化
        if "Δ%" in df_show.columns:
            df_show["Δ%"] = df_show["Δ%"].apply(lambda v: f"{safe_round(v*100, 2)}%")
        if "OEE" in df_show.columns:
            df_show["OEE"] = df_show["OEE"].apply(lambda v: to_pct(v))
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# =============================================================================
# Tab 3: 自定义情景
# =============================================================================

with tab_main3:
    st.markdown("### 🛠 自定义 What-If 情景构建器")

    with st.form("custom_scenario_form"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            scen_name = st.text_input("情景名称", value="MyScenario", max_chars=30)
            scen_desc = st.text_area("情景描述", value="自定义情景", height=80)
            add_process = st.selectbox(
                "新增设备工序",
                options=["(不新增)"] + ALL_PROCESSES,
                format_func=lambda p: "(不新增)" if p == "(不新增)" else f"{p} ({process_cn_name(p)})",
            )
            add_count = st.slider("新增设备数", min_value=0, max_value=10, value=0)

        with col_s2:
            oee_delta = st.slider("OEE 调整 (百分点)", min_value=-15, max_value=15, value=0, step=1)
            new_product = st.checkbox("引入新产品需求", value=False)
            if new_product:
                demand_ratio = st.slider("新产品需求占比", min_value=0.05, max_value=0.30, value=0.10, step=0.05)
                new_product_name = st.text_input("新产品名称", value="NewProduct_X")
            else:
                demand_ratio = 0.0
                new_product_name = ""

            pm_optimize = st.checkbox("优化 PM 计划 (频率+50%, 时长-30%)", value=False)

        submitted = st.form_submit_button("▶ 运行自定义情景", use_container_width=True)

    if submitted:
        # 构建 ScenarioConfig
        add_equipment = {}
        if add_process != "(不新增)" and add_count > 0:
            add_equipment = {add_process: add_count}

        pm_changes = {}
        if pm_optimize:
            pm_changes = {"pm_frequency_h": 168 * 1.5, "pm_duration_h": 8 * 0.7}

        cfg = ScenarioConfig(
            name=scen_name or "Custom",
            description=scen_desc or "自定义情景",
            add_equipment=add_equipment,
            oee_delta=oee_delta / 100.0,  # float 类型, run_scenario 会自动转为统一调整
            new_product_demand_ratio=demand_ratio,
            new_product_name=new_product_name if new_product else None,
            pm_changes=pm_changes,
        )

        st.info(f"情景配置: {cfg.name} | 加设备={add_equipment} | OEE Δ={oee_delta}% | 新产品={new_product} | PM优化={pm_optimize}")

        try:
            ws = WhatIfSimulator()
            baseline = ws.run_baseline()
            result = ws.run_scenario(cfg)

            # 对比展示
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Baseline 周产能", f"{int(baseline.total_effective_wafers_per_week):,} 片")
            with c2: st.metric(f"{cfg.name} 周产能", f"{int(result.total_effective_wafers_per_week):,} 片")
            with c3:
                delta = result.delta_wafers_per_week
                st.metric("Δ 产能", f"{int(delta):+,} 片", delta=f"{int(delta):+,}")
            with c4:
                delta_pct = result.delta_pct
                st.metric("Δ %", f"{safe_round(delta_pct*100, 2)}%", delta=f"{safe_round(delta_pct*100, 2)}%")

            # 蒙特卡洛
            st.markdown("#### 🎲 蒙特卡洛风险评估")
            mc_c1, mc_c2, mc_c3, mc_c4 = st.columns(4)
            with mc_c1: st.metric("P5 (悲观)", f"{int(result.mc_p5):,} 片")
            with mc_c2: st.metric("P50 (中位)", f"{int(result.mc_p50):,} 片")
            with mc_c3: st.metric("P95 (乐观)", f"{int(result.mc_p95):,} 片")
            with mc_c4: st.metric("风险等级", result.risk_level)

            # 工序明细
            if result.process_summary:
                st.markdown("#### 📋 工序级产能明细")
                ps_df = pd.DataFrame(result.process_summary)
                if not ps_df.empty:
                    if "process" in ps_df.columns:
                        ps_df["工序"] = ps_df["process"].apply(process_cn_name)
                    st.dataframe(ps_df, use_container_width=True, hide_index=True)

        except Exception as exc:
            st.error(f"情景运行失败: {exc}")

st.caption(f"FabCapacityAgent · 产能规划 · 生成于 {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
