"""
FabCapacityAgent - Streamlit 共享 UI 组件

提供页面级公共组件,避免 5 个 pages 文件重复 CSS / 标题 / 卡片样式代码。

使用方式 (任意 pages/*.py 顶部):
    import sys, os
    sys.path.insert(0, <project_root>)
    from utils.ui_components import init_page

    init_page("实时监控", icon="📊", subtitle="设备状态 / WIP 实时看板")
"""

import os
import sys
from pathlib import Path
from typing import Optional

# 让 streamlit run 也能正确找到项目根
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from utils.helpers import now_str, get_config
from utils.constants import (
    UI_PRIMARY,
    UI_BACKGROUND,
    UI_ACCENT,
    UI_SUCCESS,
    UI_WARNING,
    UI_DANGER,
    UI_TEXT,
)


# =============================================================================
# 全局 CSS (亮色主题 — 浅底深字, 偏白)
# =============================================================================

_DARK_CSS = f"""
<style>
/* 全局背景 */
.stApp {{
    background: linear-gradient(135deg, {UI_BACKGROUND} 0%, #E8EDF3 100%);
    color: {UI_TEXT};
}}

/* 页面标题区 */
.page-title {{
    background: linear-gradient(90deg, {UI_PRIMARY} 0%, #4A7AB5 100%);
    padding: 20px 28px;
    border-radius: 12px;
    border-left: 6px solid {UI_ACCENT};
    box-shadow: 0 4px 16px rgba(46, 90, 143, 0.18);
    margin-bottom: 20px;
}}
.page-title h1 {{
    color: #FFFFFF;
    font-size: 24px;
    margin: 0;
    letter-spacing: 1px;
}}
.page-title p {{
    color: #C8E0F0;
    font-size: 12px;
    margin: 4px 0 0 0;
    letter-spacing: 0.5px;
}}

/* KPI 卡片 */
div[data-testid="stMetric"] {{
    background: #FFFFFF;
    border: 1px solid rgba(46, 90, 143, 0.15);
    border-radius: 10px;
    padding: 16px 18px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    transition: all 0.2s ease;
}}
div[data-testid="stMetric"]:hover {{
    border-color: {UI_ACCENT};
    box-shadow: 0 4px 14px rgba(0, 153, 204, 0.18);
}}
div[data-testid="stMetric"] label {{
    color: #5A6B7E !important;
    font-size: 12px !important;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
    color: {UI_TEXT} !important;
    font-size: 22px !important;
    font-weight: 700;
}}

/* 侧边栏 */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #FFFFFF 0%, #F0F2F5 100%);
    border-right: 1px solid rgba(46, 90, 143, 0.15);
}}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {{
    color: {UI_PRIMARY};
}}

/* Tab */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px;
    background-color: rgba(46, 90, 143, 0.06);
    border-radius: 10px;
    padding: 5px;
}}
.stTabs [data-baseweb="tab"] {{
    color: {UI_TEXT};
    border-radius: 8px;
    padding: 6px 16px;
    font-weight: 500;
}}
.stTabs [aria-selected="true"] {{
    background-color: {UI_PRIMARY} !important;
    color: #FFFFFF !important;
}}

/* 数据表格 */
.stDataFrame, .stTable {{
    background: #FFFFFF;
    border-radius: 10px;
    padding: 6px;
    border: 1px solid rgba(46, 90, 143, 0.1);
}}

/* 状态徽章 */
.badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
.badge-success {{ background: {UI_SUCCESS}; color: #FFFFFF; }}
.badge-warning {{ background: {UI_WARNING}; color: #FFFFFF; }}
.badge-danger  {{ background: {UI_DANGER};  color: #FFFFFF; }}
.badge-info    {{ background: {UI_ACCENT};  color: #FFFFFF; }}

/* 隐藏 Streamlit 默认 footer / header */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}

/* Plotly 图表文字颜色 */
.js-plotly-plot .plotly .gtitle,
.js-plotly-plot .plotly .xtick text,
.js-plotly-plot .plotly .ytick text {{
    fill: {UI_TEXT} !important;
}}
</style>
"""


# =============================================================================
# 页面初始化 (CSS + 标题)
# =============================================================================

def init_page(
    title: str,
    icon: str = "📊",
    subtitle: Optional[str] = None,
    show_time: bool = True,
) -> None:
    """
    页面初始化: 注入深蓝科技风 CSS + 渲染标题区。

    Args:
        title: 页面标题 (中文)
        icon: 标题前缀 emoji
        subtitle: 副标题 (英文/描述), 可选
        show_time: 是否显示当前时间
    """
    # 注入 CSS
    st.markdown(_DARK_CSS, unsafe_allow_html=True)

    # 渲染标题
    time_str = f" · {now_str()}" if show_time else ""
    sub_html = f"<p>{subtitle}{time_str}</p>" if subtitle or show_time else ""
    st.markdown(
        f"""
        <div class="page-title">
            <h1>{icon} {title}</h1>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# 通用辅助: 状态徽章 HTML
# =============================================================================

def status_badge(status: str, label: Optional[str] = None) -> str:
    """
    生成状态徽章 HTML 片段。

    Args:
        status: success / warning / danger / info
        label: 显示文本, 默认取 status 中文
    """
    cls = {
        "success": "badge-success",
        "warning": "badge-warning",
        "danger": "badge-danger",
        "info": "badge-info",
    }.get(status, "badge-info")
    text = label or {
        "success": "成功",
        "warning": "警告",
        "danger": "失败",
        "info": "信息",
    }.get(status, status)
    return f'<span class="badge {cls}">{text}</span>'


# =============================================================================
# 通用辅助: Plotly 图表亮色主题
# =============================================================================

def dark_chart_layout(fig, height: int = 380) -> None:
    """给 Plotly Figure 应用亮色透明背景,与全局主题对齐。"""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=UI_TEXT,
        height=height,
        legend=dict(font=dict(color=UI_TEXT)),
        title_font_color=UI_TEXT,
    )
    fig.update_xaxes(gridcolor="rgba(46,90,143,0.10)", zerolinecolor="rgba(46,90,143,0.20)")
    fig.update_yaxes(gridcolor="rgba(46,90,143,0.10)", zerolinecolor="rgba(46,90,143,0.20)")
