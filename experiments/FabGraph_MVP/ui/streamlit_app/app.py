"""Streamlit 应用主入口。

提供侧边栏导航，切换元数据浏览 / 图谱可视化 / 语义检索 /
NL2SQL / SQL 分析等页面。

启动命令：
    streamlit run ui/streamlit_app/app.py

对应ResNet推理引擎入口：初始化共享缓存 -> 渲染页面。
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

# 确保 src 目录在 sys.path 中
_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main() -> None:
    """Streamlit 应用主函数。"""
    st.set_page_config(
        page_title="FabGraph MVP",
        page_icon=":material/hub:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("FabGraph MVP")
    st.caption("晶圆厂数据资产知识图谱与 NL2SQL 系统")

    # 侧边栏页面选择
    with st.sidebar:
        st.header("导航")
        page = st.radio(
            "选择页面",
            options=[
                "元数据浏览",
                "图谱可视化",
                "语义检索",
                "NL2SQL",
                "SQL 分析",
            ],
            key="page_nav",
        )
        st.divider()
        # 显示当前运行模式
        try:
            from ui.streamlit_app.services import get_settings_cached
            settings = get_settings_cached()
            st.caption("运行模式")
            st.write(f"- LLM Mock: `{settings.llm.use_mock}`")
            st.write(f"- Embedding Mock: `{settings.embedding.use_mock}`")
            st.write(f"- Provider: `{settings.llm.provider}`")
        except Exception as e:
            st.warning(f"配置加载失败: {e}")

    # 按选择渲染页面
    try:
        if page == "元数据浏览":
            from ui.streamlit_app.page_metadata import render_metadata_page
            render_metadata_page()
        elif page == "图谱可视化":
            from ui.streamlit_app.page_graph import render_graph_page
            render_graph_page()
        elif page == "语义检索":
            from ui.streamlit_app.page_search import render_search_page
            render_search_page()
        elif page == "NL2SQL":
            from ui.streamlit_app.page_nl2sql import render_nl2sql_page
            render_nl2sql_page()
        elif page == "SQL 分析":
            from ui.streamlit_app.page_sql_analyzer import render_sql_analyzer_page
            render_sql_analyzer_page()
    except Exception as e:
        st.error(f"页面渲染失败: {e}")
        with st.expander("详情"):
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
