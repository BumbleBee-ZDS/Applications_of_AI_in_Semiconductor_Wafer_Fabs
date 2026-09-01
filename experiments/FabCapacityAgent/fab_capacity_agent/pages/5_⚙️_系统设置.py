"""
FabCapacityAgent - 系统设置页面

职责:
  1) LLM 配置 (DeepSeek / Qwen) + 连接测试
  2) 数据库信息 (表 / 行数 / 大小) + 数据重建
  3) 系统配置查看 (settings.yaml 关键项)
  4) 关于 / 版本信息
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

from utils.ui_components import init_page, dark_chart_layout
from utils.helpers import get_logger, get_config, resolve_path, now_str
from utils.constants import (
    TABLE_EQUIPMENT, TABLE_LOTS, TABLE_LOT_HISTORY,
    TABLE_EQUIPMENT_EVENTS, TABLE_DAILY_OUTPUT, TABLE_AGENT_LOGS,
    FILE_SETTINGS, FILE_DB_DEFAULT,
)
from models.database import get_db

logger = get_logger("PageSettings", level="INFO")

init_page("系统设置", icon="⚙️", subtitle="LLM / Database / Configuration")


# =============================================================================
# Tab 1: LLM 配置
# =============================================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "🤖 LLM 配置", "🗄 数据库管理", "📋 系统配置", "ℹ️ 关于",
])

with tab1:
    st.markdown("### 🤖 LLM 大模型配置")

    # 读取 .env 状态
    env_path = resolve_path("../.env")  # 项目根上一级
    if not env_path.exists():
        env_path = _PROJECT_ROOT.parent / ".env"

    st.markdown(f"**.env 文件路径**: `{env_path}`")
    st.markdown(f"**存在**: {'✅' if env_path.exists() else '❌'}")

    if env_path.exists():
        # 读取并显示 (脱敏)
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                env_content = f.read()
            # 脱敏: API Key 只显示前 8 位 + 后 4 位
            masked_lines = []
            for line in env_content.splitlines():
                if "API_KEY" in line and "=" in line:
                    k, v = line.split("=", 1)
                    if len(v) > 12:
                        masked_lines.append(f"{k}={v[:8]}...{v[-4:]} (已脱敏, 共 {len(v)} 字符)")
                    else:
                        masked_lines.append(f"{k}={'*' * len(v)} (过短)")
                else:
                    masked_lines.append(line)
            st.code("\n".join(masked_lines), language="ini")
        except Exception as exc:
            st.error(f"读取 .env 失败: {exc}")

    st.markdown("---")

    # 测试 LLM 连接
    st.markdown("#### 🔌 LLM 连接测试")

    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        if st.button("🧪 测试 DeepSeek", use_container_width=True):
            try:
                from utils.llm_client import LLMClient, PROVIDER_DEEPSEEK
                client = LLMClient(provider=PROVIDER_DEEPSEEK)
                if not client.is_configured():
                    st.warning("⚠️ DeepSeek API Key 未配置")
                else:
                    with st.spinner("正在测试..."):
                        resp = client.chat(
                            messages=[{"role": "user", "content": "回复 'OK' 即可, 这是连接测试。"}],
                            max_tokens=20,
                        )
                        if resp:
                            st.success(f"✅ DeepSeek 连接成功\n\n响应: {resp[:100]}")
                        else:
                            st.error("❌ DeepSeek 返回空响应")
            except Exception as exc:
                st.error(f"❌ DeepSeek 测试失败: {exc}")

    with col_t2:
        if st.button("🧪 测试 Qwen", use_container_width=True):
            try:
                from utils.llm_client import LLMClient, PROVIDER_QWEN
                client = LLMClient(provider=PROVIDER_QWEN)
                if not client.is_configured():
                    st.warning("⚠️ Qwen API Key 未配置")
                else:
                    with st.spinner("正在测试..."):
                        resp = client.chat(
                            messages=[{"role": "user", "content": "回复 'OK' 即可, 这是连接测试。"}],
                            max_tokens=20,
                        )
                        if resp:
                            st.success(f"✅ Qwen 连接成功\n\n响应: {resp[:100]}")
                        else:
                            st.error("❌ Qwen 返回空响应")
            except Exception as exc:
                st.error(f"❌ Qwen 测试失败: {exc}")

    st.markdown("---")

    # 使用说明
    st.markdown("#### 📖 LLM 使用说明")
    st.info("""
    **LLM 在系统中的作用:**
    - **数据生成器**: 智能润色故障事件描述 (可选)
    - **预测服务**: `forecast_output(use_llm=True)` 时增强时序预测
    - **分析 Agent**: 生成趋势摘要文本
    - **执行 Agent**: 生成自然语言产能分析报告

    **配置方式:**
    1. 在项目根 (FabCapacityAgent/.env) 中填入 API Key
    2. DeepSeek: https://platform.deepseek.com/
    3. Qwen (DashScope): https://dashscope.console.aliyun.com/
    4. 在 Agent 工作台勾选「启用 LLM 增强」即可使用

    **未配置时**: 系统自动回退到本地模板/统计模型,功能不受影响。
    """)

# =============================================================================
# Tab 2: 数据库管理
# =============================================================================

with tab2:
    st.markdown("### 🗄 数据库管理")

    try:
        db = get_db()
        db_path = resolve_path(FILE_DB_DEFAULT)
        db_size_mb = db_path.stat().st_size / 1024 / 1024 if db_path.exists() else 0

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("数据库路径", str(db_path.name))
        with c2: st.metric("文件大小", f"{db_size_mb:.2f} MB")
        with c3: st.metric("SQLite 版本", "3.x")

        st.markdown("#### 📊 各表行数统计")

        tables = [
            (TABLE_EQUIPMENT, "设备主数据"),
            (TABLE_LOTS, "批次信息"),
            (TABLE_LOT_HISTORY, "工序历史"),
            (TABLE_EQUIPMENT_EVENTS, "设备事件"),
            (TABLE_DAILY_OUTPUT, "日产出汇总"),
            (TABLE_AGENT_LOGS, "Agent 日志"),
        ]
        rows = []
        for tbl, desc in tables:
            cnt = db.count(tbl)
            rows.append({"表名": tbl, "说明": desc, "行数": cnt})
        df_tables = pd.DataFrame(rows)
        st.dataframe(df_tables, use_container_width=True, hide_index=True)

        st.markdown("#### ⚠️ 危险操作区")

        with st.expander("🔧 数据重建 (会清除现有数据)", expanded=False):
            st.warning("""
            **警告**: 以下操作会 DROP 现有数据表并重新生成模拟数据。
            - 所有 equipment / lots / lot_history / equipment_events / daily_output 会被清除
            - agent_logs 会保留 (作为历史记录)
            - 生成耗时约 30~60 秒
            """)

            col_r1, col_r2 = st.columns([1, 1])
            with col_r1:
                days = st.number_input("历史天数", min_value=7, max_value=180, value=90, step=1)
                lots_per_day = st.number_input("日均投料批次", min_value=10, max_value=200, value=60, step=5)
            with col_r2:
                seed = st.number_input("随机种子", min_value=1, max_value=9999, value=42, step=1)
                use_llm_polish = st.checkbox("LLM 润色事件描述", value=False)

            confirm = st.checkbox("我确认要重建数据", value=False)
            if st.button("🔴 重建数据", disabled=not confirm, type="primary"):
                with st.spinner(f"正在重建数据 ({days}天 / {lots_per_day}批/天)..."):
                    try:
                        from data.generator import MESDataGenerator
                        gen = MESDataGenerator(
                            history_days=int(days),
                            lots_per_day=int(lots_per_day),
                            seed=int(seed),
                            use_llm_polish=use_llm_polish,
                        )
                        gen.run(force=True)
                        st.success(f"✅ 数据重建完成! equipment={gen.stats.get('equipment', 0)}, lot_history={gen.stats.get('lot_history', 0)}")
                        st.cache_data.clear()
                        st.cache_resource.clear()
                    except Exception as exc:
                        st.error(f"❌ 重建失败: {exc}")

        with st.expander("🧹 清空 Agent 日志", expanded=False):
            if st.button("清空 agent_logs 表", type="primary"):
                try:
                    db.execute(f"DELETE FROM {TABLE_AGENT_LOGS}")
                    st.success("✅ Agent 日志已清空")
                except Exception as exc:
                    st.error(f"❌ 清空失败: {exc}")

    except Exception as exc:
        st.error(f"数据库信息加载失败: {exc}")

# =============================================================================
# Tab 3: 系统配置
# =============================================================================

with tab3:
    st.markdown("### 📋 系统配置 (settings.yaml)")

    settings_path = resolve_path(FILE_SETTINGS)
    st.markdown(f"**配置文件路径**: `{settings_path}`")

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            content = f.read()
        st.code(content, language="yaml")
    except Exception as exc:
        st.error(f"读取配置失败: {exc}")

    st.markdown("---")
    st.markdown("#### 🔑 关键配置项速查")

    cfg_keys = [
        ("database.path", "数据库路径"),
        ("production.wafer_size", "晶圆尺寸 (mm)"),
        ("production.wafers_per_lot", "每批晶圆数"),
        ("equipment.total_count", "设备总数"),
        ("data_generator.history_days", "历史数据天数"),
        ("agent.orchestrator.timeout", "Pipeline 超时 (s)"),
        ("agent.orchestrator.max_retries", "最大重试次数"),
        ("prediction.moving_average_window", "MA 窗口"),
        ("simulator.monte_carlo_iterations", "蒙特卡洛迭代数"),
    ]
    rows = []
    for path, desc in cfg_keys:
        keys = path.split(".")
        val = get_config(*keys, default="N/A")
        rows.append({"配置项": path, "说明": desc, "当前值": str(val)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# =============================================================================
# Tab 4: 关于
# =============================================================================

with tab4:
    st.markdown("### ℹ️ 关于 FabCapacityAgent")

    st.markdown("""
    #### 🏭 FabCapacityAgent - 晶圆厂 AI 产能智能中枢

    **版本**: v1.0 MVP

    **简介**: 半导体晶圆厂 AI Agent 产能计算系统,基于 PTA (Perceive-Think-Act) 循环框架,
    串联感知 → 分析 → 决策 → 执行 4 个 Agent,实现全厂产能的实时监控、历史分析、预测规划。

    #### 🏗 技术栈

    | 模块 | 技术 |
    |------|------|
    | UI 框架 | Streamlit (多页应用) |
    | 数据存储 | SQLite + pandas |
    | 图表可视化 | Plotly |
    | Agent 框架 | 自研 PTA (无 LangChain) |
    | LLM 增强 | DeepSeek / Qwen (可选) |
    | 预测算法 | 移动平均 + 线性回归 + LLM |
    | 风险评估 | 蒙特卡洛模拟 |

    #### 📐 系统架构

    ```
    用户查询
        ↓
    ┌─────────────────────────────────────┐
    │   Orchestrator (编排器)             │
    │   ┌─────────┐  ┌─────────┐          │
    │   │Perception│→│ Analysis │          │
    │   │ Agent    │  │ Agent    │          │
    │   └─────────┘  └─────────┘          │
    │       ↓             ↓               │
    │   ┌─────────┐  ┌─────────┐          │
    │   │ Decision│→│Execution │          │
    │   │ Agent   │  │ Agent    │          │
    │   └─────────┘  └─────────┘          │
    └─────────────────────────────────────┘
        ↓
    产能分析报告 + 优化建议
    ```

    #### 📊 业务覆盖

    - **8 道主工序**: 光刻 / 刻蚀 / 沉积 / 离子注入 / 扩散 / 抛光 / 量测 / 清洗
    - **3 种产品**: Logic_A / Logic_B / Memory_C
    - **120 台设备**: 按 8 道工序分配
    - **核心 KPI**: OEE / UPH / WIP / CycleTime / Throughput / BottleneckRate
    - **6 张数据表**: equipment / lots / lot_history / equipment_events / daily_output / agent_logs

    #### 🚀 快速开始

    ```bash
    # 1) 安装依赖
    pip install -r requirements.txt

    # 2) 启动应用 (首次运行自动建库 + 生成模拟数据)
    streamlit run app.py
    ```

    #### 📁 项目结构

    ```
    fab_capacity_agent/
    ├── app.py                    # Streamlit 主入口
    ├── requirements.txt
    ├── config/settings.yaml      # 全局配置
    ├── data/
    │   ├── generator.py          # MES 模拟数据生成器
    │   └── fab_capacity.db       # SQLite 数据库 (自动生成)
    ├── models/
    │   ├── database.py           # DB 管理器
    │   ├── equipment.py          # 设备/事件模型
    │   ├── wafer.py              # 批次模型
    │   └── capacity.py           # 产能快照/DAO
    ├── services/
    │   ├── capacity_calculator.py  # OEE/UPH 计算
    │   ├── predictor.py            # 产能预测
    │   ├── bottleneck_detector.py  # 瓶颈检测
    │   └── what_if_simulator.py    # What-If 仿真
    ├── agents/
    │   ├── base_agent.py         # PTA 基类
    │   ├── perception_agent.py   # 感知 Agent
    │   ├── analysis_agent.py     # 分析 Agent
    │   ├── decision_agent.py     # 决策 Agent
    │   ├── execution_agent.py    # 执行 Agent
    │   └── orchestrator.py       # 编排器
    ├── pages/                    # 5 个 Streamlit 子页面
    └── utils/
        ├── constants.py          # 全局常量
        ├── helpers.py            # 通用工具
        ├── llm_client.py         # LLM 客户端
        └── ui_components.py      # UI 共享组件
    ```
    """)

    st.markdown("---")
    st.caption(f"FabCapacityAgent v1.0 · 生成于 {now_str()} · Powered by Streamlit + SQLite + Plotly")
