"""FabWiki —— 半导体晶圆厂数据资产知识库与 Text2SQL MVP（Streamlit 入口）。

四个页面（侧边栏导航）：
1. 🏠 首页         项目介绍、OKF 理念、知识包统计、一键初始化
2. 📚 知识浏览     按 type/tag/关键词过滤 + 渲染 markdown
3. 🕸️ 血缘图谱     pyvis 全库知识链接图 + 单表 N 跳血缘
4. 💬 Text2SQL    知识导航式对话 + 生成 SQL + 执行 + 日志

Mock 模式是一等公民：无 LLM_API_KEY 时自动降级 Mock，页面顶部提示。
"""
from __future__ import annotations

import base64
import sys
import tempfile
import warnings
from pathlib import Path

import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# 抑制 Altair 对空数据的 vegalite type 推断警告
warnings.filterwarnings("ignore", message=".*infer vegalite type.*")

# 抑制 Windows asyncio ProactorPipeTransport ConnectionResetError 噪音
if sys.platform == "win32":
    import asyncio

    def _silence_conn_reset(loop, ctx):
        exc = ctx.get("exception", "")
        if "ConnectionResetError" in str(exc):
            return
        loop.default_exception_handler(ctx)

    try:
        loop = asyncio.get_event_loop()
        if loop:
            loop.set_exception_handler(_silence_conn_reset)
    except RuntimeError:
        pass  # Streamlit 线程无 event loop，跳过

# 本文件位于项目根目录，确保可导入 config / core
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config  # noqa: E402
from core import compiler, db, extractor, knowledge, text2sql  # noqa: E402

st.set_page_config(page_title="FabWiki · 晶圆厂知识库 Text2SQL",
                   page_icon="🏭", layout="wide")


# --------------------------------------------------------------------------
# 状态与共享对象
# --------------------------------------------------------------------------
def get_kb() -> knowledge.KnowledgeBase:
    """缓存知识索引（一次会话内复用；初始化后重建）。"""
    if "kb" not in st.session_state:
        st.session_state.kb = knowledge.KnowledgeBase()
    return st.session_state.kb


@st.cache_resource
def get_engine() -> text2sql.Text2SQL:
    return text2sql.Text2SQL()


def rebuild() -> None:
    """一键初始化后重建会话内缓存。"""
    if "kb" in st.session_state:
        del st.session_state.kb
    get_engine.clear()   # 清空 @st.cache_resource 缓存的 Text2SQL 引擎（其内部持有旧 KnowledgeBase）


def run_pipeline(drop: bool = False) -> dict:
    """建库 → 抽取 → 编译（Mock/LLM），返回编译统计。与 scripts/init_db 共用逻辑。"""
    db.init_db(drop_existing=drop)
    extractor.extract_all()
    stats = compiler.compile_all()
    rebuild()
    return stats


# --------------------------------------------------------------------------
# 通用 UI 小组件
# --------------------------------------------------------------------------
def mock_banner() -> None:
    if not config.LLM_AVAILABLE:
        st.info("🔒 **Mock 模式**：未检测到 `LLM_API_KEY`，知识编译与 Text2SQL 使用内置离线模板。"
                "在 `.env` 配置 Key 后重启即可走真实 LLM。", icon="ℹ️")


def frontmatter_table(node: knowledge.KnowledgeNode) -> None:
    """用表格展示 frontmatter（含可在 app 内跳转的 related 链接）。"""
    rows = {
        "title": node.title,
        "type": node.type,
        "resource": node.resource,
        "confidence": node.confidence,
        "updated": node.updated,
    }
    if node.tags:
        rows["tags"] = ", ".join(node.tags)
    st.dataframe(pd.DataFrame([rows]), width="stretch")


