"""
FabCapacityAgent - Agent 工作台页面

职责:
  1) 一键运行全链路 Pipeline (Perception → Analysis → Decision → Execution)
  2) 单 Agent 调试 (仅运行某一个 Agent)
  3) 实时展示 Pipeline 进度 / 状态 / 耗时
  4) 查看 final_report (Markdown 渲染)
  5) 历史运行记录 + 单次 Run 详情查看
"""

import os
import sys
import json
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st
import pandas as pd
import datetime as dt

from utils.ui_components import init_page, dark_chart_layout, status_badge
from utils.helpers import get_logger, safe_round, to_pct, process_cn_name
from utils.constants import (
    AGENT_PERCEPTION, AGENT_ANALYSIS, AGENT_DECISION, AGENT_EXECUTION,
    AGENT_NAME_CN,
    STATUS_SUCCESS, STATUS_FAILED, STATUS_TIMEOUT, STATUS_RUNNING,
    CHART_PALETTE,
    UI_PRIMARY, UI_TEXT,
)
from models.capacity import AgentLogDAO
from agents.orchestrator import get_orchestrator, Orchestrator
from agents.base_agent import BaseAgent

logger = get_logger("PageAgent", level="INFO")

init_page("Agent 工作台", icon="🤖", subtitle="PTA Pipeline / Perceive-Think-Act")


# =============================================================================
# Session State: 保存最近一次 Pipeline 结果
# =============================================================================

def get_last_result():
    return st.session_state.get("last_pipeline_result", None)


def set_last_result(result):
    st.session_state["last_pipeline_result"] = result


# =============================================================================
# 顶部控制栏
# =============================================================================

st.markdown("### 🚀 Agent 全链路编排")

col_a1, col_a2, col_a3, col_a4 = st.columns([2, 2, 2, 2])
with col_a1:
    user_query = st.text_input(
        "📝 用户查询 (可选)",
        value="分析当前产能瓶颈并给出优化建议",
        help="会被注入到 Agent 上下文,影响分析方向",
    )
with col_a2:
    window_hours = st.slider("感知窗口 (h)", min_value=6, max_value=168, value=24, step=6)
with col_a3:
    history_days = st.slider("历史窗口 (天)", min_value=7, max_value=90, value=30, step=1)
with col_a4:
    use_llm = st.checkbox("启用 LLM 增强", value=False, help="使用 DeepSeek/Qwen 增强 Agent 文本生成")

col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
with col_btn1:
    btn_run_full = st.button("🚀 运行全链路 Pipeline", use_container_width=True, type="primary")
with col_btn2:
    btn_clear = st.button("🧹 清除结果", use_container_width=True)
with col_btn3:
    btn_refresh_logs = st.button("🔁 刷新日志", use_container_width=True)

# =============================================================================
# 单 Agent 调试区
# =============================================================================

with st.expander("🔬 单 Agent 调试 (可选)", expanded=False):
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        single_agent = st.radio(
            "选择 Agent",
            options=[AGENT_PERCEPTION, AGENT_ANALYSIS, AGENT_DECISION, AGENT_EXECUTION],
            format_func=lambda a: f"{AGENT_NAME_CN.get(a, a)} ({a})",
            horizontal=True,
        )
    with col_s2:
        btn_run_single = st.button("▶ 运行单 Agent", use_container_width=True)

# =============================================================================
# 运行逻辑
# =============================================================================

if btn_run_full:
    with st.spinner("🚀 正在运行全链路 Pipeline,请稍候 (约 10~30s)..."):
        try:
            orch = get_orchestrator()
            # LLM 开关
            if not use_llm:
                for a in orch.agents.values():
                    a.llm = None
            else:
                from utils.llm_client import get_llm
                llm = get_llm()
                if llm.is_configured():
                    for a in orch.agents.values():
                        a.llm = llm
                    st.info(f"✓ LLM 已启用 ({llm.provider})")
                else:
                    st.warning("⚠️ LLM 未配置 API Key, 回退到本地模式")
                    for a in orch.agents.values():
                        a.llm = None

            result = orch.run_full_pipeline(
                user_query=user_query,
                trigger="ui_manual",
                window_hours=window_hours,
                history_days=history_days,
            )
            set_last_result(result)
            st.success(f"✓ Pipeline 完成 | 状态: {result.status} | 耗时: {safe_round(result.total_duration_ms/1000, 2)}s")
        except Exception as exc:
            st.error(f"❌ Pipeline 运行失败: {exc}")
            logger.error(f"Pipeline 失败: {exc}", exc_info=True)

