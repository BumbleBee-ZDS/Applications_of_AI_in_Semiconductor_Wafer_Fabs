"""
FabCapacityAgent - Streamlit 主入口 (Home / Dashboard)

职责:
  1) 配置 Streamlit 页面 (深蓝科技风, wide 布局, 中文界面)
  2) 首次运行自动初始化数据库 + 生成 MES 模拟数据
  3) 渲染首页仪表盘: 全厂 KPI 卡片 + 工序产能概览 + Agent 链路状态
  4) 侧边栏导航到 5 个子页面 (实时监控/历史分析/产能规划/Agent工作台/系统设置)

启动方式:
  streamlit run app.py
"""

import os
import sys
from pathlib import Path

# 让 streamlit run 也能正确找到项目根
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.helpers import (
    get_logger,
    get_config,
    now_str,
    safe_round,
    to_pct,
    format_kpi,
    process_cn_name,
    kpi_cn_name,
)
from utils.constants import (
    ALL_PROCESSES,
    PROCESS_NAME_CN,
    EQUIP_STATUS_NAME_CN,
    EQUIP_STATUS_COLOR,
    KPI_OEE,
    KPI_WIP,
    KPI_DAILY_OUTPUT,
    KPI_CYCLE_TIME,
    KPI_UTILIZATION,
    KPI_BOTTLENECK_RATE,
    AGENT_NAME_CN,
    AGENT_PERCEPTION,
    AGENT_ANALYSIS,
    AGENT_DECISION,
    AGENT_EXECUTION,
    TABLE_LOT_HISTORY,
    TABLE_EQUIPMENT,
    TABLE_LOTS,
    CHART_PALETTE,
    UI_PRIMARY,
    UI_BACKGROUND,
    UI_ACCENT,
    UI_SUCCESS,
    UI_WARNING,
    UI_DANGER,
    UI_TEXT,
)
from models.database import get_db
from models.capacity import AgentLogDAO
from services.capacity_calculator import get_calculator

logger = get_logger("App", level="INFO")


# =============================================================================
# 页面配置 (必须在所有 st 命令之前)
# =============================================================================

st.set_page_config(
    page_title=get_config("ui", "page_title", default="FabCapacityAgent"),
    page_icon=get_config("ui", "page_icon", default="🏭"),
    layout=get_config("ui", "layout", default="wide"),
    initial_sidebar_state=get_config("ui", "initial_sidebar_state", default="expanded"),
)


# =============================================================================
# 亮色主题 全局 CSS 注入 (浅底深字, 偏白)
# =============================================================================