# --------------------------------------------------------------------------
# 页面 1：首页
# --------------------------------------------------------------------------
def page_home() -> None:
    mock_banner()
    st.title("🏭 FabWiki")
    st.caption("半导体晶圆厂数据资产知识库 —— OKF + 知识导航式 Text2SQL MVP")

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("""
### 背景
大型晶圆厂（Fab）的 Oracle 数仓中，MES/EAP/YMS 表结构复杂、字段编码含义晦涩、
存储过程逻辑充满隐性知识（如 `LOT_STS='05'` 表示 **Hold 待 MRB 评审**），
导致朴素 Text2SQL 直接查询准确率极低。

### OKF 理念
> **一个知识包 = 一个文件夹；一个知识点 = 一个 Markdown 文件
> （YAML frontmatter + 正文）；文件间用相对路径链接构成知识图谱。**

FabWiki 基于 OKF 思想，把数据字典 + 隐性知识 + Text2SQL 注意事项"编译"成
可导航的知识图谱，让 LLM「确定性读取」而非「向量分块检索」所需知识后写 SQL。

### 核心闭环
1. **L1 抽取**：从 SQLite（模拟 Oracle）自动抽取数据字典 →
   `knowledge/raw/dictionary/`
2. **L2 编译**：LLM（或 Mock）把 raw「编译」为 wiki 知识文件，含隐性知识、
   Text2SQL 注意事项 → `knowledge/wiki/`
3. **对话**：知识浏览 / 血缘图谱 / 知识导航式 Text2SQL
""")
    with c2:
        kb = get_kb()
        st.subheader("📊 知识包统计")
        s = kb.stats()
        ctypes = s["types"]
        col1, col2 = st.columns(2)
        col1.metric("知识点总数", s["nodes"])
        col2.metric("图谱边（链接）", s["edges"])
        if s["nodes"] == 0:
            st.info("尚未初始化，点击下方「一键初始化」生成知识包。")
        else:
            st.write("**按类型**")
            type_data = []
            for t in ["Table", "Column", "Metric", "Spec"]:
                if t in ctypes:
                    type_data.append({"type": t, "count": ctypes[t], "icon": _TYPE_ICONS.get(t, "📄")})
            for t, cnt in ctypes.items():
                if t not in ["Table", "Column", "Metric", "Spec"]:
                    type_data.append({"type": t, "count": cnt, "icon": "📄"})
            st.dataframe(pd.DataFrame([{"type": f"{row['icon']} {row['type']}", "count": row["count"]}
                                        for row in type_data]),
                         width="stretch", hide_index=True)
            st.write("**confidence 分布**")
            conf_data = pd.DataFrame(
                [{"confidence": k, "count": v} for k, v in s["conf"].items()])
            st.bar_chart(conf_data, x="confidence", y="count")

    st.divider()
    st.subheader("⚙️ 一键初始化")
    st.write("建库 → 抽取 L1 → 编译 L2（Mock/LLM）→ 刷新知识索引，可重复执行（幂等）。")
    b1, b2 = st.columns(2)
    if b1.button("🚀 初始化（建库+抽取+编译）", width="stretch"):
        with st.spinner("正在建库、抽取、编译知识……"):
            stats = run_pipeline(drop=False)
        st.success(f"完成：编译 {stats['tables']} 张表 + {stats['metrics']} 个指标，"
                   f"其中 LLM {stats['llm']} / Mock {stats['mock']}。")
        st.rerun()
    if b2.button("♻️ 重建并初始化（drop 后重来）", width="stretch", type="secondary"):
        with st.spinner("重建数据库并重新初始化……"):
            stats = run_pipeline(drop=True)
        st.success("已重建完成。")
        st.rerun()


# --------------------------------------------------------------------------
# 页面 2：知识浏览
# --------------------------------------------------------------------------
_TYPE_ICONS = {
    "Table": "📊",
    "Column": "🔖",
    "Metric": "📈",
    "Spec": "📐",
    "unknown": "📄",
}


