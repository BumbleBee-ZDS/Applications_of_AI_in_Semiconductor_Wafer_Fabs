"""
app.py  — FAB 多 Agent 评估框架 MVP 的 Streamlit UI 入口
===========================================================
本文件只负责 UI 布局与交互；核心 Agent 逻辑均已解耦到：
    core/  ── Evaluator / Memory / ToolSet / Planner / Reflector / Orchestrator
    data/  ── LOT_DB / RECIPE_DB / 生成数据加载

运行方式：
    python -m streamlit run app.py
"""

import time

import streamlit as st

from core import Evaluator, Memory, ToolSet, Planner, Reflector, Orchestrator
from data.mock_data import LOT_DB, RECIPE_DB, GENERATED_QUESTIONS, DATA_SOURCE


# =====================================================================
# 页面配置
# =====================================================================
st.set_page_config(page_title="FAB 多Agent评估框架", page_icon="🔬", layout="wide")
st.title("🔬 半导体晶圆厂 多 Agent 评估框架 MVP")
st.caption("晶圆缺陷根因分析 · 过程质量 / 资源成本 / 系统韧性 实时评估")


# =====================================================================
# Session State 初始化
# =====================================================================
if "logs" not in st.session_state:
    st.session_state.logs = []
if "report" not in st.session_state:
    st.session_state.report = ""
if "evaluator" not in st.session_state:
    st.session_state.evaluator = None


# =====================================================================
# 两栏布局
# =====================================================================
col_left, col_right = st.columns([3, 2], gap="large")

# -------------------- 左侧：输入与执行流 --------------------
with col_left:
    st.subheader("🛠 输入与执行流")
    st.caption(
        f"数据来源：{DATA_SOURCE} · 可用批次 {len(LOT_DB)} 个 · 配方 {len(RECIPE_DB)} 个"
    )

    # 示例问题下拉（来自 DeepSeek 生成；若无则仅手动输入）
    sample_options = ["（手动输入）"] + GENERATED_QUESTIONS
    selected_q = st.selectbox(
        "示例问题（DeepSeek 生成）",
        sample_options,
        index=0,
        help="选择一个示例问题快速测试，也可在下方手动编辑",
    )
    default_q = (
        selected_q
        if selected_q != "（手动输入）"
        else "批次 W12345 的关键尺寸（CD）超标，分析原因。"
    )

    question = st.text_input(
        "工艺工程师问题",
        value=default_q,
        help="输入批次号（如 W12345）以触发根因分析流程",
    )
    run_btn = st.button("🚀 开始分析", type="primary", use_container_width=True)

    st.markdown("#### 执行日志")
    log_placeholder = st.empty()

    # 展示历史日志（按钮未点击）
    if st.session_state.logs and not run_btn:
        with log_placeholder.container():
            st.code("\n".join(st.session_state.logs), language="text")

    # -------------------- 点击按钮：启动 Orchestrator --------------------
    if run_btn:
        st.session_state.logs = []
        st.session_state.report = ""
        st.session_state.evaluator = None
        logs: list[str] = []

        def log_fn(msg: str) -> None:
            """日志回调：实时刷新日志区"""
            logs.append(msg)
            with log_placeholder.container():
                st.code("\n".join(logs), language="text")
            time.sleep(0.15)

        # 实例化各模块
        evaluator = Evaluator()
        memory = Memory()
        toolset = ToolSet(evaluator, log_fn)
        planner = Planner(evaluator, log_fn)
        reflector = Reflector(evaluator, log_fn)
        orchestrator = Orchestrator(
            memory, toolset, planner, reflector, evaluator, log_fn
        )

        report = orchestrator.run(question)

        # 持久化结果
        st.session_state.logs = logs
        st.session_state.report = report
        st.session_state.evaluator = evaluator

    # -------------------- 最终报告 --------------------
    if st.session_state.report:
        st.markdown("---")
        st.subheader("📄 最终报告")
        st.markdown(st.session_state.report)


# -------------------- 右侧：评估面板 --------------------
with col_right:
    st.subheader("📊 评估面板")

    ev = st.session_state.evaluator
    if ev is None:
        st.info("👈 点击「开始分析」启动 Agent 流程，评估指标将实时显示于此。")
    else:
        # —— 资源成本 & 过程质量 ——
        st.markdown("**资源成本 & 过程质量**")
        m1, m2 = st.columns(2)
        with m1:
            st.metric("执行步数", f"{ev.step_count} / {ev.max_steps}")
            st.metric("工具调用次数", ev.tool_call_count)
        with m2:
            st.metric("模拟 Token 消耗", ev.token_cost_mock)
            st.metric("重试次数", ev.retry_count)

        st.markdown("---")

        # —— 系统韧性 ——
        st.markdown("**系统韧性**")
        if ev.dead_loop_flag:
            st.error("⛔ 检测到死循环（连续 2 步相同工具调用）")
        else:
            st.success("✅ 未检测到死循环")
        st.markdown(f"韧性评分：**{ev.resilience_score()}**")

        st.markdown("---")

        # —— 反思有效性 ——
        st.markdown("**反思有效性**")
        if ev.reflection_valid:
            st.warning("⚡ Reflector 发现数据矛盾")
        else:
            st.info("未发现数据矛盾")

        st.markdown("---")

        # —— 业务价值 ——
        st.markdown("**业务价值**")
        if ev.business_value():
            st.success("✅ 最终结论包含可执行建议")
        else:
            st.error("❌ 最终结论缺少建议")

        st.markdown("---")

        # —— 指标明细 JSON ——
        with st.expander("🔍 评估指标明细（JSON）"):
            st.json(ev.to_dict())


# 页脚
st.markdown("---")
st.caption(
    "FAB 多 Agent 评估框架 MVP · "
    "白盒模块：Memory / ToolSet / Planner / Reflector / Orchestrator / Evaluator · "
    "设备接口超时率 30% · 步数上限 6"
)