def inject_css() -> None:
    """注入亮色主题的全局样式,覆盖 Streamlit 默认主题。"""
    st.markdown(
        f"""
        <style>
        /* 全局背景 */
        .stApp {{
            background: linear-gradient(135deg, {UI_BACKGROUND} 0%, #E8EDF3 100%);
            color: {UI_TEXT};
        }}

        /* 主标题区 */
        .main-title {{
            background: linear-gradient(90deg, {UI_PRIMARY} 0%, #4A7AB5 100%);
            padding: 24px 32px;
            border-radius: 12px;
            border-left: 6px solid {UI_ACCENT};
            box-shadow: 0 4px 16px rgba(46, 90, 143, 0.18);
            margin-bottom: 24px;
        }}
        .main-title h1 {{
            color: #FFFFFF;
            font-size: 28px;
            margin: 0;
            letter-spacing: 1px;
        }}
        .main-title p {{
            color: #C8E0F0;
            font-size: 13px;
            margin: 6px 0 0 0;
            letter-spacing: 0.5px;
        }}

        /* KPI 卡片 */
        div[data-testid="stMetric"] {{
            background: #FFFFFF;
            border: 1px solid rgba(46, 90, 143, 0.15);
            border-radius: 10px;
            padding: 18px 20px;
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
            font-size: 26px !important;
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
            gap: 8px;
            background-color: rgba(46, 90, 143, 0.06);
            border-radius: 10px;
            padding: 6px;
        }}
        .stTabs [data-baseweb="tab"] {{
            color: {UI_TEXT};
            border-radius: 8px;
            padding: 8px 18px;
            font-weight: 500;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {UI_PRIMARY} !important;
            color: #FFFFFF !important;
            box-shadow: 0 2px 8px rgba(46, 90, 143, 0.3);
        }}

        /* 数据表格 */
        .stDataFrame, .stTable {{
            background: #FFFFFF;
            border-radius: 10px;
            padding: 8px;
            border: 1px solid rgba(46, 90, 143, 0.1);
        }}

        /* 警告/提示框 */
        .stAlert {{
            border-radius: 10px;
        }}

        /* 隐藏 Streamlit 默认 footer / header */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        header[data-testid="stHeader"] {{ background: transparent; }}

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

        /* Agent 链路时间轴 */
        .agent-timeline {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #FFFFFF;
            border: 1px solid rgba(46, 90, 143, 0.1);
            padding: 16px;
            border-radius: 10px;
            margin-top: 10px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }}
        .agent-node {{
            text-align: center;
            flex: 1;
        }}
        .agent-node .dot {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin: 0 auto 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
        }}
        .agent-arrow {{
            color: {UI_ACCENT};
            font-size: 20px;
            opacity: 0.5;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# 首次运行: 自动初始化数据库 + 生成模拟数据
# =============================================================================

@st.cache_resource(show_spinner="正在初始化数据库...")
def ensure_database_ready() -> bool:
    """
    首次运行自动建表 + 生成 MES 模拟数据。
    使用 @st.cache_resource 保证整个 Session 只执行一次。
    """
    try:
        db = get_db()
        db.initialize_schema(force=False)

        # 检查是否已有数据,没有则触发生成器
        existing = db.count(TABLE_LOT_HISTORY)
        if existing == 0:
            logger.info("首次运行, 触发 MES 模拟数据生成...")
            # 延迟导入,避免在数据已存在时浪费加载时间
            from data.generator import MESDataGenerator
            gen = MESDataGenerator(use_llm_polish=False)  # 首次启动关闭 LLM 加速
            gen.run(force=False)
        return True
    except Exception as exc:
        logger.error(f"数据库初始化失败: {exc}", exc_info=True)
        return False


# =============================================================================
# 页面组件: 标题区
# =============================================================================

def render_header() -> None:
    """渲染主标题与系统状态徽章。"""
    db_ok = ensure_database_ready()
    badge = (
        f'<span class="badge badge-success">● 系统正常</span>'
        if db_ok
        else f'<span class="badge badge-danger">● 初始化失败</span>'
    )
    st.markdown(
        f"""
        <div class="main-title">
            <h1>🏭 FabCapacityAgent — 晶圆厂 AI 产能智能中枢</h1>
            <p>Semiconductor Fab Capacity Intelligence Agent · PTA Cycle · {now_str()} &nbsp; {badge}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# 页面组件: KPI 卡片行
# =============================================================================

def render_kpi_cards(snapshot: dict) -> None:
    """渲染全厂 KPI 卡片 (6 个核心指标)。

    CapacitySnapshot.to_dict() 返回扁平字段:
      overall_oee / wip_total_wafers / daily_output_24h /
      avg_cycle_time_h / by_process / bottleneck_rank
    """
    if not isinstance(snapshot, dict):
        snapshot = {}

    oee = snapshot.get("overall_oee", 0)
    wip = snapshot.get("wip_total_wafers", 0)
    daily_out = snapshot.get("daily_output_24h", 0)
    ct = snapshot.get("avg_cycle_time_h", 0)

    # 平均利用率: 从 by_process 聚合
    by_proc = snapshot.get("by_process", {}) or {}
    if by_proc:
        utils = [float(p.get("utilization", 0)) for p in by_proc.values() if isinstance(p, dict)]
        util = sum(utils) / len(utils) if utils else 0
    else:
        util = 0

    # 瓶颈工序 Top1
    bn_rank = snapshot.get("bottleneck_rank", []) or []
    bn = bn_rank[0] if bn_rank else "N/A"

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric(label="全厂 OEE", value=to_pct(oee))
    with col2:
        st.metric(label="WIP 在制品", value=f"{int(wip):,} 片")
    with col3:
        st.metric(label="24h 产出", value=f"{int(daily_out):,} 片")
    with col4:
        st.metric(label="平均 CycleTime", value=f"{safe_round(ct, 1)} h")
    with col5:
        st.metric(label="平均利用率", value=to_pct(util))
    with col6:
        st.metric(label="瓶颈工序", value=process_cn_name(bn) if bn != "N/A" else "N/A")


# =============================================================================
# 页面组件: 工序产能概览图表
# =============================================================================

def render_process_overview(snapshot: dict) -> None:
    """渲染 8 道工序的 OEE / WIP / 利用率 概览图。

    by_process 是 Dict[process_code, ProcessKPI.to_dict()],
    每个 value 含: process / equipment_count / utilization /
    availability / performance / quality / oee / uph /
    wip_wafers / avg_cycle_time_h / is_bottleneck / bottleneck_rate
    """
    by_proc = snapshot.get("by_process", {}) if isinstance(snapshot, dict) else {}
    if not by_proc:
        st.info("暂无工序级产能数据,请先运行 Agent 链路。")
        return

    # 把 dict-of-dict 转为 DataFrame
    rows = [p for p in by_proc.values() if isinstance(p, dict)]
    df = pd.DataFrame(rows)
    if df.empty:
        st.info("工序级产能数据为空。")
        return

    df["工序"] = df["process"].apply(process_cn_name)
    df["OEE"] = df["oee"].astype(float)
    df["WIP"] = df["wip_wafers"].astype(float)
    df["利用率"] = df["utilization"].astype(float)

    tab1, tab2, tab3 = st.tabs(["📊 OEE 对比", "📦 WIP 分布", "⚙️ 利用率"])

    with tab1:
        if "OEE" in df.columns:
            fig = px.bar(
                df, x="工序", y="OEE", color="工序",
                color_discrete_sequence=CHART_PALETTE,
                title="各工序 OEE (综合设备效率)",
                text=df["OEE"].apply(lambda v: to_pct(v)),
            )
            fig.update_layout(
                showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", font_color=UI_TEXT,
                yaxis_tickformat=".0%", yaxis_range=[0, 1],
                height=380,
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("缺少 OEE 字段")

    with tab2:
        if "WIP" in df.columns:
            fig = px.bar(
                df, x="工序", y="WIP", color="工序",
                color_discrete_sequence=CHART_PALETTE,
                title="各工序 WIP (在制品分布)",
                text=df["WIP"].apply(lambda v: f"{int(v):,}"),
            )
            fig.update_layout(
                showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", font_color=UI_TEXT,
                height=380,
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("缺少 WIP 字段")

    with tab3:
        if "利用率" in df.columns:
            fig = px.bar(
                df, x="工序", y="利用率", color="工序",
                color_discrete_sequence=CHART_PALETTE,
                title="各工序平均利用率",
                text=df["利用率"].apply(lambda v: to_pct(v)),
            )
            fig.update_layout(
                showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", font_color=UI_TEXT,
                yaxis_tickformat=".0%", yaxis_range=[0, 1],
                height=380,
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("缺少利用率字段")


# =============================================================================
# 页面组件: 设备状态分布 (饼图)
# =============================================================================

def render_equipment_status_pie() -> None:
    """渲染全厂设备状态分布饼图。"""
    try:
        db = get_db()
        df = db.query_df(f"""
            SELECT status, COUNT(*) AS cnt
            FROM {TABLE_EQUIPMENT}
            GROUP BY status
            ORDER BY cnt DESC
        """)
        if df.empty:
            st.info("暂无设备数据")
            return

        df["状态"] = df["status"].apply(lambda s: EQUIP_STATUS_NAME_CN.get(s, s))
        df["颜色"] = df["status"].apply(lambda s: EQUIP_STATUS_COLOR.get(s, "#888888"))

        fig = go.Figure(data=[go.Pie(
            labels=df["状态"],
            values=df["cnt"],
            hole=0.55,
            marker=dict(colors=df["颜色"]),
            textfont=dict(color=UI_TEXT, size=13),
            textinfo="label+percent",
        )])
        fig.update_layout(
            title="全厂设备状态分布",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=UI_TEXT,
            height=380,
            showlegend=True,
            legend=dict(font=dict(color=UI_TEXT)),
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as exc:
        st.error(f"设备状态查询失败: {exc}")


# =============================================================================
# 页面组件: Agent 链路时间轴
# =============================================================================

def render_agent_timeline() -> None:
    """渲染 4 个 Agent 的 PTA 链路时间轴 (静态展示)。"""
    agents = [
        (AGENT_PERCEPTION, "🔍", "Perception", "感知数据"),
        (AGENT_ANALYSIS, "📈", "Analysis", "分析瓶颈"),
        (AGENT_DECISION, "🎯", "Decision", "生成决策"),
        (AGENT_EXECUTION, "📝", "Execution", "输出报告"),
    ]

    nodes_html = []
    for i, (agent_type, icon, en_name, cn_desc) in enumerate(agents):
        nodes_html.append(f"""
            <div class="agent-node">
                <div class="dot" style="background:{CHART_PALETTE[i]};color:#1A2332;">{icon}</div>
                <div style="color:{UI_ACCENT};font-weight:600;font-size:13px;">{en_name}</div>
                <div style="color:{UI_TEXT};font-size:11px;">{cn_desc}</div>
                <div style="color:#8899AA;font-size:10px;">{AGENT_NAME_CN.get(agent_type, '')}</div>
            </div>
        """)
        if i < len(agents) - 1:
            nodes_html.append('<div class="agent-arrow">→</div>')

    st.markdown(
        f'<div class="agent-timeline">{"".join(nodes_html)}</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# 页面组件: 最近 Agent 执行记录
# =============================================================================

def render_recent_agent_logs() -> None:
    """渲染最近 10 次 Agent 全链路 run 记录。

    AgentLogDAO.recent_runs() 返回 DataFrame:
      run_id / created_at / succ_steps / fail_steps / total_ms
    """
    try:
        log_dao = AgentLogDAO()
        df = log_dao.recent_runs(limit=10)
        if df is None or df.empty:
            st.info("暂无 Agent 执行记录,请到「Agent 工作台」运行一次全链路。")
            return

        # 字段重命名 + 文本化
        df = df.copy()
        if "created_at" in df.columns:
            df["created_at"] = df["created_at"].astype(str).str[:19]
        if "succ_steps" in df.columns and "fail_steps" in df.columns:
            df["状态"] = df.apply(
                lambda r: f"✅ {int(r['succ_steps'])} 步成功"
                          + (f" / ❌ {int(r['fail_steps'])} 步失败" if r["fail_steps"] else ""),
                axis=1,
            )
        if "total_ms" in df.columns:
            df["总耗时"] = df["total_ms"].apply(
                lambda v: f"{int(v)/1000:.2f} s" if pd.notna(v) and v else "-"
            )

        keep = ["created_at", "run_id", "状态", "总耗时"]
        df = df[[c for c in keep if c in df.columns]]
        df.columns = ["时间", "Run ID", "执行状态", "总耗时"][: len(df.columns)]
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.warning(f"Agent 日志加载失败: {exc}")


# =============================================================================
# 页面组件: 侧边栏
# =============================================================================

def render_sidebar() -> None:
    """渲染侧边栏: 系统信息 + 导航说明。"""
    with st.sidebar:
        st.markdown("### 🏭 FabCapacityAgent")
        st.caption("晶圆厂 AI 产能智能中枢")

        st.markdown("---")
        st.markdown("#### 📑 页面导航")
        st.markdown("""
        - 🏠 **首页仪表盘** (当前)
        - 📊 **实时监控** — 设备状态 / WIP 实时看板
        - 📈 **历史分析** — 趋势 / 异常 / 瓶颈诊断
        - 🎯 **产能规划** — What-If 仿真 / 预测
        - 🤖 **Agent 工作台** — PTA 链路 / 报告
        - ⚙️ **系统设置** — LLM / 数据库 / 主题
        """)

        st.markdown("---")
        st.markdown("#### ℹ️ 系统信息")
        try:
            db = get_db()
            eq_cnt = db.count(TABLE_EQUIPMENT)
            lot_cnt = db.count(TABLE_LOTS)
            hist_cnt = db.count(TABLE_LOT_HISTORY)
            st.metric(label="设备总数", value=f"{eq_cnt}")
            st.metric(label="在制批次", value=f"{lot_cnt}")
            st.metric(label="工序历史", value=f"{hist_cnt:,}")
        except Exception:
            st.warning("数据库统计失败")


# =============================================================================
# 主函数
# =============================================================================

def main() -> None:
    inject_css()
    render_sidebar()
    render_header()

    # 确保数据库就绪
    if not ensure_database_ready():
        st.error("❌ 数据库初始化失败,请检查日志或运行 `python models/database.py` 自检。")
        st.stop()

    # === 第 1 区: KPI 卡片 ===
    st.markdown("### 📊 全厂产能 KPI 概览")

    # 构建一次 snapshot 用于首页展示
    @st.cache_data(ttl=300, show_spinner="正在计算产能快照...")
    def _build_snapshot_cached():
        try:
            calc = get_calculator()
            return calc.build_snapshot(window_hours=24).to_dict()
        except Exception as exc:
            logger.error(f"快照构建失败: {exc}", exc_info=True)
            return {}

    snapshot = _build_snapshot_cached()
    render_kpi_cards(snapshot)

    st.markdown("---")

    # === 第 2 区: 工序概览 + 设备状态 ===
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown("### 🏭 工序产能概览")
        render_process_overview(snapshot)
    with col_right:
        st.markdown("### ⚙️ 设备状态分布")
        render_equipment_status_pie()

    st.markdown("---")

    # === 第 3 区: Agent 链路 ===
    st.markdown("### 🤖 Agent PTA 链路")
    st.caption("Perceive → Think → Act 循环,串联 4 个 Agent 完成感知→分析→决策→执行")
    render_agent_timeline()

    st.markdown("#### 📋 最近 Agent 执行记录")
    render_recent_agent_logs()

    # 页脚
    st.markdown("---")
    st.caption(
        f"FabCapacityAgent v1.0 · 半导体晶圆厂 AI 产能智能中枢 · "
        f"Powered by Streamlit + SQLite + Plotly · {now_str()}"
    )


if __name__ == "__main__":
    main()
