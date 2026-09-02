"""📡 实时监控：设备状态 / 批次 / 告警 / PM 计划 / 异常注入。"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from data import factory_simulator
from utils import helpers

st.set_page_config(page_title="1 实时监控", page_icon="📡", layout="wide")
helpers.init_session_state()

st.title("📡 实时监控")
st.caption("模拟晶圆厂实时数据帧。下拉选择异常场景后点击「刷新 / 注入」，感知 Agent 将据此稳定检出事件。")

# 首次进入自动生成数据帧
if st.session_state["factory_state"] is None:
    st.session_state["factory_state"] = factory_simulator.generate_factory_state()
state = st.session_state["factory_state"]

# ---------- 工具栏 ----------
top = st.columns([2.4, 1.1, 1.6])
with top[0]:
    anomaly_choice = st.selectbox(
        "注入异常场景",
        list(factory_simulator.ANOMALY_LABELS.keys()),
        format_func=lambda k: factory_simulator.ANOMALY_LABELS[k],
    )
with top[1]:
    if st.button("🔄 刷新 / 注入", use_container_width=True, type="primary"):
        anomaly = None if anomaly_choice == "none" else anomaly_choice
        st.session_state["factory_state"] = factory_simulator.generate_factory_state(force_anomaly=anomaly)
        st.rerun()
with top[2]:
    st.caption(f"🕐 数据帧时间：{state['timestamp']}")

# ---------- 指标 ----------
m = st.columns(4)
m[0].metric("总 WIP（片）", state["wip_total"])
m[1].metric("宕机设备", state["tool_down_count"])
m[2].metric("告警数", len(state["alarms"]))
m[3].metric("URGENT 批次", sum(1 for lot in state["lots"] if lot["priority"] == "URGENT"))

# ---------- 设备状态表（RUNNING 绿 / IDLE 黄 / DOWN 红 / PM 蓝） ----------
st.subheader("🛠 设备状态")
STATUS_COLOR = {"RUNNING": "#d4f7d4", "IDLE": "#fff3cd", "DOWN": "#f8d7da", "PM": "#d1e7ff"}

df_eq = pd.DataFrame([
    {
        "设备": eq["equipment_id"],
        "类型": eq["type"],
        "区域": eq["area"],
        "状态": eq["status"],
        "当前配方": eq.get("current_recipe") or "-",
        "支持配方": " / ".join(eq["supported_recipes"]),
        "下一批次": eq.get("next_lot") or "-",
        "参数快照": str(eq.get("params", {})),
    }
    for eq in state["equipment"]
])


def _color_eq(row: pd.Series) -> list[str]:
    color = STATUS_COLOR.get(row["状态"], "")
    return [f"background-color: {color}"] * len(row)


st.dataframe(df_eq.style.apply(_color_eq, axis=1), use_container_width=True, hide_index=True)

# ---------- 批次表（URGENT/HIGH/NORMAL/LOW 着色） ----------
st.subheader("📦 批次 WIP")
PRIORITY_COLOR = {"URGENT": "#f8d7da", "HIGH": "#fff3cd", "NORMAL": "#d1e7ff", "LOW": "#e2e3e5"}

df_lots = pd.DataFrame([
    {
        "批次": lot["lot_id"],
        "优先级": lot["priority"],
        "配方": lot["recipe"],
        "区域": lot["area"],
        "当前工序": lot["current_step"],
        "Q-Time 剩余(min)": lot["q_time_remaining_min"],
        "Q-Time 状态": (
            "⚠️ 已超时" if lot["q_time_remaining_min"] < 0
            else ("🕐 紧急(<30min)" if lot["q_time_remaining_min"] < 30 else "正常")
        ),
        "片数": lot["wafer_count"],
        "HOLD": "✅" if lot.get("hold") else "-",
    }
    for lot in state["lots"]
])


def _color_lot(row: pd.Series) -> list[str]:
    color = PRIORITY_COLOR.get(row["优先级"], "")
    return [f"background-color: {color}"] * len(row)


st.dataframe(df_lots.style.apply(_color_lot, axis=1), use_container_width=True, hide_index=True)

# ---------- 告警区（HIGH=error / MEDIUM=warning） ----------
st.subheader("🚨 告警区")
if not state["alarms"]:
    st.success("✅ 当前无告警")
for alarm in state["alarms"]:
    msg = f"**[{alarm['equipment_id']}] {alarm['message']}**（{alarm['code']} · {alarm['timestamp']}）"
    if alarm["severity"] == "HIGH":
        st.error(msg)
    elif alarm["severity"] == "MEDIUM":
        st.warning(msg)
    else:
        st.info(msg)

# ---------- PM 计划 ----------
st.subheader("🗓 PM 计划")
df_pm = pd.DataFrame([
    {
        "设备": pm["equipment_id"],
        "PM 类型": pm["pm_type"],
        "剩余时间(min)": pm["due_in_min"],
        "时长(min)": pm["duration_min"],
        "状态": pm["status"],
    }
    for pm in state["pm_schedule"]
])
st.dataframe(df_pm, use_container_width=True, hide_index=True)

# ---------- 区域瓶颈负载 ----------
st.subheader("📊 区域瓶颈负载")
load = state["bottleneck_load"]
fig = px.bar(
    x=list(load.keys()),
    y=list(load.values()),
    color=list(load.values()),
    color_continuous_scale="RdYlGn_r",
    text=[f"{v:.0%}" for v in load.values()],
    labels={"x": "区域", "y": "负载率"},
)
fig.update_layout(yaxis_range=[0, 1.05], showlegend=False, height=320)
st.plotly_chart(fig, use_container_width=True)
