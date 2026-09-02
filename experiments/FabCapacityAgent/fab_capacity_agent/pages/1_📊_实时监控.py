"""
FabCapacityAgent - 实时监控页面

职责:
  1) 全厂设备状态实时看板 (饼图 + 工序列表)
  2) WIP 在制品分布 (按工序 / 按产品)
  3) 近 N 小时 Move / 产出趋势
  4) 设备明细表 (支持筛选工序/状态)

刷新策略: 手动刷新按钮 + st.cache_data TTL 缓存 60s
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

from utils.ui_components import init_page, dark_chart_layout, status_badge
from utils.helpers import get_logger, safe_round, to_pct, process_cn_name
from utils.constants import (
    ALL_PROCESSES,
    PROCESS_NAME_CN,
    EQUIP_STATUS_NAME_CN,
    EQUIP_STATUS_COLOR,
    EQUIP_STATUS_RUN,
    EQUIP_STATUS_IDLE,
    EQUIP_STATUS_DOWN,
    EQUIP_STATUS_PM,
    EQUIP_STATUS_SETUP,
    TABLE_EQUIPMENT,
    TABLE_LOT_HISTORY,
    CHART_PALETTE,
)
from models.database import get_db
from models.equipment import EquipmentDAO
from services.capacity_calculator import get_calculator

logger = get_logger("PageRealtime", level="INFO")

init_page("实时监控", icon="📊", subtitle="Equipment Status / WIP / Move · 实时看板")


# =============================================================================
# 数据加载 (缓存 60s)
# =============================================================================

@st.cache_data(ttl=60, show_spinner="正在加载实时数据...")
def load_realtime_data(window_hours: int = 24) -> dict:
    """加载实时监控所需数据 (60s 缓存,避免频繁查询)。"""
    import datetime as dt
    db = get_db()
    ed = EquipmentDAO()
    calc = get_calculator()

    now_t = dt.datetime.now()
    start_t = now_t - dt.timedelta(hours=window_hours)

    # 设备状态汇总 (列: process / status / cnt)
    status_df = ed.status_summary()

    # 设备明细
    equip_list = ed.list_equipment()

    # WIP 分布 (按工序)
    wip_df = calc.wip_distribution()

    # WIP 按产品
    wip_product_df = calc.wip_by_product()

    # 近 N 小时 Move / 产出 (output_in_window 接受 start_time/end_time)
    output_stats = calc.output_in_window(start_t, now_t)

    # 近 N 小时 lot_history 明细 (按小时聚合用)
    hist_detail_df = db.query_df(f"""
        SELECT lot_id, process, start_time, end_time, output_qty, process_time_h
        FROM {TABLE_LOT_HISTORY}
        WHERE start_time >= ? AND start_time <= ?
        ORDER BY start_time ASC
    """, (start_t.strftime("%Y-%m-%d %H:%M:%S"), now_t.strftime("%Y-%m-%d %H:%M:%S")))

    # 工序级聚合
    hist_df = db.query_df(f"""
        SELECT process,
               COUNT(*) AS move_cnt,
               SUM(CASE WHEN end_time IS NOT NULL THEN output_qty ELSE 0 END) AS out_qty,
               AVG(process_time_h) AS avg_pt
        FROM {TABLE_LOT_HISTORY}
        WHERE start_time >= ?
        GROUP BY process
        ORDER BY move_cnt DESC
    """, (start_t.strftime("%Y-%m-%d %H:%M:%S"),))

    return {
        "status_df": status_df,
        "equip_list": equip_list,
        "wip_df": wip_df,
        "wip_product_df": wip_product_df,
        "output_stats": output_stats,
        "hist_detail_df": hist_detail_df,
        "hist_df": hist_df,
        "window_hours": window_hours,
    }


# =============================================================================
# 顶部控制栏
# =============================================================================

col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 2, 1])
with col_ctrl1:
    window_hours = st.slider("⏱ 监控时间窗口 (小时)", min_value=1, max_value=72, value=24, step=1)
with col_ctrl2:
    auto_refresh = st.checkbox("🔄 每 60s 自动刷新 (需手动开启)", value=False)
with col_ctrl3:
    if st.button("🔁 立即刷新", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

if auto_refresh:
    st_autorefresh_interval = 60
    try:
        from streamlit_autorefresh import st_autorefresh  # type: ignore
        st_autorefresh(interval=st_autorefresh_interval * 1000, key="realtime_refresh")
    except ImportError:
        st.caption("⚠️ 未安装 streamlit-autorefresh, 自动刷新不可用 (可 `pip install streamlit-autorefresh`)")

# 加载数据
data = load_realtime_data(window_hours=window_hours)
status_df = data["status_df"]
equip_list = data["equip_list"]
wip_df = data["wip_df"]
wip_product_df = data["wip_product_df"]
output_stats = data["output_stats"]
hist_detail_df = data["hist_detail_df"]
hist_df = data["hist_df"]

# =============================================================================
# 第 1 区: 全厂 KPI 概览
# =============================================================================

st.markdown("### 📊 全厂实时 KPI")

total_equip = len(equip_list) if equip_list is not None else 0
# status_summary 列为 ['process','status','cnt'], 按状态聚合需 groupby
if status_df is not None and not status_df.empty and "status" in status_df.columns and "cnt" in status_df.columns:
    status_total = status_df.groupby("status")["cnt"].sum().to_dict()
    run_cnt = int(status_total.get(EQUIP_STATUS_RUN, 0))
    down_cnt = int(status_total.get(EQUIP_STATUS_DOWN, 0))
    pm_cnt = int(status_total.get(EQUIP_STATUS_PM, 0))
else:
    run_cnt = down_cnt = pm_cnt = 0

total_wip = int(wip_df["wafers"].sum()) if wip_df is not None and not wip_df.empty and "wafers" in wip_df.columns else 0
total_move = int(hist_df["move_cnt"].sum()) if hist_df is not None and not hist_df.empty else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: st.metric("设备总数", f"{total_equip}")
with c2: st.metric("运行中", f"{run_cnt}")
with c3: st.metric("故障停机", f"{down_cnt}")
with c4: st.metric("PM 中", f"{pm_cnt}")
with c5: st.metric("WIP 总量", f"{total_wip:,} 片")
with c6: st.metric(f"{window_hours}h Move", f"{total_move:,}")

st.markdown("---")

# =============================================================================
# 第 2 区: 设备状态分布 + WIP 分布
# =============================================================================

col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("### ⚙️ 设备状态分布")
    if status_df is None or status_df.empty:
        st.info("暂无设备状态数据")
    else:
        # status_summary 按 process × status 分组, 这里按 status 聚合
        df_pie = status_df.groupby("status", as_index=False)["cnt"].sum()
        df_pie["状态"] = df_pie["status"].apply(lambda s: EQUIP_STATUS_NAME_CN.get(s, s))
        df_pie["颜色"] = df_pie["status"].apply(lambda s: EQUIP_STATUS_COLOR.get(s, "#888888"))

        fig = go.Figure(data=[go.Pie(
            labels=df_pie["状态"],
            values=df_pie["cnt"],
            hole=0.55,
            marker=dict(colors=df_pie["颜色"]),
            textfont=dict(color="#FFFFFF", size=13),
            textinfo="label+value+percent",
        )])
        fig.update_layout(title=f"全厂设备状态 (共 {total_equip} 台)", height=380)
        dark_chart_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("### 📦 WIP 在制品分布 (按工序)")
    if wip_df is None or wip_df.empty:
        st.info("暂无 WIP 数据")
    else:
        df_w = wip_df.copy()
        # wip_distribution 列: process / lots / wafers / process_cn
        if "process" in df_w.columns:
            df_w["工序"] = df_w.get("process_cn", df_w["process"].apply(process_cn_name))
            df_w["WIP(片)"] = df_w["wafers"].astype(int)

            fig = px.bar(
                df_w, x="工序", y="WIP(片)", color="工序",
                color_discrete_sequence=CHART_PALETTE,
                text=df_w["WIP(片)"].apply(lambda v: f"{int(v):,}"),
            )
            fig.update_layout(title=f"WIP 总量: {total_wip:,} 片", showlegend=False)
            fig.update_traces(textposition="outside")
            dark_chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# =============================================================================
# 第 3 区: 近 N 小时产出 / Move 趋势
# =============================================================================

st.markdown(f"### 📈 近 {window_hours}h 产出 / Move 趋势")

if hist_detail_df is None or hist_detail_df.empty:
    st.info(f"近 {window_hours}h 无产出数据")
else:
    # 按小时聚合
    df_o = hist_detail_df.copy()
    if "start_time" in df_o.columns:
        df_o["hour"] = pd.to_datetime(df_o["start_time"]).dt.floor("H")
        hourly = df_o.groupby("hour").agg(
            move_cnt=("lot_id", "count"),
            out_qty=("output_qty", "sum"),
        ).reset_index()
        hourly["out_qty"] = hourly["out_qty"].fillna(0).astype(int)
        hourly["hour_str"] = hourly["hour"].dt.strftime("%m-%d %H:%M")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=hourly["hour_str"], y=hourly["move_cnt"],
            name="Move 数", marker_color=CHART_PALETTE[0],
        ))
        fig.add_trace(go.Scatter(
            x=hourly["hour_str"], y=hourly["out_qty"],
            name="产出 (片)", mode="lines+markers",
            line=dict(color=CHART_PALETTE[1], width=2),
            yaxis="y2",
        ))
        fig.update_layout(
            title=f"近 {window_hours}h Move 与产出趋势",
            xaxis_title="时间",
            yaxis=dict(title="Move 数"),
            yaxis2=dict(title="产出 (片)", overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        dark_chart_layout(fig, height=400)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# =============================================================================
# 第 4 区: 工序级 Move / 产出 / 平均工时
# =============================================================================

st.markdown(f"### 🔧 近 {window_hours}h 工序级产出明细")

if hist_df is None or hist_df.empty:
    st.info(f"近 {window_hours}h 无工序历史数据")
else:
    df_h = hist_df.copy()
    if "process" in df_h.columns:
        df_h["工序"] = df_h["process"].apply(process_cn_name)
        df_h["平均工时(h)"] = df_h["avg_pt"].apply(lambda v: safe_round(v, 2))
        df_h = df_h.rename(columns={"move_cnt": "Move数", "out_qty": "产出(片)"})
        df_h = df_h[["工序", "Move数", "产出(片)", "平均工时(h)"]]
        df_h = df_h.sort_values("Move数", ascending=False)
        st.dataframe(df_h, use_container_width=True, hide_index=True)

st.markdown("---")

# =============================================================================
# 第 5 区: 设备明细表 (带筛选)
# =============================================================================

st.markdown("### 🏭 设备明细")

col_f1, col_f2 = st.columns(2)
with col_f1:
    sel_process = st.multiselect(
        "筛选工序",
        options=ALL_PROCESSES,
        default=[],
        format_func=lambda p: f"{p} ({process_cn_name(p)})",
    )
with col_f2:
    sel_status = st.multiselect(
        "筛选状态",
        options=[EQUIP_STATUS_RUN, EQUIP_STATUS_IDLE, EQUIP_STATUS_DOWN, EQUIP_STATUS_PM, EQUIP_STATUS_SETUP],
        default=[],
        format_func=lambda s: EQUIP_STATUS_NAME_CN.get(s, s),
    )

if equip_list is None or equip_list.empty:
    st.info("暂无设备数据")
else:
    df_e = equip_list.copy()
    # 应用筛选
    if sel_process:
        df_e = df_e[df_e["process"].isin(sel_process)]
    if sel_status:
        df_e = df_e[df_e["status"].isin(sel_status)]

    # 字段美化
    if "process" in df_e.columns:
        df_e["工序"] = df_e["process"].apply(process_cn_name)
    if "status" in df_e.columns:
        df_e["状态"] = df_e["status"].apply(lambda s: EQUIP_STATUS_NAME_CN.get(s, s))

    keep_cols = [c for c in ["equip_id", "equip_type", "工序", "状态", "model", "location", "total_run_hours"] if c in df_e.columns]
    st.dataframe(df_e[keep_cols], use_container_width=True, hide_index=True)
    st.caption(f"共 {len(df_e)} 台设备 (筛选后)")

st.caption(f"FabCapacityAgent · 实时监控 · 数据更新于 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
