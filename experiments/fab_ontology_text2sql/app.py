# -*- coding: utf-8 -*-
"""
app.py —— Streamlit 交互界面（Palantir Ontology 三层架构的「展示壳」）
=====================================================================

布局说明
--------
- 左侧边栏：LLM 配置（OpenAI 兼容）、数据库状态（动态层）、本体字典预览（语义层）
- 主界面   ：聊天窗口 + 快速示例问题
- 每条回答下方：「思考链 Trace」面板，展示
    ① 语义层匹配的本体概念 / 注入片段  ② 动力层意图 JSON
    ③ 最终执行的模板 SQL / 参数         ④ 动态层执行结果（表格 + 趋势折线图）

运行：streamlit run app.py
"""

import datetime as dt
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().with_name(".env"))  # 读取 .env（DEEPSEEK_API_KEY 等）

from mock_db import init_db, get_db_summary
from ontology import FabQueryAgent, LLMConfig, OntologyDictionary, TraceData

st.set_page_config(page_title="🏭 Fab Ontology Text2SQL", page_icon="🏭", layout="wide")

# ---------------------------------------------------------------------------
# 会话/资源初始化
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "db_summary" not in st.session_state:
    st.session_state.db_summary = init_db()          # 动态层：幂等初始化


@st.cache_resource
def get_ontology() -> OntologyDictionary:
    return OntologyDictionary()


ontology = get_ontology()

# 快速示例问题（批次号年份跟随当前年份，与 mock 数据一致）
_YEAR = dt.date.today().year
SAMPLE_QUESTIONS = [
    "帮我查一下 3号机 上周的良率趋势",
    "膜厚异常的晶圆有哪些？",
    "各设备的平均良率排名",
    f"LOT-{_YEAR}-001 的工艺日志",
    "缺陷偏高的晶圆有哪些",
    "当前所有设备的状态",
]


# ---------------------------------------------------------------------------
# 侧边栏
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🏭 Fab Ontology Text2SQL")
    st.caption("基于 Palantir Ontology 三层架构的 FAB 数据问答 MVP")

    st.divider()
    st.subheader("🤖 LLM（动力层引擎，OpenAI 兼容）")
    llm_enabled = st.checkbox(
        "启用 LLM 提取意图", value=os.getenv("LLM_ENABLED", "1") == "1",
        help="关闭后使用本地规则引擎（完全离线可用）",
    )
    llm_model = st.text_input("模型", value=os.getenv("LLM_MODEL", "deepseek-chat"))
    llm_base_url = st.text_input("Base URL", value=os.getenv("DEEPSEEK_BASE_URL", ""))
    llm_api_key = st.text_input("API Key", type="password",
                                value=os.getenv("DEEPSEEK_API_KEY", ""))
    st.caption("配置项已从 .env 读取，可在此覆盖。调用失败会自动回退规则引擎。")

    st.divider()
    st.subheader("🗄️ 数据库（动态层）")
    if st.button("🔄 重新生成 Mock 数据", use_container_width=True):
        st.session_state.db_summary = init_db(force=True)
        st.rerun()
    if st.session_state.db_summary:
        st.dataframe(
            pd.DataFrame([{"表": k, "行数": v}
                          for k, v in st.session_state.db_summary.items()]),
            use_container_width=True, hide_index=True,
        )
    else:
        st.warning("数据库未初始化")

    st.divider()
    st.subheader("📖 本体字典（语义层）")
    st.caption(f"共 {ontology.total_concepts} 个业务概念")
    with st.expander("点击展开预览", expanded=False):
        st.json(ontology.raw)
    st.caption("LLM 只收到与问题相关的片段，而非整本字典。")


