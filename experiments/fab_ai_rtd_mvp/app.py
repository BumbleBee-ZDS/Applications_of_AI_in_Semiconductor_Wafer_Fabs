"""🏭 晶圆厂 RTD 实时派工 LLM Agent —— MVP 主页。

包含：标题、技术栈表格、快速开始说明、侧边栏 API 状态与清空会话按钮、
顶部 4 个 metric 卡片（总 WIP / 宕机数 / 告警数 / 未决审批）。
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from data import factory_simulator
from utils import helpers, knowledge_base
from utils.llm_client import is_dashscope_ready, is_deepseek_ready

st.set_page_config(page_title="晶圆厂 RTD 智能派工 Agent (MVP)", page_icon="🏭", layout="wide")

helpers.init_session_state()

# ---------- 侧边栏 ----------
with st.sidebar:
    st.title("🏭 FAB RTD Agent")
    st.caption("半导体 12 英寸晶圆厂 RTD 实时派工 LLM Agent MVP")
    st.divider()
    st.markdown("**API 配置状态**")
    st.markdown(f"- DeepSeek：{'✅ 已配置' if is_deepseek_ready() else '❌ 未配置'}")
    st.markdown(f"- 千问 Embedding：{'✅ 已配置' if is_dashscope_ready() else '❌ 未配置'}")
    if not is_deepseek_ready() or not is_dashscope_ready():
        st.info("未配置 Key 时系统自动使用**规则降级**策略，演示流程仍可完整跑通。")
    st.divider()
    if st.button("🧹 清空会话状态", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.caption("提示：复制 `.env.example` 为 `.env` 并填入真实 Key 后重启生效。")

# ---------- 首次启动：自动向量化知识库 ----------
if "kb_ready_flag" not in st.session_state:
    with st.spinner("正在向量化工艺知识库（千问 Embedding，约 1~2 次 API 调用）..."):
        kb_info = knowledge_base.ensure_indexed()
    st.session_state["kb_ready_flag"] = kb_info
kb_info = st.session_state["kb_ready_flag"]
if kb_info.get("error"):
    st.warning(f"⚠️ 千问 Embedding 暂不可用，已回退本地伪向量：{kb_info['error']}")

# ---------- 工厂状态（会话级，页面间共享） ----------
if st.session_state["factory_state"] is None:
    st.session_state["factory_state"] = factory_simulator.generate_factory_state()
state = st.session_state["factory_state"]

# ---------- 顶部 4 个指标卡片 ----------
store = st.session_state["approval_store"]
pending_count = len(store.pending_tickets())

m1, m2, m3, m4 = st.columns(4)
m1.metric("📦 总 WIP（片）", state["wip_total"])
m2.metric("🛠 宕机设备数", state["tool_down_count"])
m3.metric("🚨 当前告警数", len(state["alarms"]))
m4.metric("⏳ 未决审批单", pending_count)

# ---------- 项目介绍 ----------
st.title("🏭 晶圆厂 RTD 实时派工 LLM Agent —— MVP")
st.markdown(
    "模拟 **12 英寸晶圆厂 RTD（Real-Time Dispatching）实时派工系统**被 LLM Agent 增强后的完整工作流："
    "**感知 → RAG 诊断 → 调度决策 → RL 仿真 → 人工审批 → 审计追溯**，全程调用真实大模型 API"
    "（DeepSeek 推理 + 阿里千问向量化）。"
)

st.subheader("🧩 Agent 全链路")
st.markdown("""
| 环节 | Agent | 说明 | 模型 |
|---|---|---|---|
| ① 感知 | perception_agent | 扫描设备参数与告警，输出标准化异常事件 | 规则（阈值） |
| ② 诊断 | diagnosis_agent | 千问 RAG 检索知识库 + DeepSeek 根因分析 | deepseek-v4-pro + qwen3.7-text-embedding |
| ③ 调度 | scheduling_agent | 生成派工策略（Q-Time / Recipe / PM / HOLD 约束） | deepseek-v4-pro |
| ④ 仿真 | rl_simulator | 启发式奖励函数评估 + 策略扰动探索 | 规则 |
| ⑤ 执行 | execution_agent | L1~L4 风险分级 + 人工审批 | 规则 |
| ⑥ 审计 | audit_agent | 全链路日志追溯与导出 | 内存日志 |
""")

st.subheader("⚙️ 技术栈")
st.table(pd.DataFrame({
    "组件": ["Streamlit", "DeepSeek（聊天/推理）", "阿里千问（向量化）", "pandas / numpy / scikit-learn", "plotly", "python-dotenv"],
    "用途": ["多页面 UI（pages/ 机制）", "根因分析 / 调度决策", "知识库 RAG 检索", "数据处理 / 启发式评估", "负载与趋势可视化", "环境变量管理"],
}))

st.subheader("🚀 快速开始")
st.markdown("""
1. 复制 `.env.example` 为 `.env`，填入 `DEEPSEEK_API_KEY` 与 `DASHSCOPE_API_KEY`；
2. `pip install -r requirements.txt`；
3. `streamlit run app.py`；
4. 前往 **1 实时监控** 注入异常 → **2 Agent 分析** 一键运行全链路 → **3 人工审批** 审批执行 → **4 审计日志** 追溯全链路。
""")

st.caption("说明：未配置 API Key 时，诊断/调度自动降级为规则启发式策略，RL 与审批流程不受影响，可完整演示。")
