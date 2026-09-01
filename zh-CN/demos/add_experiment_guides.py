# -*- coding: utf-8 -*-
"""在15个相关章节末尾追加"本章配套实验"指引段落（三语并行）"""
import io, os

ROOT = r'H:\code\traework\AI在半导体晶圆厂的应用'
LINK = '../part7/chapter27.md'

# 章节号 -> (简体, 繁体, 英文)
GUIDES = {
    'chapter02': (
        '> **本章配套实验**：第27章 27.11 节的多 Agent 评估框架（`demos/experiments/fab_agent_test`）以白盒方式演示了 2.6 节所述的 Agent 概念如何落地为可评估的系统——规划、工具调用、反思、编排四模块协作，并实时评估过程质量、资源成本与系统韧性。',
        '> **本章配套實驗**：第27章 27.11 節的多 Agent 評估框架（`demos/experiments/fab_agent_test`）以白盒方式演示了 2.6 節所述的 Agent 概念如何落地為可評估的系統——規劃、工具呼叫、反思、編排四模組協作，並即時評估過程品質、資源成本與系統韌性。',
        '> **Hands-on experiment for this chapter**: The multi-Agent evaluation framework in Section 27.11 of Chapter 27 (`demos/experiments/fab_agent_test`) demonstrates in a white-box manner how the Agent concept from Section 2.6 becomes an evaluable system — four collaborating modules (planner, toolset, reflector, orchestrator) with real-time assessment of process quality, resource cost, and resilience.'),
    'chapter07': (
        '> **本章配套实验**：第27章 27.6 节的 K8s 式声明式调度实验（`demos/experiments/C9S_agent`）把本章讨论的智能排程思想做成了可交互的系统——用"期望态-实际态"调谐循环替代人工调度脚本，并可在界面注入设备故障观察系统自愈，零外部依赖、秒级启动。',
        '> **本章配套實驗**：第27章 27.6 節的 K8s 式宣告式排程實驗（`demos/experiments/C9S_agent`）把本章討論的智慧排程思想做成了可互動的系統——用「期望態-實際態」調諧迴圈取代人工排程腳本，並可在介面注入設備故障觀察系統自愈，零外部依賴、秒級啟動。',
        '> **Hands-on experiment for this chapter**: The K8s-style declarative scheduling experiment in Section 27.6 of Chapter 27 (`demos/experiments/C9S_agent`) turns the smart scheduling ideas of this chapter into an interactive system — replacing hand-written dispatch scripts with an expected-vs-actual reconciliation loop, with injectable equipment faults to observe self-healing. Zero external dependencies, starts in seconds.'),
    'chapter08': (
        '> **本章配套实验**：第27章 27.9 节的 RTD 实时派工实验（`demos/experiments/fab_ai_rtd_mvp`）完整演示了本章的实时异常响应如何走向闭环——感知、RAG 诊断、调度建议、仿真验证，再到 L1–L4 分级人工审批与审计留痕，正是制程/设备工程场景中"AI 建议、人来把关"的工程形态。',
        '> **本章配套實驗**：第27章 27.9 節的 RTD 即時派工實驗（`demos/experiments/fab_ai_rtd_mvp`）完整演示了本章的即時異常回應如何走向閉環——感知、RAG 診斷、排程建議、模擬驗證，再到 L1–L4 分級人工審批與稽核留痕，正是製程/設備工程場景中「AI 建議、人來把關」的工程形態。',
        '> **Hands-on experiment for this chapter**: The RTD real-time dispatching experiment in Section 27.9 of Chapter 27 (`demos/experiments/fab_ai_rtd_mvp`) demonstrates the full closed loop of this chapter\'s real-time anomaly response — perception, RAG diagnosis, dispatch recommendation, simulation validation, and then L1–L4 tiered human approval with audit trails: the engineering form of "AI proposes, humans gatekeep" in PE/EE scenarios.'),
    'chapter10': (
        '> **本章配套实验**：第27章 27.7 节的产能规划 PTA Agent（`demos/experiments/FabCapacityAgent`）是本章方法论的可运行版本——OEE 实时监控、基于排队论的瓶颈定位、蒙特卡洛 What-If 仿真一应俱全，建议在"先找瓶颈、再定投资"一节之后动手体验。',
        '> **本章配套實驗**：第27章 27.7 節的產能規劃 PTA Agent（`demos/experiments/FabCapacityAgent`）是本章方法論的可執行版本——OEE 即時監控、基於排隊論的瓶頸定位、蒙地卡羅 What-If 模擬一應俱全，建議在「先找瓶頸、再定投資」一節之後動手體驗。',
        '> **Hands-on experiment for this chapter**: The capacity-planning PTA Agent in Section 27.7 of Chapter 27 (`demos/experiments/FabCapacityAgent`) is a runnable version of this chapter\'s methodology — OEE monitoring, queueing-theory bottleneck detection, and Monte-Carlo What-If simulation all included. Try it right after the "find the bottleneck before investing" section.'),
    'chapter11': (
        '> **本章配套实验**：第27章 27.9 节的 RTD 实时派工实验（`demos/experiments/fab_ai_rtd_mvp`）演示了建设期最稀缺的能力——人机协同的信任机制：L1–L4 分级审批让低风险动作自动放行、高风险动作必须人工确认，全部决策留痕可追溯。',
        '> **本章配套實驗**：第27章 27.9 節的 RTD 即時派工實驗（`demos/experiments/fab_ai_rtd_mvp`）演示了建設期最稀缺的能力——人機協同的信任機制：L1–L4 分級審批讓低風險動作自動放行、高風險動作必須人工確認，全部決策留痕可追溯。',
        '> **Hands-on experiment for this chapter**: The RTD real-time dispatching experiment in Section 27.9 of Chapter 27 (`demos/experiments/fab_ai_rtd_mvp`) demonstrates the scarcest capability of the construction phase — the trust mechanism of human-AI collaboration: L1–L4 tiered approval lets low-risk actions pass automatically while high-risk ones require human confirmation, with every decision auditable.'),
    'chapter13': (
        '> **本章配套实验**：第27章 27.5 节的 FabGraph 双图谱平台（`demos/experiments/FabGraph_MVP`）是"数据即服务"转型的技术底座演示——Schema/Lineage 双图谱驱动元数据治理与语义检索，可体验从自然语言提问到图谱推荐 JOIN 路径再生成 SQL 的完整链路。',
        '> **本章配套實驗**：第27章 27.5 節的 FabGraph 雙圖譜平台（`demos/experiments/FabGraph_MVP`）是「資料即服務」轉型的技術底座演示——Schema/Lineage 雙圖譜驅動中繼資料治理與語義檢索，可體驗從自然語言提問到圖譜推薦 JOIN 路徑再生成 SQL 的完整鏈路。',
        '> **Hands-on experiment for this chapter**: The FabGraph dual-graph platform in Section 27.5 of Chapter 27 (`demos/experiments/FabGraph_MVP`) demonstrates the technical foundation of the "data as a service" transformation — Schema/Lineage dual graphs driving metadata governance and semantic retrieval, letting you experience the full chain from natural-language question to graph-recommended JOIN paths to generated SQL.'),
    'chapter14': (
        '> **本章配套实验**：两个实验与本章呼应——第27章 27.4 节的晶圆厂 Ontology MVP（`demos/experiments/wafer_ontology_mvp`）演示知识图谱辅助根因分析的完整工程形态；27.5 节的 FabGraph（`demos/experiments/FabGraph_MVP`）则展示符号化元数据治理如何支撑语义检索与 NL2SQL。',
        '> **本章配套實驗**：兩個實驗與本章呼應——第27章 27.4 節的晶圓廠 Ontology MVP（`demos/experiments/wafer_ontology_mvp`）演示知識圖譜輔助根因分析的完整工程形態；27.5 節的 FabGraph（`demos/experiments/FabGraph_MVP`）則展示符號化中繼資料治理如何支撐語義檢索與 NL2SQL。',
        '> **Hands-on experiments for this chapter**: Two experiments echo this chapter — the Wafer Fab Ontology MVP in Section 27.4 of Chapter 27 (`demos/experiments/wafer_ontology_mvp`) demonstrates the complete engineering form of knowledge-graph-assisted root cause analysis; FabGraph in Section 27.5 (`demos/experiments/FabGraph_MVP`) shows how symbolic metadata governance supports semantic retrieval and NL2SQL.'),
    'chapter15': (
        '> **本章配套实验**：第27章 27.8 节的 LoRA 微调实验（`demos/experiments/fab_llm_fine_tuning`）完整走通"数据合成 → LoRA 训练 → 推理 → 量化评估"链路，用 0.5B 小模型做领域预处理辅助大模型——是本章"数据稀缺场景下的 AI 加速"在 LLM 时代的延伸。',
        '> **本章配套實驗**：第27章 27.8 節的 LoRA 微調實驗（`demos/experiments/fab_llm_fine_tuning`）完整走通「資料合成 → LoRA 訓練 → 推理 → 量化評估」鏈路，用 0.5B 小模型做領域預處理輔助大模型——是本章「資料稀缺場景下的 AI 加速」在 LLM 時代的延伸。',
        '> **Hands-on experiment for this chapter**: The LoRA fine-tuning experiment in Section 27.8 of Chapter 27 (`demos/experiments/fab_llm_fine_tuning`) walks through the full "data synthesis → LoRA training → inference → quantitative evaluation" pipeline, using a 0.5B small model for domain preprocessing to assist a large model — an LLM-era extension of this chapter\'s "AI acceleration under data scarcity" theme.'),
    'chapter17': (
        '> **本章配套实验**：两个实验分别对应本章两条融合路径——第27章 27.8 节的 LoRA 微调（`demos/experiments/fab_llm_fine_tuning`）演示连接主义方法与大模型的分工协作；27.3 节的 Ontology Text2SQL（`demos/experiments/fab_ontology_text2sql`）演示符号语义层如何约束 LLM 的生成行为。',
        '> **本章配套實驗**：兩個實驗分別對應本章兩條融合路徑——第27章 27.8 節的 LoRA 微調（`demos/experiments/fab_llm_fine_tuning`）演示連接主義方法與大模型的分工協作；27.3 節的 Ontology Text2SQL（`demos/experiments/fab_ontology_text2sql`）演示符號語義層如何約束 LLM 的生成行為。',
        '> **Hands-on experiments for this chapter**: Two experiments correspond to the two fusion paths of this chapter — the LoRA fine-tuning experiment in Section 27.8 of Chapter 27 (`demos/experiments/fab_llm_fine_tuning`) demonstrates the division of labor between connectionist methods and large models; the Ontology Text2SQL experiment in Section 27.3 (`demos/experiments/fab_ontology_text2sql`) shows how a symbolic semantic layer constrains LLM generation.'),
    'chapter20': (
        '> **本章配套实验**：第27章 27.6 节的 K8s 式声明式调度（`demos/experiments/C9S_agent`）是本章 SA 融合的生动案例——符号系统定义目标与约束（声明式目标），行为系统负责持续逼近（调谐循环），还内置了与传统命令式管道的对比实验。',
        '> **本章配套實驗**：第27章 27.6 節的 K8s 式宣告式排程（`demos/experiments/C9S_agent`）是本章 SA 融合的生動案例——符號系統定義目標與約束（宣告式目標），行為系統負責持續逼近（調諧迴圈），還內建了與傳統命令式管道的對比實驗。',
        '> **Hands-on experiment for this chapter**: The K8s-style declarative scheduling experiment in Section 27.6 of Chapter 27 (`demos/experiments/C9S_agent`) is a vivid SA-fusion case of this chapter — the symbolic system defines goals and constraints (declarative targets) while the behavioral system keeps converging toward them (reconciliation loop), with a built-in comparison against the traditional imperative pipeline.'),
    'chapter21': (
        '> **本章配套实验**：第27章 27.11 节的多 Agent 评估框架（`demos/experiments/fab_agent_test`）回答了 NSA 全融合系统"如何评估"的问题——从过程质量、资源成本到故障注入下的系统韧性，为端到端智能体提供了可复用的三维评估方法。',
        '> **本章配套實驗**：第27章 27.11 節的多 Agent 評估框架（`demos/experiments/fab_agent_test`）回答了 NSA 全融合系統「如何評估」的問題——從過程品質、資源成本到故障注入下的系統韌性，為端到端智慧體提供了可複用的三維評估方法。',
        '> **Hands-on experiment for this chapter**: The multi-Agent evaluation framework in Section 27.11 of Chapter 27 (`demos/experiments/fab_agent_test`) answers the "how to evaluate" question for NSA full-fusion systems — from process quality and resource cost to resilience under injected faults, providing a reusable three-dimensional evaluation method for end-to-end agents.'),
    'chapter22': (
        '> **本章配套实验**：两个实验覆盖本章两大主题——第27章 27.10 节的红蓝对抗（`demos/experiments/wafer-trust-guard`）用四层防线验证 LLM 进厂后的可信边界；27.9 节的 RTD 实时派工（`demos/experiments/fab_ai_rtd_mvp`）演示 LLM 诊断建议如何通过分级审批赢得产线信任。',
        '> **本章配套實驗**：兩個實驗涵蓋本章兩大主題——第27章 27.10 節的紅藍對抗（`demos/experiments/wafer-trust-guard`）用四層防線驗證 LLM 進廠後的可信邊界；27.9 節的 RTD 即時派工（`demos/experiments/fab_ai_rtd_mvp`）演示 LLM 診斷建議如何透過分級審批贏得產線信任。',
        '> **Hands-on experiments for this chapter**: Two experiments cover the chapter\'s two major themes — the red-blue adversarial exercise in Section 27.10 of Chapter 27 (`demos/experiments/wafer-trust-guard`) verifies the trust boundary of LLMs in the fab with a four-layer defense; the RTD real-time dispatching experiment in Section 27.9 (`demos/experiments/fab_ai_rtd_mvp`) shows how LLM diagnostic recommendations earn production-line trust through tiered approval.'),
    'chapter23': (
        '> **本章配套实验**：两个实验补全 Agent 系统的"验证"环节——第27章 27.11 节的评估框架（`demos/experiments/fab_agent_test`）提供质量/成本/韧性三维评估方法；27.10 节的红蓝对抗（`demos/experiments/wafer-trust-guard`）演示上线前的对抗式信任演练。',
        '> **本章配套實驗**：兩個實驗補全 Agent 系統的「驗證」環節——第27章 27.11 節的評估框架（`demos/experiments/fab_agent_test`）提供品質/成本/韌性三維評估方法；27.10 節的紅藍對抗（`demos/experiments/wafer-trust-guard`）演示上線前的對抗式信任演練。',
        '> **Hands-on experiments for this chapter**: Two experiments complete the "verification" side of Agent systems — the evaluation framework in Section 27.11 of Chapter 27 (`demos/experiments/fab_agent_test`) provides a quality/cost/resilience three-dimensional evaluation method; the red-blue adversarial exercise in Section 27.10 (`demos/experiments/wafer-trust-guard`) demonstrates pre-launch adversarial trust drills.'),
    'chapter24': (
        '> **本章配套实验**：两个实验把本章的本体思想变成可运行的代码——第27章 27.3 节的 Ontology Text2SQL（`demos/experiments/fab_ontology_text2sql`）用三段式架构演示"本体作为受控语义层"；27.4 节的晶圆厂 Ontology MVP（`demos/experiments/wafer_ontology_mvp`）则完整实现"对象-链接-动作"三层映射驱动的根因分析 Agent。',
        '> **本章配套實驗**：兩個實驗把本章的本體思想變成可執行的程式碼——第27章 27.3 節的 Ontology Text2SQL（`demos/experiments/fab_ontology_text2sql`）用三段式架構演示「本體作為受控語義層」；27.4 節的晶圓廠 Ontology MVP（`demos/experiments/wafer_ontology_mvp`）則完整實現「物件-連結-動作」三層映射驅動的根因分析 Agent。',
        '> **Hands-on experiments for this chapter**: Two experiments turn this chapter\'s ontology thinking into runnable code — the Ontology Text2SQL experiment in Section 27.3 of Chapter 27 (`demos/experiments/fab_ontology_text2sql`) demonstrates "ontology as a controlled semantic layer" with a three-stage architecture; the Wafer Fab Ontology MVP in Section 27.4 (`demos/experiments/wafer_ontology_mvp`) fully implements an RCA Agent driven by the object-link-action three-layer mapping.'),
    'chapter25': (
        '> **本章配套实验**：第27章提供了本章方法论的两个可运行参照——27.3 节的 Ontology Text2SQL（`demos/experiments/fab_ontology_text2sql`）展示本体语义层如何约束查询生成，是"增量式构建"最小可行起点；27.4 节的晶圆厂 Ontology MVP（`demos/experiments/wafer_ontology_mvp`）展示本体图如何支撑 GraphRAG 推理。',
        '> **本章配套實驗**：第27章提供了本章方法論的兩個可執行參照——27.3 節的 Ontology Text2SQL（`demos/experiments/fab_ontology_text2sql`）展示本體語義層如何約束查詢生成，是「增量式構建」最小可行起點；27.4 節的晶圓廠 Ontology MVP（`demos/experiments/wafer_ontology_mvp`）展示本體圖如何支撐 GraphRAG 推理。',
        '> **Hands-on experiments for this chapter**: Chapter 27 offers two runnable references for this chapter\'s methodology — the Ontology Text2SQL experiment in Section 27.3 (`demos/experiments/fab_ontology_text2sql`) shows how an ontology semantic layer constrains query generation, serving as the minimal viable starting point for incremental construction; the Wafer Fab Ontology MVP in Section 27.4 (`demos/experiments/wafer_ontology_mvp`) shows how an ontology graph supports GraphRAG reasoning.'),
}

def find_chapter(lang, chname):
    base = os.path.join(ROOT, lang, 'chapters')
    for dp, dn, fns in os.walk(base):
        for fn in fns:
            if fn == chname + '.md':
                return os.path.join(dp, fn)
    return None

langs = {'zh-CN': 0, 'zh-TW': 1, 'en': 2}
applied, failed = 0, []
for lang, idx in langs.items():
    for ch, texts in sorted(GUIDES.items()):
        p = find_chapter(lang, ch)
        if not p:
            failed.append('%s/%s (not found)' % (lang, ch))
            continue
        t = io.open(p, encoding='utf-8', newline='').read()
        if 'demos/experiments/' in t:
            failed.append('%s/%s (already has experiment guide)' % (lang, ch))
            continue
        nl = '\r\n' if '\r\n' in t else '\n'
        guide = texts[idx]
        t = t.rstrip() + nl * 2 + guide + nl
        io.open(p, 'w', encoding='utf-8', newline='').write(t)
        applied += 1

print('Applied: %d guides' % applied)
if failed:
    print('Issues:', failed)
