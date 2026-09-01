# -*- coding: utf-8 -*-
"""为三语第24/25/26章插入补充流程图引用(7张新图)"""
import io

NL = '\r\n'
B = NL * 2

def blk(img_alt, img_file, caption):
    return '![%s](../../images/%s.png)%s%s*%s*' % (img_alt, img_file, NL, NL, caption)

jobs = [
    # ---------------- zh-CN ----------------
    (r'H:\code\traework\AI在半导体晶圆厂的应用\zh-CN\chapters\part6\chapter24.md', [
        ('**数据源层：**', blk('Palantir Foundry 五层架构', 'flow_ch24_foundry_arch',
            '图24-1：Palantir Foundry 五层架构——以本体层为核心'), 'after'),
        ('这个过程缩短到30-60分钟', blk('传统与本体的根因分析对比', 'flow_ch24_rca_comparison',
            '图24-2：晶圆良率根因分析（RCA）——传统跨系统人工查询与 Ontology 驱动自动推理对比'), 'after'),
        ('![Palantir Ontology在半导体的技术架构]', blk('Palantir 在半导体行业的三阶段演进', 'flow_ch24_evolution',
            '图24-3：从个案到范式——Palantir 在半导体行业的三阶段演进与三层价值'), 'before'),
    ]),
    (r'H:\code\traework\AI在半导体晶圆厂的应用\zh-CN\chapters\part6\chapter25.md', [
        ('### 工艺本体', blk('晶圆厂核心本体模型地图', 'flow_ch25_ontology_map',
            '图25-1：晶圆厂核心本体模型地图——产品/工艺/设备/缺陷/时间五大本体与关系链路'), 'before'),
        ('### 跨系统语义对齐', blk('Ontology 驱动的数据融合架构', 'flow_ch25_data_fusion',
            '图25-2：Ontology 驱动的数据融合——MES、FDC、SPC、YMS 经语义对齐映射到统一本体'), 'before'),
        ('### 从哪些本体开始构建', blk('晶圆厂本体实施四阶段路径', 'flow_ch25_build_roadmap',
            '图25-3：晶圆厂 Ontology 实施四阶段路径——增量式构建，从最高价值场景出发'), 'before'),
    ]),
    (r'H:\code\traework\AI在半导体晶圆厂的应用\zh-CN\chapters\part6\chapter26.md', [
        ('- **异常处理**：遇到障碍物或异常时自主判断并上报', blk('AMHS 天车与 AGV 智能搬运闭环', 'flow_ch26_amhs_transport',
            '图26-6：AMHS 天车与 AGV 智能搬运闭环——动态路径规划、自主异常处理与反馈闭环'), 'after'),
    ]),
    # ---------------- zh-TW ----------------
    (r'H:\code\traework\AI在半导体晶圆廠的应用\zh-TW\chapters\part6\chapter24.md', []),  # placeholder replaced below
]
jobs[3] = (r'H:\code\traework\AI在半导体晶圆厂的应用\zh-TW\chapters\part6\chapter24.md', [
    ('**資料源層：**', blk('Palantir Foundry 五層架構', 'flow_ch24_foundry_arch',
        '圖24-1：Palantir Foundry 五層架構——以本體層為核心'), 'after'),
    ('這個過程縮短到30-60分鐘', blk('傳統與本體驅動的根因分析對比', 'flow_ch24_rca_comparison',
        '圖24-2：晶圓良率根因分析（RCA）——傳統跨系統人工查詢與本體驅動自動推理對比'), 'after'),
    ('![Palantir Ontology在半導體的技術架構]', blk('Palantir 在半導體行業的三階段演進', 'flow_ch24_evolution',
        '圖24-3：從個案到範式——Palantir 在半導體行業的三階段演進與三層價值'), 'before'),
])
jobs.append((r'H:\code\traework\AI在半导体晶圆厂的应用\zh-TW\chapters\part6\chapter25.md', [
    ('### 製程本體', blk('晶圓廠核心本體模型地圖', 'flow_ch25_ontology_map',
        '圖25-1：晶圓廠核心本體模型地圖——產品/製程/設備/缺陷/時間五大本體與關係鏈路'), 'before'),
    ('### 跨系統語義對齊', blk('本體驅動的資料融合架構', 'flow_ch25_data_fusion',
        '圖25-2：本體驅動的資料融合——MES、FDC、SPC、YMS 經語義對齊映射到統一本體'), 'before'),
    ('### 從哪些本體開始構建', blk('晶圓廠本體實施四階段路徑', 'flow_ch25_build_roadmap',
        '圖25-3：晶圓廠本體實施四階段路徑——增量式構建，從最高價值場景出發'), 'before'),
]))
jobs.append((r'H:\code\traework\AI在半导体晶圆厂的应用\zh-TW\chapters\part6\chapter26.md', [
    ('- **異常處理**：遇到障礙物或異常時自主判斷並上報', blk('AMHS 天車與 AGV 智慧搬運閉環', 'flow_ch26_amhs_transport',
        '圖26-6：AMHS 天車與 AGV 智慧搬運閉環——動態路徑規劃、自主異常處理與回饋閉環'), 'after'),
]))
# ---------------- en ----------------
jobs.append((r'H:\code\traework\AI在半导体晶圆厂的应用\en\chapters\part6\chapter24.md', [
    ('**Ontology layer', blk('The five-layer architecture of Palantir Foundry', 'flow_ch24_foundry_arch',
        'Figure 24-1: The five-layer architecture of Palantir Foundry — the Ontology layer as the core'), 'before'),
    ('This process was reduced to 30-60 minutes', blk('Traditional vs. Ontology-driven root cause analysis', 'flow_ch24_rca_comparison',
        'Figure 24-2: Wafer-yield root cause analysis (RCA) — traditional cross-system manual querying vs. Ontology-driven automated reasoning'), 'after'),
    ('![Palantir Ontology Technical Architecture in Semiconductors]', blk('Three-phase evolution of Palantir in the semiconductor industry', 'flow_ch24_evolution',
        'Figure 24-3: From individual cases to paradigm — the three-phase evolution of Palantir in the semiconductor industry and its three value levels'), 'before'),
]))
jobs.append((r'H:\code\traework\AI在半导体晶圆厂的应用\en\chapters\part6\chapter25.md', [
    ('### Process Ontology', blk('Wafer-fab core ontology model map', 'flow_ch25_ontology_map',
        'Figure 25-1: Wafer-fab core ontology model map — the five ontologies (product/process/equipment/defect/time) and their relation links'), 'before'),
    ('### Cross-System Semantic Alignment', blk('Ontology-driven data fusion architecture', 'flow_ch25_data_fusion',
        'Figure 25-2: Ontology-driven data fusion — mapping MES, FDC, SPC, and YMS into a unified ontology through semantic alignment'), 'before'),
    ('### Where to Start Building the Ontology', blk('Four-phase roadmap for building wafer-fab Ontology', 'flow_ch25_build_roadmap',
        'Figure 25-3: Four-phase roadmap for building wafer-fab Ontology — incremental construction starting from the highest-value scenario'), 'before'),
]))
jobs.append((r'H:\code\traework\AI在半导体晶圆厂的应用\en\chapters\part6\chapter26.md', [
    ('- **Exception handling**: autonomously judging and reporting when obstacles or anomalies occur', blk('The intelligent-transport closed loop of AMHS overhead hoists and AGVs', 'flow_ch26_amhs_transport',
        'Figure 26-6: The intelligent-transport closed loop of AMHS overhead hoists and AGVs — dynamic path planning, autonomous anomaly handling, and feedback loop'), 'after'),
]))

for path, ops in jobs:
    if not ops:
        continue
    with io.open(path, 'r', encoding='utf-8', newline='') as f:
        text = f.read()
    for anchor, block, mode in ops:
        assert text.count(anchor) == 1, 'anchor not unique (%d): %s in %s' % (text.count(anchor), anchor[:40], path)
    lines = text.split(NL)
    out = []
    for line in lines:
        pending_after = None
        for anchor, block, mode in ops:
            if anchor in line:
                if mode == 'before':
                    out.append(block)
                    out.append('')
                pending_after = block if mode == 'after' else None
        out.append(line)
        if pending_after:
            out.append('')
            out.append(pending_after)
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(NL.join(out))
    print('Updated:', path)
print('All done.')
