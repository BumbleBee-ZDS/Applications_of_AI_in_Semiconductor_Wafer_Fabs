"""
FabCapacityAgent - 历史分析页面

职责:
  1) 日期范围选择 (默认近 30 天)
  2) 日产出 / OEE / CycleTime 趋势曲线
  3) WIP 与 Move 历史对比
  4) 瓶颈诊断报告 (BottleneckDetector)
  5) 异常事件分析 (设备故障 / PM 停机 Pareto)
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
from utils.helpers import get_logger, safe_round, to_pct, process_cn_name, parse_datetime
from utils.constants import (
    ALL_PROCESSES,
    PROCESS_NAME_CN,
    TABLE_DAILY_OUTPUT,
    TABLE_EQUIPMENT_EVENTS,
    TABLE_LOT_HISTORY,
    EVENT_EQUIP_DOWN,
    EVENT_PM_START,
    EVENT_SETUP_START,
    CHART_PALETTE,
    KPI_OEE,
    KPI_CYCLE_TIME,
)
from models.database import get_db
from models.capacity import DailyOutputDAO
from services.bottleneck_detector import BottleneckDetector
from services.capacity_calculator import get_calculator

logger = get_logger("PageHistory", level="INFO")

init_page("历史分析", icon="📈", subtitle="Trend / Anomaly / Bottleneck Diagnosis")


# =============================================================================
# 数据加载
# =============================================================================

@st.cache_data(ttl=300, show_spinner="正在加载历史数据...")
def load_history_data(start_date: str, end_date: str) -> dict:
    """加载历史分析数据 (5min 缓存)。"""
    db = get_db()
    dao = DailyOutputDAO()

    # daily_output 表数据
    daily_df = dao.between(start_date, end_date, product_type="ALL")

    # 工序级历史聚合 (按天)
    proc_df = db.query_df(f"""
        SELECT DATE(start_time) AS stat_date,
               process,
               COUNT(*) AS move_cnt,
               SUM(CASE WHEN end_time IS NOT NULL THEN output_qty ELSE 0 END) AS out_qty,
               AVG(process_time_h) AS avg_pt,
               AVG(wait_time_h) AS avg_wait
        FROM {TABLE_LOT_HISTORY}
        WHERE start_time >= ? AND start_time <= ?
          AND process IS NOT NULL
        GROUP BY DATE(start_time), process
        ORDER BY stat_date ASC, process
    """, (start_date, end_date + " 23:59:59"))

    # 设备事件 Pareto (故障 + PM + 换型)
    events_df = db.query_df(f"""
        SELECT event_type, equip_id,
               COUNT(*) AS cnt,
               SUM(duration_h) AS total_h,
               AVG(duration_h) AS avg_h
        FROM {TABLE_EQUIPMENT_EVENTS}
        WHERE event_time >= ? AND event_time <= ?
        GROUP BY event_type
        ORDER BY total_h DESC
    """, (start_date, end_date + " 23:59:59"))

    # 故障 Top 设备
    down_df = db.query_df(f"""
        SELECT equip_id, reason,
               COUNT(*) AS cnt,
               SUM(duration_h) AS total_h
        FROM {TABLE_EQUIPMENT_EVENTS}
        WHERE event_type = ?
          AND event_time >= ? AND event_time <= ?
        GROUP BY equip_id
        ORDER BY total_h DESC
        LIMIT 15
    """, (EVENT_EQUIP_DOWN, start_date, end_date + " 23:59:59"))

    return {
        "daily_df": daily_df,
        "proc_df": proc_df,
        "events_df": events_df,
        "down_df": down_df,
    }


@st.cache_data(ttl=300, show_spinner="正在生成瓶颈诊断报告...")
def run_bottleneck_analysis(window_hours: int) -> dict:
    """运行瓶颈检测,返回结构化报告 (5min 缓存)。

    BottleneckReport 字段:
      bottlenecks: List[dict] 含 process/process_cn/score/utilization/oee/
                   wip_wafers/down_hours/flag_high_util/flag_high_wip/flag_high_down
      causes:      List[BottleneckCause] (process/dimension/severity_score/
                   quantitative_indicator/detail)
      suggestions: List[BottleneckSuggestion] (process/category/action/
                   expected_improvement/priority/effort)
    """
    bd = BottleneckDetector()
    report = bd.detect_and_report(window_hours=window_hours)

    # bottlenecks 已经是 dict
    bottlenecks = []
    for b in report.bottlenecks:
        if isinstance(b, dict):
            bottlenecks.append(b)
        elif hasattr(b, "__dict__"):
            bottlenecks.append(vars(b))

    # causes 转 dict
    causes = []
    for c in report.causes:
        if isinstance(c, dict):
            causes.append(c)
        elif hasattr(c, "__dict__"):
            causes.append(vars(c))

    # suggestions 转 dict
    suggestions = []
    for s in report.suggestions:
        if isinstance(s, dict):
            suggestions.append(s)
        elif hasattr(s, "__dict__"):
            suggestions.append(vars(s))

    return {
        "snapshot_time": report.snapshot_time.strftime("%Y-%m-%d %H:%M:%S") if report.snapshot_time else "",
        "window_hours": report.window_hours,
        "bottlenecks": bottlenecks,
        "causes": causes,
        "suggestions": suggestions,
        "utilization_breakdown": report.utilization_breakdown.to_dict(orient="records") if hasattr(report.utilization_breakdown, "to_dict") else [],
        "llm_enhanced": report.llm_enhanced,
    }


# =============================================================================
# 顶部控制栏: 日期范围
# =============================================================================

today = dt.date.today()
default_start = today - dt.timedelta(days=30)

col_d1, col_d2, col_d3 = st.columns([2, 2, 2])
with col_d1:
    start_date = st.date_input("📅 开始日期", value=default_start, max_value=today)
with col_d2:
    end_date = st.date_input("📅 结束日期", value=today, max_value=today)
with col_d3:
    bn_window = st.slider("🔍 瓶颈分析窗口 (小时)", min_value=6, max_value=168, value=24, step=6)

if start_date > end_date:
    st.error("开始日期不能晚于结束日期")
    st.stop()

start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

# 加载数据
data = load_history_data(start_str, end_str)
daily_df = data["daily_df"]
proc_df = data["proc_df"]
events_df = data["events_df"]
down_df = data["down_df"]

# =============================================================================
# 第 1 区: 概览 KPI
# =============================================================================

st.markdown(f"### 📊 {start_str} ~ {end_str} 概览")

days_span = (end_date - start_date).days + 1
total_output = int(daily_df["output_wafers"].sum()) if daily_df is not None and not daily_df.empty else 0
avg_oee = float(daily_df["avg_oee"].mean()) if daily_df is not None and "avg_oee" in daily_df.columns and not daily_df.empty else 0
avg_ct = float(daily_df["avg_cycle_time_h"].mean()) if daily_df is not None and "avg_cycle_time_h" in daily_df.columns and not daily_df.empty else 0
total_move = int(proc_df["move_cnt"].sum()) if proc_df is not None and not proc_df.empty else 0
total_downtime = float(events_df["total_h"].sum()) if events_df is not None and not events_df.empty else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: st.metric("分析天数", f"{days_span}")
with c2: st.metric("累计产出", f"{total_output:,} 片")
with c3: st.metric("平均 OEE", to_pct(avg_oee))
with c4: st.metric("平均 CycleTime", f"{safe_round(avg_ct, 1)} h")
with c5: st.metric("累计 Move", f"{total_move:,}")
with c6: st.metric("累计停机", f"{safe_round(total_downtime, 1)} h")

st.markdown("---")

# =============================================================================
# 第 2 区: 趋势曲线 (日产出 / OEE / CycleTime)
# =============================================================================

st.markdown("### 📈 趋势分析")

tab1, tab2, tab3 = st.tabs(["📊 日产出趋势", "⚙️ OEE 趋势", "⏱ CycleTime 趋势"])

if daily_df is None or daily_df.empty:
    for tab in [tab1, tab2, tab3]:
        with tab:
            st.info("所选日期范围内无 daily_output 数据")
else:
    df = daily_df.copy()
    if "stat_date" in df.columns:
        df["date"] = pd.to_datetime(df["stat_date"])

    with tab1:
        fig = px.bar(
            df, x="date", y="output_wafers",
            color_discrete_sequence=[CHART_PALETTE[0]],
            labels={"output_wafers": "日产出 (片)", "date": "日期"},
        )
        # 加 7 天移动平均线
        df["ma7"] = df["output_wafers"].rolling(window=7, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["ma7"],
            name="7日移动平均", mode="lines",
            line=dict(color=CHART_PALETTE[1], width=2.5),
        ))
        fig.update_layout(title="日产出趋势 (柱: 实际, 线: 7日MA)")
        dark_chart_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if "avg_oee" in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["avg_oee"],
                mode="lines+markers", name="OEE",
                line=dict(color=CHART_PALETTE[3], width=2.5),
                marker=dict(size=6),
            ))
            fig.add_trace(go.Scatter(
                x=df["date"], y=[0.85] * len(df),
                mode="lines", name="目标 85%",
                line=dict(color=CHART_PALETTE[5], dash="dash", width=1.5),
            ))
            fig.update_layout(
                title="平均 OEE 趋势 (虚线: 85% 目标)",
                yaxis_tickformat=".0%", yaxis_range=[0, 1],
            )
            dark_chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("无 OEE 数据")

    with tab3:
        if "avg_cycle_time_h" in df.columns:
            fig = px.area(
                df, x="date", y="avg_cycle_time_h",
                color_discrete_sequence=[CHART_PALETTE[6]],
                labels={"avg_cycle_time_h": "CycleTime (h)", "date": "日期"},
            )
            fig.update_layout(title="平均 CycleTime 趋势")
            dark_chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("无 CycleTime 数据")

st.markdown("---")

# =============================================================================
# 第 3 区: 工序级热力图 (按天 × 工序的产出)
# =============================================================================

st.markdown("### 🔥 工序级产出热力图 (按天)")

if proc_df is None or proc_df.empty:
    st.info("所选日期范围内无工序历史数据")
else:
    df_p = proc_df.copy()
    df_p["date"] = pd.to_datetime(df_p["stat_date"]).dt.strftime("%m-%d")
    df_p["工序"] = df_p["process"].apply(process_cn_name)

    pivot = df_p.pivot_table(index="工序", columns="date", values="out_qty", aggfunc="sum").fillna(0)

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="Blues",
        text=pivot.values.astype(int),
        texttemplate="%{text}",
        textfont={"size": 9},
    ))
    fig.update_layout(
        title="工序 × 日期 产出热力图 (片)",
        xaxis_title="日期", yaxis_title="工序",
        height=400,
    )
    dark_chart_layout(fig, height=400)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# =============================================================================
# 第 4 区: 瓶颈诊断报告
# =============================================================================

st.markdown(f"### 🎯 瓶颈诊断报告 (近 {bn_window}h)")

if st.button("▶ 重新生成瓶颈报告", use_container_width=False):
    st.cache_data.clear()
    st.rerun()

bn_report = run_bottleneck_analysis(bn_window)

if bn_report.get("llm_enhanced"):
    st.success(f"✓ 报告已用 LLM 增强 (生成于 {bn_report.get('snapshot_time', '')})")
else:
    st.info(f"ℹ️ 报告使用本地算法 (生成于 {bn_report.get('snapshot_time', '')})")

# 瓶颈列表
bottlenecks = bn_report.get("bottlenecks", [])
if bottlenecks:
    st.markdown("#### 🚨 识别到的瓶颈工序")
    bn_rows = []
    for b in bottlenecks:
        if isinstance(b, dict):
            # 标记是否高利用/高WIP/高停机
            flags = []
            if b.get("flag_high_util"): flags.append("高利用")
            if b.get("flag_high_wip"): flags.append("高WIP")
            if b.get("flag_high_down"): flags.append("高停机")
            bn_rows.append({
                "工序": b.get("process_cn") or process_cn_name(b.get("process", "")),
                "瓶颈评分": safe_round(b.get("score", 0), 3),
                "利用率": to_pct(b.get("utilization", 0)),
                "OEE": to_pct(b.get("oee", 0)),
                "WIP(片)": int(b.get("wip_wafers", 0)),
                "停机(h)": safe_round(b.get("down_hours", 0), 1),
                "异常标记": " / ".join(flags) if flags else "-",
            })
    if bn_rows:
        st.dataframe(pd.DataFrame(bn_rows), use_container_width=True, hide_index=True)

# 原因分析
causes = bn_report.get("causes", [])
if causes:
    st.markdown("#### 🔍 瓶颈原因分析")
    cause_rows = []
    for c in causes:
        if isinstance(c, dict):
            cause_rows.append({
                "工序": process_cn_name(c.get("process", "")),
                "维度": c.get("dimension", ""),
                "严重度": safe_round(c.get("severity_score", 0), 2),
                "量化指标": c.get("quantitative_indicator", ""),
                "详情": c.get("detail", ""),
            })
    if cause_rows:
        st.dataframe(pd.DataFrame(cause_rows), use_container_width=True, hide_index=True)

# 优化建议
suggestions = bn_report.get("suggestions", [])
if suggestions:
    st.markdown("#### 💡 优化建议")
    sug_rows = []
    for s in suggestions:
        if isinstance(s, dict):
            ei = s.get("expected_improvement", {}) or {}
            ei_str = ""
            if isinstance(ei, dict):
                parts = []
                if "oee_increase" in ei: parts.append(f"OEE+{safe_round(ei['oee_increase']*100, 2)}%")
                if "capacity_increase_pct" in ei: parts.append(f"产能+{safe_round(ei['capacity_increase_pct'], 2)}%")
                if "weekly_wafers_gain" in ei: parts.append(f"周+{int(ei['weekly_wafers_gain'])}片")
                ei_str = " / ".join(parts)
            sug_rows.append({
                "工序": process_cn_name(s.get("process", "")),
                "类别": s.get("category", ""),
                "建议动作": s.get("action", ""),
                "预期改善": ei_str,
                "优先级": s.get("priority", "-"),
                "工作量": s.get("effort", "-"),
            })
    if sug_rows:
        st.dataframe(pd.DataFrame(sug_rows), use_container_width=True, hide_index=True)

st.markdown("---")

# =============================================================================
# 第 5 区: 设备停机 Pareto
# =============================================================================

st.markdown("### 📉 设备停机 Pareto 分析")

tab_p1, tab_p2 = st.tabs(["📊 事件类型分布", "🔧 故障 Top15 设备"])

with tab_p1:
    if events_df is None or events_df.empty:
        st.info("所选日期范围内无设备事件数据")
    else:
        df_e = events_df.copy()
        df_e["累计占比"] = df_e["total_h"].cumsum() / df_e["total_h"].sum() * 100

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_e["event_type"], y=df_e["total_h"],
            name="累计停机时长 (h)",
            marker_color=CHART_PALETTE[5],
            text=df_e["total_h"].apply(lambda v: f"{safe_round(v, 1)}h"),
            textposition="outside",
        ))
        fig.add_trace(go.Scatter(
            x=df_e["event_type"], y=df_e["累计占比"],
            name="累计占比 (%)", mode="lines+markers",
            line=dict(color=CHART_PALETTE[1], width=2),
            yaxis="y2",
        ))
        fig.update_layout(
            title="设备事件 Pareto (按类型)",
            yaxis=dict(title="停机时长 (h)"),
            yaxis2=dict(title="累计占比 (%)", overlaying="y", side="right", range=[0, 105]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        dark_chart_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df_e, use_container_width=True, hide_index=True)

with tab_p2:
    if down_df is None or down_df.empty:
        st.info("所选日期范围内无故障记录")
    else:
        df_d = down_df.copy()
        df_d = df_d.sort_values("total_h", ascending=True)

        fig = px.bar(
            df_d, x="total_h", y="equip_id", orientation="h",
            color_discrete_sequence=[CHART_PALETTE[5]],
            labels={"total_h": "累计故障时长 (h)", "equip_id": "设备 ID"},
            text=df_d["total_h"].apply(lambda v: f"{safe_round(v, 1)}h"),
        )
        fig.update_layout(title="故障 Top15 设备 (按累计时长)", height=500)
        fig.update_traces(textposition="outside")
        dark_chart_layout(fig, height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df_d, use_container_width=True, hide_index=True)

st.caption(f"FabCapacityAgent · 历史分析 · 分析窗口 {start_str} ~ {end_str}")