if btn_clear:
    set_last_result(None)
    st.rerun()

if btn_run_single:
    with st.spinner(f"▶ 正在运行 {AGENT_NAME_CN.get(single_agent, single_agent)}..."):
        try:
            orch = get_orchestrator()
            if not use_llm:
                for a in orch.agents.values():
                    a.llm = None

            single_result = orch.run_single(
                agent_type=single_agent,
                user_query=user_query,
                window_hours=window_hours,
                history_days=history_days,
            )
            if single_result:
                st.success(f"✓ {AGENT_NAME_CN.get(single_agent)} 完成 | 状态: {single_result.get('status', 'N/A')}")
                # 包装成简化 Pipeline 结果存入 session
                class _SimpleResult:
                    pass
                sr = _SimpleResult()
                sr.status = single_result.get("status")
                sr.total_duration_ms = sum(s.get("duration_ms", 0) for s in single_result.get("steps", []))
                sr.pipeline_steps = []
                sr.final_report = ""
                sr.final_output = single_result.get("output")
                sr.llm_enhanced = single_result.get("llm_enhanced", False)
                sr.user_query = user_query
                sr.run_id = single_result.get("run_id", "single")
                sr.error_message = None
                sr.summary = lambda: {
                    "run_id": sr.run_id,
                    "status": sr.status,
                    "total_duration_ms": sr.total_duration_ms,
                    "started_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "finished_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_query": sr.user_query,
                    "llm_enhanced": sr.llm_enhanced,
                    "steps": [{
                        "agent_type": single_agent,
                        "agent_name_cn": AGENT_NAME_CN.get(single_agent, single_agent),
                        "status": single_result.get("status"),
                        "duration_ms": sr.total_duration_ms,
                        "error": single_result.get("error"),
                    }],
                }
                set_last_result(sr)
            else:
                st.error("单 Agent 运行返回 None")
        except Exception as exc:
            st.error(f"❌ 单 Agent 运行失败: {exc}")

# =============================================================================
# 结果展示
# =============================================================================

last_result = get_last_result()

if last_result is None:
    st.info("👆 点击「运行全链路 Pipeline」开始,或展开「单 Agent 调试」测试单个 Agent")