# ---------------------------------------------------------------------------
# 渲染辅助
# ---------------------------------------------------------------------------
def build_summary(trace: TraceData) -> str:
    """生成回答摘要文本。"""
    if trace.error:
        return f"❌ 查询执行失败：{trace.error}"
    plan = trace.plan

    def label(kind: str, id_: str) -> str:
        for c in ontology.raw.get(kind, []):
            if c["id"] == id_:
                return c["label"]
        return id_

    bits = []
    if plan.get("metric"):
        bits.append(f"指标「{label('metrics', plan['metric'])}」")
    if plan.get("condition"):
        bits.append(f"条件「{label('conditions', plan['condition'])}」")
    if plan.get("equipment"):
        bits.append(f"设备 {plan['equipment']}")
    if plan.get("lot"):
        bits.append(f"批次 {plan['lot']}")
    if plan.get("time_range"):
        bits.append(f"时间 {plan['time_range']['start']} ~ {plan['time_range']['end']}")
    if plan.get("trend"):
        bits.append("按日趋势")
    head = "✅ 已执行：" + "、".join(bits) if bits else "✅ 已执行查询"
    n = 0 if trace.result is None else len(trace.result)
    return f"{head}，共返回 {n} 行。"


def render_result(trace: TraceData) -> None:
    """④ 动态层结果：趋势折线图 + 数据表。"""
    df = trace.result
    if df is None or df.empty:
        st.info("查询成功，但该条件下暂无数据（可尝试扩大时间范围）。")
        return
    if trace.plan.get("trend") and "日期" in df.columns:
        plot_df = df.set_index("日期")
        num_cols = [c for c in plot_df.columns if c not in ("晶圆数", "量测点数")]
        if num_cols:
            st.line_chart(plot_df[num_cols[0]])
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_trace(trace: TraceData) -> None:
    """「思考链 Trace」面板：语义层 -> 动力层 -> 动态层 全链路透明展示。"""
    with st.expander("🔍 思考链 Trace（语义层 → 动力层 → 动态层）",
                     expanded=trace.error is not None):
        c1, c2, c3 = st.columns(3)
        c1.metric("提取模式", trace.extraction_mode)
        c2.metric("耗时", f"{trace.elapsed_ms} ms")
        c3.metric("结果行数", "—" if trace.error else len(trace.result))

        st.markdown("**① 语义层 · 本体概念匹配**")
        if trace.matched_concepts:
            for m in trace.matched_concepts:
                st.markdown(f"- `{m['type']}` **{m['label']}** —— {m['explain']}")
        else:
            st.markdown("_未命中任何本体概念_")
        st.caption(f"注入 LLM 的本体片段：{len(trace.injected_fragments)} 条"
                   f"（全部概念共 {ontology.total_concepts} 条）")

        st.markdown("**② 动力层 · 意图提取计划（结构化 JSON）**")
        st.json(trace.plan)

        st.markdown("**③ 动力层 · 预定义模板**")
        st.code(f"模板库文件: {trace.template_name}.sql", language="text")
        st.code(trace.sql if trace.sql else "—", language="sql")
        st.caption(f"绑定参数（参数化查询，防注入）：`{trace.params}`")

        st.markdown("**④ 动态层 · SQLite 执行结果**")
        if trace.error:
            st.error(f"执行失败：{trace.error}")
        else:
            render_result(trace)


# ---------------------------------------------------------------------------
# 主界面：聊天
# ---------------------------------------------------------------------------
st.title("💬 FAB 自然语言查数")
st.caption("自然语言 → 业务对象映射（语义层）→ 预定义查询逻辑（动力层）→ 模拟数据执行（动态层）")

# 快速示例问题（chips）
chip_cols = st.columns(3)
question = None
for i, s in enumerate(SAMPLE_QUESTIONS):
    if chip_cols[i % 3].button(s, key=f"chip-{i}", use_container_width=True):
        question = s
if question is None:
    question = st.chat_input("例如：帮我查一下 3号机 上周的良率趋势")

# 渲染历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("trace"):
            render_trace(msg["trace"])

# 新问题处理
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("语义层匹配 → 意图提取 → 模板拼装 → SQL 执行 …"):
            agent = FabQueryAgent(
                ontology=ontology,
                llm_config=LLMConfig(enabled=llm_enabled, model=llm_model,
                                     base_url=llm_base_url, api_key=llm_api_key),
            )
            trace = agent.ask(question)
        summary = build_summary(trace)
        st.markdown(summary)
        render_trace(trace)

    st.session_state.messages.append(
        {"role": "assistant", "content": summary, "trace": trace})