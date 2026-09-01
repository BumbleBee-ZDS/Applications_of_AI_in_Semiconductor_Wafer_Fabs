# -*- coding: utf-8 -*-
"""在三个 OUTLINE 中插入第七部分·第27章条目（参考文献段之前）"""
import io, os

ROOT = r'H:\code\traework\AI在半导体晶圆厂的应用'

BLOCKS = {
    'zh-CN': ('## 参考文献', """## 第七部分：动手实验实验室

### 第27章 动手实验实验室——把关键概念跑起来

- 27.1 为什么需要动手实验
- 27.2 实验环境准备
- 27.3 实验一：Ontology 驱动的 Text2SQL（fab_ontology_text2sql）
  - 本体三段式架构：语义层/动力层/动态层，受控 SQL 生成
- 27.4 实验二：晶圆厂 Ontology MVP——根因分析 Agent（wafer_ontology_mvp）
  - NetworkX 本体图 + LangGraph ReAct，"对象-链接-动作"三层映射
- 27.5 实验三：FabGraph 双图谱知识平台（FabGraph_MVP）
  - Schema/Lineage 图谱 + NL2SQL + 图算法
- 27.6 实验四：K8s 式声明式调度（C9S_agent）
  - 控制论调谐循环，四 Agent 协作，与命令式管道对比
- 27.7 实验五：产能规划 PTA Agent（FabCapacityAgent）
  - OEE 监控、瓶颈检测、蒙特卡洛 What-If 仿真
- 27.8 实验六：LoRA 微调两阶段查询增强（fab_llm_fine_tuning）
  - 数据合成→训练→推理→量化评估全链路
- 27.9 实验七：RTD 实时派工与人机协同（fab_ai_rtd_mvp）
  - 感知→RAG 诊断→调度→仿真→L1-L4 分级审批→审计
- 27.10 实验八：CIM 可信系统红蓝对抗（wafer-trust-guard）
  - 规则+嵌入+LLM Judge+记忆闭环的四层验证
- 27.11 实验九：多 Agent 评估框架（fab_agent_test）
  - 过程质量/资源成本/系统韧性三维实时评估
- 27.12 从实验到生产：改造指引

## 参考文献"""),
    'zh-TW': ('## 參考文獻', """## 第七部分：動手實驗實驗室

### 第27章 動手實驗實驗室——把關鍵概念跑起來

- 27.1 為什麼需要動手實驗
- 27.2 實驗環境準備
- 27.3 實驗一：Ontology 驅動的 Text2SQL（fab_ontology_text2sql）
  - 本體三段式架構：語義層/動力層/動態層，受控 SQL 生成
- 27.4 實驗二：晶圓廠 Ontology MVP——根因分析 Agent（wafer_ontology_mvp）
  - NetworkX 本體圖 + LangGraph ReAct，「物件-連結-動作」三層映射
- 27.5 實驗三：FabGraph 雙圖譜知識平台（FabGraph_MVP）
  - Schema/Lineage 圖譜 + NL2SQL + 圖演算法
- 27.6 實驗四：K8s 式宣告式排程（C9S_agent）
  - 控制論調諧迴圈，四 Agent 協作，與命令式管道對比
- 27.7 實驗五：產能規劃 PTA Agent（FabCapacityAgent）
  - OEE 監控、瓶頸檢測、蒙地卡羅 What-If 模擬
- 27.8 實驗六：LoRA 微調兩階段查詢增強（fab_llm_fine_tuning）
  - 資料合成→訓練→推理→量化評估全鏈路
- 27.9 實驗七：RTD 即時派工與人機協同（fab_ai_rtd_mvp）
  - 感知→RAG 診斷→排程→模擬→L1-L4 分級審批→稽核
- 27.10 實驗八：CIM 可信系統紅藍對抗（wafer-trust-guard）
  - 規則+嵌入+LLM Judge+記憶閉環的四層驗證
- 27.11 實驗九：多 Agent 評估框架（fab_agent_test）
  - 過程品質/資源成本/系統韌性三維即時評估
- 27.12 從實驗到生產：改造指引

## 參考文獻"""),
    'en': ('## References', """## Part 7: Hands-On Lab

### Chapter 27 Hands-On Lab — Running the Key Concepts

- 27.1 Why Hands-On Experiments Matter
- 27.2 Lab Environment Setup
- 27.3 Experiment 1: Ontology-Driven Text2SQL (fab_ontology_text2sql)
  - Three-stage ontology architecture: semantic / motive / dynamic layers, controlled SQL generation
- 27.4 Experiment 2: Wafer Fab Ontology MVP — RCA Agent (wafer_ontology_mvp)
  - NetworkX ontology graph + LangGraph ReAct, object-link-action three-layer mapping
- 27.5 Experiment 3: FabGraph Dual-Graph Knowledge Platform (FabGraph_MVP)
  - Schema/Lineage graphs + NL2SQL + graph algorithms
- 27.6 Experiment 4: K8s-Style Declarative Scheduling (C9S_agent)
  - Control-theoretic reconciliation loop, four-Agent collaboration, compared with imperative pipelines
- 27.7 Experiment 5: Capacity Planning PTA Agent (FabCapacityAgent)
  - OEE monitoring, bottleneck detection, Monte-Carlo What-If simulation
- 27.8 Experiment 6: LoRA Fine-Tuning Two-Stage Query Enhancement (fab_llm_fine_tuning)
  - Full pipeline: data synthesis → training → inference → quantitative evaluation
- 27.9 Experiment 7: RTD Real-Time Dispatching & Human-AI Collaboration (fab_ai_rtd_mvp)
  - Perception → RAG diagnosis → dispatch → simulation → L1-L4 tiered approval → audit
- 27.10 Experiment 8: CIM Trusted System Red-Blue Adversarial Exercise (wafer-trust-guard)
  - Four-layer verification: rules + embeddings + LLM Judge + memory closed loop
- 27.11 Experiment 9: Multi-Agent Evaluation Framework (fab_agent_test)
  - Real-time three-dimensional evaluation of quality / cost / resilience
- 27.12 From Experiments to Production: A Retrofitting Guide

## References"""),
}

for lang, (anchor, block) in BLOCKS.items():
    p = os.path.join(ROOT, lang, 'OUTLINE.md')
    t = io.open(p, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in t else '\n'
    block_n = block.replace('\n', nl)
    if anchor in t:
        t = t.replace(anchor, block_n, 1)
        io.open(p, 'w', encoding='utf-8', newline='').write(t)
        print(lang + '/OUTLINE.md: inserted')
    else:
        print(lang + '/OUTLINE.md: ANCHOR NOT FOUND')