def page_browse() -> None:
    mock_banner()
    st.title("📚 知识浏览")
    kb = get_kb()

    # 左侧过滤
    with st.sidebar:
        st.subheader("🎛️ 过滤")
        types = kb.types()
        sel_type = st.selectbox("type", ["全部"] + types)
        sel_tag = st.selectbox("tag", ["全部"] + kb.tags())
        kw = st.text_input("关键词", "")

    # 右侧知识点列表 + 渲染
    nodes = kb.all(type_=None if sel_type == "全部" else sel_type,
                   tag=None if sel_tag == "全部" else sel_tag,
                   kw=kw or None)
    if not nodes:
        st.warning("没有匹配的知识点，请调整过滤条件。")
        return

    # 按 type 分组显示
    by_type: dict[str, list[knowledge.KnowledgeNode]] = {}
    for n in nodes:
        by_type.setdefault(n.type, []).append(n)

    # 默认选中的节点
    default = st.session_state.get("sel_node")
    all_paths = [str(n.path) for n in nodes]
    if default not in all_paths:
        default = nodes[0].path

    # 用两栏布局：左侧列表，右侧详情（比 selectbox + 全页刷新更平滑）
    list_col, detail_col = st.columns([1, 3])

    with list_col:
        st.caption(f"共 {len(nodes)} 个知识点")
        for t in sorted(by_type.keys()):
            st.markdown(f"**{_TYPE_ICONS.get(t, '📄')} {t}（{len(by_type[t])}）**")
            for n in by_type[t]:
                is_active = str(n.path) == default
                btn_label = n.resource
                if len(btn_label) > 28:
                    btn_label = btn_label[:26] + "…"
                if st.button(
                    btn_label,
                    key=f"nav_{n.path}",
                    width="stretch",
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state["sel_node"] = str(n.path)
                    st.rerun()
            st.divider()

    with detail_col:
        node = kb.get(default)
        if not node:
            st.info("选择左侧的知识点查看详情。")
            return
        # 标题 + 类型标签
        icon = _TYPE_ICONS.get(node.type, "📄")
        st.subheader(f"{icon} {node.title}")
        st.caption(f"type: **{node.type}** · resource: `{node.resource}`")
        frontmatter_table(node)
        st.markdown("---")
        st.markdown(node.body, unsafe_allow_html=False)

        # 关联知识点：用 chip 样式的按钮展示
        if node.links:
            st.markdown("### 🔗 关联知识点")
            link_cols = st.columns(min(len(node.links), 4))
            for i, dst in enumerate(node.links):
                target = kb.get(dst)
                if not target:
                    continue
                t_icon = _TYPE_ICONS.get(target.type, "📄")
                label = f"{t_icon} {target.resource}"
                if len(label) > 22:
                    label = label[:20] + "…"
                with link_cols[i % 4]:
                    if st.button(label, key=f"rel_{node.path}_{dst}",
                                 width="stretch"):
                        st.session_state["sel_node"] = dst
                        st.rerun()


# --------------------------------------------------------------------------
# 页面 3：血缘图谱
# --------------------------------------------------------------------------
def page_graph() -> None:
    mock_banner()
    st.title("🕸️ 血缘图谱")

    kb = get_kb()
    g = kb.graph
    type_color = {"Table": "#e74c3c", "Metric": "#3498db",
                  "Spec": "#2ecc71", "Column": "#9b59b6", "unknown": "#95a5a6"}

    # 展平 networkx 到 pyvis
    try:
        from pyvis.network import Network
    except Exception as e:  # pragma: no cover
        st.error(f"未安装 pyvis：{e}")
        return

    net = Network(height="560px", width="100%", directed=True,
                  notebook=False, bgcolor="#ffffff", font_color="#222222",
                  cdn_resources="in_line")
    # 物理引擎配置：更稳定的布局
    net.set_options("""{
        "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 120,
                "springConstant": 0.08
            },
            "stabilization": {
                "enabled": true,
                "iterations": 100
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100
        }
    }""")

    for rel, node in kb.nodes.items():
        color = type_color.get(node.type, "#95a5a6")
        label = node.resource
        if len(label) > 20:
            label = label[:18] + "…"
        net.add_node(str(rel), label=label, color=color,
                     title=f"{node.title}\n类型: {node.type}\n置信度: {node.confidence}",
                     size=22 if node.type == "Table" else 16)
    for u, v in g.edges():
        net.add_edge(str(u), str(v), arrows="to", color="#bbbbbb", width=1)

    # 用 Streamlit components 原生嵌入 HTML
    # 注意：pyvis 的 write_html 在 Windows 上用系统默认编码（GBK）写文件，
    # 遇到 © 等 Unicode 字符会报 UnicodeEncodeError。
    # 解决方案：调用 generate_html() 让 pyvis 内部构建 HTML 字串到 self.html，
    # 然后直接传给 components.html()，完全绕过文件 I/O。
    try:
        net.generate_html()
    except Exception:
        # 某些 pyvis 版本 generate_html 需要 name 参数
        net.generate_html(name="graph")
    components.html(net.html, height=600, scrolling=False)

    # 图例
    legend_col1, legend_col2, legend_col3, legend_col4, legend_col5 = st.columns(5)
    legend_items = [
        ("Table", "📊 表", type_color["Table"]),
        ("Column", "🔖 字段", type_color["Column"]),
        ("Metric", "📈 指标", type_color["Metric"]),
        ("Spec", "📐 规范", type_color["Spec"]),
    ]
    cols = st.columns(len(legend_items))
    for i, (tname, tlabel, tcolor) in enumerate(legend_items):
        with cols[i]:
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:8px;'>"
                f"<div style='width:14px;height:14px;border-radius:50%;"
                f"background:{tcolor};'></div>"
                f"<span style='font-size:13px;'>{tlabel}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    st.caption("拖拽节点可调整位置，滚轮缩放，悬停节点查看详情。"
               "在下方选择某张表观察其 N 跳血缘子图。")

    # 单表 N 跳血缘
    st.divider()
    st.subheader("🔍 单表 N 跳血缘")
    tables = sorted([str(n.path) for n in kb.all(type_="Table")])
    if not tables:
        st.info("尚未编译表知识，请先在首页一键初始化。")
        return

    col_sel, col_hop = st.columns([2, 1])
    with col_sel:
        sel_t = st.selectbox("选择表知识点", tables,
                             format_func=lambda p: kb.get(p).resource if kb.get(p) else p)
    with col_hop:
        hops = st.slider("跳数", 1, 3, 1)

    nb = kb.neighbors(sel_t, hops=hops)
    up, down = nb["upstream"], nb["downstream"]

    # 如果有上下游节点，显示一个迷你子图
    if up or down:
        try:
            from pyvis.network import Network as Net2
            sub_net = Net2(height="320px", width="100%", directed=True,
                           notebook=False, bgcolor="#f8f9fa",
                           font_color="#222222", cdn_resources="in_line")
            sub_net.set_options("""{
                "physics": {
                    "enabled": true,
                    "solver": "forceAtlas2Based",
                    "forceAtlas2Based": {
                        "gravitationalConstant": -30,
                        "centralGravity": 0.02,
                        "springLength": 100
                    },
                    "stabilization": { "iterations": 50 }
                }
            }""")
            # 中心节点
            center_node = kb.get(sel_t)
            sub_net.add_node(sel_t, label=center_node.resource if center_node else sel_t,
                             color="#e74c3c", size=30,
                             title="当前选中的表")
            # 上游
            for p in up:
                n = kb.get(p)
                color = type_color.get(n.type if n else "unknown", "#95a5a6")
                sub_net.add_node(p, label=n.resource if n else p, color=color, size=18,
                                 title=n.title if n else p)
                sub_net.add_edge(p, sel_t, arrows="to", color="#999", width=2)
            # 下游
            for p in down:
                n = kb.get(p)
                color = type_color.get(n.type if n else "unknown", "#95a5a6")
                sub_net.add_node(p, label=n.resource if n else p, color=color, size=18,
                                 title=n.title if n else p)
                sub_net.add_edge(sel_t, p, arrows="to", color="#999", width=2)
            try:
                sub_net.generate_html()
            except Exception:
                sub_net.generate_html(name="subgraph")
            components.html(sub_net.html, height=340, scrolling=False)
        except Exception:
            pass  # pyvis 不可用时降级为纯文本

    c_up, c_down = st.columns(2)
    with c_up:
        st.markdown("**⬆️ 上游（被引用 / 依赖的主档）**")
        if up:
            for p in up:
                n = kb.get(p)
                icon = _TYPE_ICONS.get(n.type, "📄") if n else "📄"
                st.markdown(f"- {icon} {n.title if n else p} `{n.resource if n else p}`")
        else:
            st.markdown("_（无上游）_")
    with c_down:
        st.markdown("**⬇️ 下游（引用本表的表/指标）**")
        if down:
            for p in down:
                n = kb.get(p)
                icon = _TYPE_ICONS.get(n.type, "📄") if n else "📄"
                st.markdown(f"- {icon} {n.title if n else p} `{n.resource if n else p}`")
        else:
            st.markdown("_（无下游）_")


