"""📚 工艺知识库：全部文档展示 + RAG 检索演示（千问 Embedding）。"""

from __future__ import annotations

import streamlit as st

from utils import helpers, knowledge_base

st.set_page_config(page_title="5 知识库", page_icon="📚", layout="wide")
helpers.init_session_state()

st.title("📚 工艺知识库（RAG 检索）")

with st.spinner("正在向量化工艺知识库（千问 Embedding）..."):
    kb_info = knowledge_base.ensure_indexed()
st.caption(f"向量化模式：**{kb_info['mode']}** ｜ 文档数 {kb_info['docs']} ｜ 向量维度 {kb_info.get('dim', '-')}")
if kb_info.get("error"):
    st.warning(f"⚠️ 千问 Embedding 暂不可用，已回退本地伪向量：{kb_info['error']}")

st.subheader("🗂 全部知识文档")
for doc in knowledge_base.KNOWLEDGE_DOCS:
    with st.expander(f"{doc['doc_id']} {doc['title']}（{doc['category']}）"):
        st.write(doc["content"])

st.subheader("🔎 RAG 检索演示")
with st.form("rag_query_form"):
    query = st.text_input("输入查询（例如：CVD 温度漂移怎么处理？Q-Time 超时怎么办？）")
    top_k = st.slider("Top-K", 1, len(knowledge_base.KNOWLEDGE_DOCS), 3)
    submitted = st.form_submit_button("🔍 检索")

if submitted:
    if not query.strip():
        st.warning("请输入查询内容")
    else:
        with st.spinner("调用千问 Embedding 生成查询向量并检索..."):
            hits = knowledge_base.retrieve(query.strip(), top_k=top_k)
        st.markdown(f"**“{query.strip()}” 的 Top-{len(hits)} 检索结果**（相似度越高越相关）：")
        for i, (doc, score) in enumerate(hits, start=1):
            with st.expander(f"#{i} {doc['doc_id']} {doc['title']}　相似度 {score:.4f}", expanded=i == 1):
                st.markdown(f"**类别**：{doc['category']}")
                st.write(doc["content"])
