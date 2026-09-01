"""
Streamlit UI: 晶圆厂 LLM 两阶段查询增强 MVP
============================================================
展示「小模型预处理 + DeepSeek」vs「直接 DeepSeek」的对比效果
运行: streamlit run fab_mvp/app.py
"""
import sys
import os
import json

# 确保能 import fab_mvp 包 (streamlit run 时把脚本目录加入sys.path, 需补上项目根)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from fab_mvp.inference import MODE_LABELS, get_predictor
from fab_mvp.agent import run_comparison
from fab_mvp.eval_cases import EVAL_CASES

st.set_page_config(page_title="晶圆厂LLM两阶段查询增强", page_icon="🔬", layout="wide")

# ResNet Step 1: 标题与说明
st.title("🔬 晶圆厂 LLM 两阶段查询增强 MVP")
st.markdown(
    "**架构**: 用户口语问题 → 微调后 Qwen2-0.5B (小模型) 预处理 → 结构化上下文 → DeepSeek (强模型) 生成最终SQL/回答\n\n"
    "**对比**: 增强路径 (小模型+DeepSeek) vs 直接路径 (仅DeepSeek, 无领域知识注入)"
)
st.divider()

# ResNet Step 2: 输入区
col_in1, col_in2 = st.columns([3, 1])
with col_in1:
    query = st.text_area(
        "工程师口语提问",
        value="昨天3号机良率掉的厉害咋回事",
        height=80,
        help="模拟晶圆厂工程师日常口语提问, 含缩写/黑话/模糊指代",
    )
with col_in2:
    mode = st.selectbox("小模型预处理模式", list(MODE_LABELS.keys()),
                        format_func=lambda x: MODE_LABELS[x])
    run_btn = st.button("🚀 运行对比", type="primary")

# 示例问题快捷填充
st.markdown("**示例问题 (点击填入)**:")
example_cols = st.columns(len(EVAL_CASES[:5]))
for i, (q, _, _, _) in enumerate(EVAL_CASES[:5]):
    with example_cols[i]:
        if st.button(q[:14] + "...", key=f"ex_{i}", help=q):
            st.session_state["query_input"] = q
            st.rerun()

# ResNet Step 3: 运行并展示对比
if run_btn or query:
    if not query.strip():
        st.warning("请输入问题")
        st.stop()
    with st.spinner("小模型预处理 + DeepSeek 生成中 (首次运行需加载小模型, 约几十秒)..."):
        result = run_comparison(query, mode)

    small_out = result.get("small_output")
    enhanced = result.get("enhanced_answer")
    direct = result.get("direct_answer")
    err = result.get("error")

    if err:
        st.error(f"部分流程出错: {err}")

    # 小模型预处理结果
    st.subheader("① 小模型预处理结果")
    if small_out:
        if small_out.get("_parse_error"):
            st.warning("小模型输出JSON解析失败, 原始输出:")
            st.code(small_out.get("raw", ""), language="text")
        else:
            st.json(small_out)
    else:
        st.warning("小模型无输出")

    st.divider()

    # 增强路径 vs 直接路径 对比
    st.subheader("② 最终回答对比")
    col_e, col_d = st.columns(2)
    with col_e:
        st.markdown(f"**🟢 增强路径** (小模型 {MODE_LABELS[mode]} → DeepSeek)")
        if enhanced:
            st.markdown(enhanced)
        else:
            st.warning("无输出")
    with col_d:
        st.markdown("**⚪ 直接路径** (仅 DeepSeek, 无领域知识注入)")
        if direct:
            st.markdown(direct)
        else:
            st.warning("无输出")

    st.divider()
    with st.expander("💡 对比说明"):
        st.markdown(
            "- **增强路径**: 小模型先把口语/黑话翻译为结构化上下文 (意图/实体/领域提示/SQL模板), "
            "DeepSeek 拿到后能精准定位表与模板, 输出更专业的SQL与分析思路。\n"
            "- **直接路径**: DeepSeek 直接面对口语问题, 缺乏领域黑话与表结构知识, "
            "可能误解'3号机''掉得厉害'等表述, SQL可能与晶圆厂实际schema不符。\n"
            "- 小模型 (0.5B) 微调成本低, 专注'窄而深'的领域信号放大, 把推理留给强模型。"
        )