# --------------------------------------------------------------------------
# 页面 4：Text2SQL
# --------------------------------------------------------------------------
_EXAMPLE_QS = [
    "当前 Hold 中的批次数量？",
    "最近一个月各产品的良率趋势？",
    "PHOTO 工序缺陷 Top10？",
    "设备当前可用的各类型数量？",
    "各产品在制品的批次数量？",
]


def page_text2sql() -> None:
    mock_banner()
    st.title("💬 Text2SQL 知识导航")

    engine = get_engine()

    with st.sidebar:
        st.subheader("🧠 知识导航说明")
        st.markdown("对话时系统会：定位相关表 → **确定性读取**这些表的完整知识"
                    "（含隐性知识、Text2SQL 注意事项）+ 规则文件 → 组装 prompt "
                    "→ 生成并执行 SQL。失败自动重试一次。")

    st.markdown("**试一试内置示例**：")
    for q in _EXAMPLE_QS:
        if st.button(q, key=f"ex_{q}"):
            st.session_state["q"] = q
            st.session_state["ask"] = True

    question = st.text_input("输入你的数据查询问题：",
                             value=st.session_state.get("q", ""))
    ask = st.button("🔍 查询", type="primary",
                    disabled=not question.strip())

    if (ask or st.session_state.get("ask")) and question.strip():
        st.session_state["ask"] = False
        with st.spinner("知识导航 + 生成 SQL + 执行中……"):
            res = engine.ask(question.strip())

        if not res.success:
            st.error(f"❌ {res.error}")
            if res.referenced:
                st.info("引用的知识文件：" + "、".join(res.referenced))
            return

        # 侧栏：引用的知识文件
        with st.sidebar:
            with st.expander(f"本次引用的知识文件（{len(res.referenced)}）"):
                for r in res.referenced:
                    st.markdown(f"- `{r}`")

        # mock/llm 标签
        mode = "Mock" if res.mock else "LLM"
        st.success(f"✅ 执行成功（{mode} 模式，{len(res.df)} 行）")

        tab_tbl, tab_sql, tab_log = st.tabs(
            ["📊 数据表格", "🗃️ 生成的 SQL", "📜 执行日志"])
        with tab_tbl:
            st.dataframe(res.df, width="stretch")
        with tab_sql:
            st.code(res.sql, language="sql")
            st.download_button("📋 复制 SQL / 下载",
                               data=res.sql, file_name="query.sql", mime="text/plain")
        with tab_log:
            for l in res.logs:
                st.write(f"- {l}")
    elif not (ask or st.session_state.get("ask")):
        st.info("在下方输入问题，或点击上方示例按钮开始。")


# --------------------------------------------------------------------------
# 导航
# --------------------------------------------------------------------------
def main() -> None:
    st.sidebar.title("FabWiki")
    page = st.sidebar.radio(
        "导航",
        ["🏠 首页", "📚 知识浏览", "🕸️ 血缘图谱", "💬 Text2SQL"],
        label_visibility="collapsed")
    if page == "🏠 首页":
        page_home()
    elif page == "📚 知识浏览":
        page_browse()
    elif page == "🕸️ 血缘图谱":
        page_graph()
    else:
        page_text2sql()


if __name__ == "__main__":
    main()