else:
    st.markdown("---")
    st.markdown("### 📊 Pipeline 执行结果")

    # 概览 KPI
    summary = last_result.summary() if hasattr(last_result, "summary") else {}
    s_status = summary.get("status", "N/A")
    s_duration = summary.get("total_duration_ms", 0)
    s_llm = summary.get("llm_enhanced", False)
    s_run_id = summary.get("run_id", "N/A")
    steps = summary.get("steps", [])

    # 状态徽章
    status_emoji = {
        STATUS_SUCCESS: "✅",
        STATUS_FAILED: "❌",
        STATUS_TIMEOUT: "⏱",
        STATUS_RUNNING: "🔄",
        "partial": "⚠️",
    }.get(s_status, "❓")
    st.markdown(f"**{status_emoji} 状态**: `{s_status}`  |  **Run ID**: `{s_run_id}`  |  **耗时**: `{safe_round(s_duration/1000, 2)}s`  |  **LLM**: {'✓' if s_llm else '✗'}")

    # 步骤进度条 (Agent 链路时间轴)
    if steps:
        st.markdown("#### 🔗 Agent 执行链路")
        step_cols = st.columns(len(steps))
        for i, (col, step) in enumerate(zip(step_cols, steps)):
            with col:
                agent_type = step.get("agent_type", "")
                agent_cn = step.get("agent_name_cn", "")
                step_status = step.get("status", "")
                step_dur = step.get("duration_ms", 0)
                step_err = step.get("error")

                emoji = {
                    STATUS_SUCCESS: "✅", STATUS_FAILED: "❌",
                    STATUS_TIMEOUT: "⏱", STATUS_RUNNING: "🔄",
                }.get(step_status, "❓")
                color = {
                    STATUS_SUCCESS: "#00A66E", STATUS_FAILED: "#E53935",
                    STATUS_TIMEOUT: "#E8A300", STATUS_RUNNING: "#0099CC",
                }.get(step_status, "#888888")

                st.markdown(
                    f"""
                    <div style="background:#FFFFFF;border:1px solid {color};
                                border-radius:10px;padding:12px;text-align:center;
                                box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                        <div style="font-size:24px;">{emoji}</div>
                        <div style="color:{UI_PRIMARY};font-weight:600;font-size:13px;margin-top:4px;">{agent_cn}</div>
                        <div style="color:#8899AA;font-size:10px;">{agent_type}</div>
                        <div style="color:{UI_TEXT};font-size:11px;margin-top:6px;">{safe_round(step_dur/1000, 2)}s</div>
                        {f'<div style="color:#E53935;font-size:10px;margin-top:4px;">{step_err[:30]}</div>' if step_err else ''}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # 最终报告
    final_report = getattr(last_result, "final_report", "") or ""
    if final_report:
        st.markdown("---")
        st.markdown("### 📝 最终产能分析报告")
        tab_r1, tab_r2 = st.tabs(["📄 渲染报告", "📋 原始 Markdown"])

        with tab_r1:
            st.markdown(final_report)

        with tab_r2:
            st.code(final_report, language="markdown")

        # 下载按钮
        st.download_button(
            label="📥 下载报告 (Markdown)",
            data=final_report.encode("utf-8"),
            file_name=f"fab_capacity_report_{s_run_id}.md",
            mime="text/markdown",
        )

    # 错误信息
    err = getattr(last_result, "error_message", None)
    if err:
        st.error(f"❌ 错误: {err}")

# =============================================================================
# 历史 Run 记录
# =============================================================================

st.markdown("---")
st.markdown("### 📚 历史 Pipeline 运行记录")

try:
    log_dao = AgentLogDAO()
    df_runs = log_dao.recent_runs(limit=20)
    if df_runs is None or df_runs.empty:
        st.info("暂无历史运行记录")
    else:
        df_runs = df_runs.copy()
        # 状态文本化
        df_runs["状态"] = df_runs.apply(
            lambda r: f"✅ {int(r.get('succ_steps', 0))} 成功"
                      + (f" / ❌ {int(r.get('fail_steps', 0))} 失败" if r.get("fail_steps", 0) else ""),
            axis=1,
        )
        df_runs["总耗时"] = df_runs["total_ms"].apply(
            lambda v: f"{safe_round(v/1000, 2)}s" if pd.notna(v) and v else "-"
        )
        df_runs["created_at"] = df_runs["created_at"].astype(str).str[:19]

        show_cols = [c for c in ["created_at", "run_id", "状态", "总耗时"] if c in df_runs.columns]
        df_runs = df_runs[show_cols]
        df_runs.columns = ["时间", "Run ID", "执行状态", "总耗时"][: len(show_cols)]
        st.dataframe(df_runs, use_container_width=True, hide_index=True)

        # 选择查看某次 Run 详情
        st.markdown("#### 🔍 查看某次 Run 的 Agent 步骤详情")
        if "Run ID" in df_runs.columns:
            sel_run = st.selectbox("选择 Run ID", options=["(不选)"] + df_runs["Run ID"].tolist())
            if sel_run != "(不选)":
                detail_df = log_dao.list_by_run(sel_run)
                if detail_df is not None and not detail_df.empty:
                    detail_df = detail_df.copy()
                    if "agent_type" in detail_df.columns:
                        detail_df["Agent"] = detail_df["agent_type"].apply(lambda a: AGENT_NAME_CN.get(a, a))
                    if "status" in detail_df.columns:
                        detail_df["状态"] = detail_df["status"].apply(lambda s: {
                            STATUS_SUCCESS: "✅", STATUS_FAILED: "❌",
                            STATUS_TIMEOUT: "⏱", STATUS_RUNNING: "🔄",
                        }.get(s, s))
                    if "duration_ms" in detail_df.columns:
                        detail_df["耗时"] = detail_df["duration_ms"].apply(lambda v: f"{safe_round(v/1000, 2)}s" if v else "-")
                    if "created_at" in detail_df.columns:
                        detail_df["created_at"] = detail_df["created_at"].astype(str).str[:19]

                    keep = [c for c in ["created_at", "Agent", "状态", "耗时", "stage", "error_message"] if c in detail_df.columns]
                    st.dataframe(detail_df[keep], use_container_width=True, hide_index=True)
                else:
                    st.warning(f"Run ID {sel_run} 无日志记录")
except Exception as exc:
    st.warning(f"历史记录加载失败: {exc}")

st.caption(f"FabCapacityAgent · Agent 工作台 · {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
