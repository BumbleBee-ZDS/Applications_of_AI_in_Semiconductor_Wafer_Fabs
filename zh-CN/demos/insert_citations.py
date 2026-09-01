# -*- coding: utf-8 -*-
"""为三语书稿正文插入新增参考文献引用标记 [78]-[102]"""
import io, sys

ROOT = r'H:\code\traework\AI在半导体晶圆厂的应用'
def P(lang, part, ch):
    return ROOT + '\\' + lang + '\\chapters\\' + part + '\\' + ch

# (file, old, new) — 每组三语
OPS = []

# ---------- 第5章 [101][102] ----------
ops_ch5 = [
    # Decision Transformer
    ('part2/chapter05.md',
     '**决策Transformer**（Decision Transformer）：将强化学习重新表述为序列建模问题。',
     '**决策Transformer**（Decision Transformer）：将强化学习重新表述为序列建模问题[102]。'),
    ('part2/chapter05.md',
     '**Decision Transformer**: Recasting reinforcement learning as a sequence modeling problem.',
     '**Decision Transformer**: Recasting reinforcement learning as a sequence modeling problem[102].'),
    ('part2/chapter05.md',
     '**決策Transformer**（Decision Transformer）：將強化學習重新表述為序列建模問題。',
     '**決策Transformer**（Decision Transformer）：將強化學習重新表述為序列建模問題[102]。'),
    # CQL (表格行)
    ('part2/chapter05.md',
     '| Conservative Q-Learning (CQL) | 离线RL，防止对分布外动作的过估计 |',
     '| Conservative Q-Learning (CQL)[101] | 离线RL，防止对分布外动作的过估计 |'),
    ('part2/chapter05.md',
     '| Conservative Q-Learning (CQL) | Offline RL, prevents overestimation of out-of-distribution actions |',
     '| Conservative Q-Learning (CQL)[101] | Offline RL, prevents overestimation of out-of-distribution actions |'),
    ('part2/chapter05.md',
     '| Conservative Q-Learning (CQL) | 離線RL，防止對分佈外動作的過估計 |',
     '| Conservative Q-Learning (CQL)[101] | 離線RL，防止對分佈外動作的過估計 |'),
]

# ---------- 第6章 [91][92] ----------
ops_ch6 = [
    ('part3/chapter06.md',
     'SK海力士投资的AI公司Gauss Labs开发了Panoptes虚拟量测（Virtual Metrology, VM）系统，2022年12月在SK海力士量产产线部署。',
     'SK海力士投资的AI公司Gauss Labs开发了Panoptes虚拟量测（Virtual Metrology, VM）系统，2022年12月在SK海力士量产产线部署[91][92]。'),
    ('part3/chapter06.md',
     'Gauss Labs, an AI company invested in by SK Hynix, developed the Panoptes Virtual Metrology (VM) system, deployed on SK Hynix\'s mass production line in December 2022.',
     'Gauss Labs, an AI company invested in by SK Hynix, developed the Panoptes Virtual Metrology (VM) system, deployed on SK Hynix\'s mass production line in December 2022[91][92].'),
    ('part3/chapter06.md',
     'SK海力士投資的AI公司Gauss Labs開發了Panoptes虛擬量測（Virtual Metrology, VM）系統，2022年12月在SK海力士量產產線部署。',
     'SK海力士投資的AI公司Gauss Labs開發了Panoptes虛擬量測（Virtual Metrology, VM）系統，2022年12月在SK海力士量產產線部署[91][92]。'),
]

# ---------- 第7章 [87][88] ----------
ops_ch7 = [
    ('part3/chapter07.md',
     '**AISSI项目（2021-2024）**：由Bosch、Nexperia、Bosch Sensortec、D-SIMLAB、SYSTEMA和KIT联合开展，使用深度RL代理进行工厂调度。',
     '**AISSI项目（2021-2024）**：由Bosch、Nexperia、Bosch Sensortec、D-SIMLAB、SYSTEMA和KIT联合开展，使用深度RL代理进行工厂调度[87]。'),
    ('part3/chapter07.md',
     '**AISSI Project (2021–2024):** A joint project by Bosch, Nexperia, Bosch Sensortec, D-SIMLAB, SYSTEMA, and KIT, using deep RL agents for factory scheduling.',
     '**AISSI Project (2021–2024):** A joint project by Bosch, Nexperia, Bosch Sensortec, D-SIMLAB, SYSTEMA, and KIT, using deep RL agents for factory scheduling[87].'),
    ('part3/chapter07.md',
     '**AISSI專案（2021-2024）**：由Bosch、Nexperia、Bosch Sensortec、D-SIMLAB、SYSTEMA和KIT聯合開展，使用深度RL代理進行工廠排程。',
     '**AISSI專案（2021-2024）**：由Bosch、Nexperia、Bosch Sensortec、D-SIMLAB、SYSTEMA和KIT聯合開展，使用深度RL代理進行工廠排程[87]。'),
    ('part3/chapter07.md',
     '虽然RL在晶圆厂调度中的研究由来已久，但真正在产线上验证的案例正在积累：',
     '虽然RL在晶圆厂调度中的研究由来已久，但真正在产线上验证的案例正在积累[88]：'),
    ('part3/chapter07.md',
     'Although RL research in fab scheduling has a long history, cases validated on actual production lines are accumulating:',
     'Although RL research in fab scheduling has a long history, cases validated on actual production lines are accumulating[88]:'),
    ('part3/chapter07.md',
     '雖然RL在晶圓廠排程中的研究由來已久，但真正在產線上驗證的案例正在積累：',
     '雖然RL在晶圓廠排程中的研究由來已久，但真正在產線上驗證的案例正在積累[88]：'),
]

# ---------- 第8章 [95][96] ----------
ops_ch8 = [
    ('part3/chapter08.md',
     'ASML使用AI加速OPC计算已超过十年。2025年与Mistral AI合作，用生成式AI提升OPC Recipe质量和求解速度。',
     'ASML使用AI加速OPC计算已超过十年。2025年与Mistral AI合作，用生成式AI提升OPC Recipe质量和求解速度[95][96]。'),
    ('part3/chapter08.md',
     'ASML has used AI to accelerate OPC computation for over a decade. In 2025, it partnered with Mistral AI to use generative AI to improve OPC Recipe quality and solving speed.',
     'ASML has used AI to accelerate OPC computation for over a decade. In 2025, it partnered with Mistral AI to use generative AI to improve OPC Recipe quality and solving speed[95][96].'),
    ('part3/chapter08.md',
     'ASML使用AI加速OPC計算已超過十年。2025年與Mistral AI合作，用生成式AI提升OPC Recipe品質和求解速度。',
     'ASML使用AI加速OPC計算已超過十年。2025年與Mistral AI合作，用生成式AI提升OPC Recipe品質和求解速度[95][96]。'),
]

# ---------- 第9章 [78][79][80] [81][82] ----------
ops_ch9 = [
    ('part3b/chapter09.md',
     '**Murphy模型**考虑了缺陷密度的不均匀性，对Poisson模型进行修正，适用于缺陷密度在晶圆间存在波动的情况。',
     '**Murphy模型**考虑了缺陷密度的不均匀性，对Poisson模型进行修正，适用于缺陷密度在晶圆间存在波动的情况[78][79][80]。'),
    ('part3b/chapter09.md',
     '**Murphy model** accounts for non-uniformity of defect density across wafers, correcting the Poisson model for wafer-to-wafer variation.',
     '**Murphy model** accounts for non-uniformity of defect density across wafers, correcting the Poisson model for wafer-to-wafer variation[78][79][80].'),
    ('part3b/chapter09.md',
     '**Murphy模型**考慮了缺陷密度的不均勻性，對Poisson模型進行修正，適用於缺陷密度在晶圓間存在波動的情況。',
     '**Murphy模型**考慮了缺陷密度的不均勻性，對Poisson模型進行修正，適用於缺陷密度在晶圓間存在波動的情況[78][79][80]。'),
    ('part3b/chapter09.md',
     '对于复杂产品，芯片良率还受到电路密度和关键面积（Critical Area）的影响——并非芯片上所有区域都对缺陷同样敏感，只有落在关键区域（如金属线间距最小处）的缺陷才会导致失效。',
     '对于复杂产品，芯片良率还受到电路密度和关键面积（Critical Area）的影响——并非芯片上所有区域都对缺陷同样敏感，只有落在关键区域（如金属线间距最小处）的缺陷才会导致失效[81][82]。'),
    ('part3b/chapter09.md',
     'For complex products, chip yield is also affected by circuit density and critical area — not all regions of the chip are equally defect-sensitive; only defects landing in critical regions (e.g., the minimum metal-line spacing) cause failures.',
     'For complex products, chip yield is also affected by circuit density and critical area — not all regions of the chip are equally defect-sensitive; only defects landing in critical regions (e.g., the minimum metal-line spacing) cause failures[81][82].'),
    ('part3b/chapter09.md',
     '對於複雜產品，晶片良率還受到電路密度和關鍵面積（Critical Area）的影響——並非晶片上所有區域都對缺陷同樣敏感，只有落在關鍵區域（如金屬線間距最小處）的缺陷才會導致失效。',
     '對於複雜產品，晶片良率還受到電路密度和關鍵面積（Critical Area）的影響——並非晶片上所有區域都對缺陷同樣敏感，只有落在關鍵區域（如金屬線間距最小處）的缺陷才會導致失效[81][82]。'),
]

# ---------- 第16章 [83][84] [85][86] ----------
ops_ch16 = [
    ('part4/chapter16.md',
     '- 超过100次商业tape-out使用了DSO.ai',
     '- 超过100次商业tape-out使用了DSO.ai[83][84]'),
    ('part4/chapter16.md',
     '- Over 100 commercial tape-outs have used DSO.ai',
     '- Over 100 commercial tape-outs have used DSO.ai[83][84]'),
    ('part4/chapter16.md',
     '- 超過100次商業tape-out使用了DSO.ai',
     '- 超過100次商業tape-out使用了DSO.ai[83][84]'),
    ('part4/chapter16.md',
     'AlphaChip的两位核心作者（Anna Goldie和Azalia Mirhoseini）随后创立了Ricursive Intelligence，融资3亿美元（估值40亿），将RL芯片设计平台商业化——这表明RL在半导体领域的价值已被资本市场认可。',
     'AlphaChip的两位核心作者（Anna Goldie和Azalia Mirhoseini）随后创立了Ricursive Intelligence[85]，融资3亿美元（估值40亿），将RL芯片设计平台商业化——这表明RL在半导体领域的价值已被资本市场认可[86]。'),
    ('part4/chapter16.md',
     'The two core authors of AlphaChip (Anna Goldie and Azalia Mirhoseini) subsequently founded Ricursive Intelligence, raising $300 million (valuation of $4 billion), commercializing the RL chip design platform—this demonstrates that the value of RL in the semiconductor field has been recognized by capital markets.',
     'The two core authors of AlphaChip (Anna Goldie and Azalia Mirhoseini) subsequently founded Ricursive Intelligence[85], raising $300 million (valuation of $4 billion), commercializing the RL chip design platform—this demonstrates that the value of RL in the semiconductor field has been recognized by capital markets[86].'),
    ('part4/chapter16.md',
     'AlphaChip的兩位核心作者（Anna Goldie和Azalia Mirhoseini）隨後創立了Ricursive Intelligence，融資3億美元（估值40億），將RL晶片設計平台商業化——這表明RL在半導體領域的價值已被資本市場認可。',
     'AlphaChip的兩位核心作者（Anna Goldie和Azalia Mirhoseini）隨後創立了Ricursive Intelligence[85]，融資3億美元（估值40億），將RL晶片設計平台商業化——這表明RL在半導體領域的價值已被資本市場認可[86]。'),
]

# ---------- 第18章 [97][98] ----------
ops_ch18 = [
    ('part4b/chapter18.md',
     '更深层的NB融合是在模型架构层面将符号约束嵌入神经网络——在训练过程中用符号规则约束神经网络的输出空间。',
     '更深层的NB融合是在模型架构层面将符号约束嵌入神经网络——在训练过程中用符号规则约束神经网络的输出空间[97][98]。'),
    ('part4b/chapter18.md',
     'A deeper NB fusion embeds symbolic constraints into the neural network at the model architecture level—using symbolic rules during training to constrain the output space of the neural network.',
     'A deeper NB fusion embeds symbolic constraints into the neural network at the model architecture level—using symbolic rules during training to constrain the output space of the neural network[97][98].'),
    ('part4b/chapter18.md',
     '更深層的NB融合是在模型架構層面將符號約束嵌入類神經網路——在訓練過程中用符號規則約束類神經網路的輸出空間。',
     '更深層的NB融合是在模型架構層面將符號約束嵌入類神經網路——在訓練過程中用符號規則約束類神經網路的輸出空間[97][98]。'),
]

# ---------- 第20章 [89][90] Flexciton ----------
ops_ch20 = [
    ('part4b/chapter20.md',
     'Flexciton的晶圆厂调度系统体现了SA融合在MFG中的实践：',
     'Flexciton的晶圆厂调度系统体现了SA融合在MFG中的实践[89][90]：'),
    ('part4b/chapter20.md',
     'Flexciton\'s wafer fab scheduling system embodies the practice of SA fusion in MFG:',
     'Flexciton\'s wafer fab scheduling system embodies the practice of SA fusion in MFG[89][90]:'),
    ('part4b/chapter20.md',
     'Flexciton的晶圓廠排程系統體現了SA融合在MFG中的實踐：',
     'Flexciton的晶圓廠排程系統體現了SA融合在MFG中的實踐[89][90]：'),
]

# ---------- 第21章 [94] ----------
ops_ch21 = [
    ('part4b/chapter21.md',
     'Palantir与NVIDIA联合发布的AIOS-RA（AI Operating System Reference Architecture）定义了NSA全融合的工业级架构：',
     'Palantir与NVIDIA联合发布的AIOS-RA（AI Operating System Reference Architecture）定义了NSA全融合的工业级架构[94]：'),
    ('part4b/chapter21.md',
     'Palantir and NVIDIA jointly released AIOS-RA (AI Operating System Reference Architecture), defining an industrial-grade architecture for NSA full fusion:',
     'Palantir and NVIDIA jointly released AIOS-RA (AI Operating System Reference Architecture), defining an industrial-grade architecture for NSA full fusion[94]:'),
    ('part4b/chapter21.md',
     'Palantir與NVIDIA聯合釋出的AIOS-RA（AI Operating System Reference Architecture）定義了NSA全融合的工業級架構：',
     'Palantir與NVIDIA聯合釋出的AIOS-RA（AI Operating System Reference Architecture）定義了NSA全融合的工業級架構[94]：'),
]

# ---------- 第24章 [93] [94] ----------
ops_ch24 = [
    ('part6/chapter24.md',
     '而是一个"可执行的企业数字孪生"——本体不仅是数据的语义映射，还是企业运营逻辑的形式化表达。',
     '而是一个"可执行的企业数字孪生"[93]——本体不仅是数据的语义映射，还是企业运营逻辑的形式化表达。'),
    ('part6/chapter24.md',
     'but an "executable enterprise digital twin" — the ontology is not only a semantic mapping of data but a formal expression of enterprise operational logic.',
     'but an "executable enterprise digital twin"[93] — the ontology is not only a semantic mapping of data but a formal expression of enterprise operational logic.'),
    ('part6/chapter24.md',
     '而是一個"可執行的企業數字孿生"——本體不僅是資料的語義對映，還是企業營運邏輯的形式化表達。',
     '而是一個"可執行的企業數字孿生"[93]——本體不僅是資料的語義對映，還是企業營運邏輯的形式化表達。'),
    ('part6/chapter24.md',
     'Reference Architecture, AIOS-RA）。这是一个里程碑式的事件',
     'Reference Architecture, AIOS-RA）[94]。这是一个里程碑式的事件'),
    ('part6/chapter24.md',
     'Reference Architecture** (AIOS-RA). This was a milestone event',
     'Reference Architecture** (AIOS-RA)[94]. This was a milestone event'),
    ('part6/chapter24.md',
     'Reference Architecture, AIOS-RA）。這是一個里程碑式的事件',
     'Reference Architecture, AIOS-RA）[94]。這是一個里程碑式的事件'),
]

# ---------- 第26章 [99] [100] ----------
ops_ch26 = [
    ('part6/chapter26.md',
     'VLA 让机器人的操作从"为每个任务编写程序"走向"用自然语言指挥通用操作"。',
     'VLA 让机器人的操作从"为每个任务编写程序"走向"用自然语言指挥通用操作"[99]。'),
    ('part6/chapter26.md',
     'VLA moves robot operation from "writing a program for every task" toward "commanding general operations in natural language."',
     'VLA moves robot operation from "writing a program for every task" toward "commanding general operations in natural language"[99].'),
    ('part6/chapter26.md',
     'VLA 讓機器人的操作從「為每個任務編寫程式」走向「用自然語言指揮通用操作」。',
     'VLA 讓機器人的操作從「為每個任務編寫程式」走向「用自然語言指揮通用操作」[99]。'),
    ('part6/chapter26.md',
     '在数字孪生环境中训练和验证机器人操作策略，再部署到物理设备（呼应第21章世界模型与数字孪生）',
     '在数字孪生环境中训练和验证机器人操作策略，再部署到物理设备（呼应第21章世界模型与数字孪生）[100]'),
    ('part6/chapter26.md',
     'training and validating robot operation policies in digital-twin environments before deploying to physical equipment (echoing the world models and digital twins of Chapter 21)',
     'training and validating robot operation policies in digital-twin environments before deploying to physical equipment (echoing the world models and digital twins of Chapter 21)[100]'),
    ('part6/chapter26.md',
     '在數位孿生環境中訓練和驗證機器人操作策略，再部署到物理設備（呼應第21章世界模型與數位孿生）',
     '在數位孿生環境中訓練和驗證機器人操作策略，再部署到物理設備（呼應第21章世界模型與數位孿生）[100]'),
]

# 组织为任务列表：每个 group 的 ops 内已按 [zh-CN, en, zh-TW] 顺序，relpath 含 part 目录
LANGS = ['zh-CN', 'en', 'zh-TW']
groups = [ops_ch5, ops_ch6, ops_ch7, ops_ch8, ops_ch9, ops_ch16,
          ops_ch18, ops_ch20, ops_ch21, ops_ch24, ops_ch26]

def build_tasks():
    tasks = []
    all_ops = (ops_ch5 + ops_ch6 + ops_ch7 + ops_ch8 + ops_ch9 + ops_ch16 +
               ops_ch18 + ops_ch20 + ops_ch21 + ops_ch24 + ops_ch26)
    # 每 3 条一组，顺序为 [zh-CN, en, zh-TW]；relpath 已含 part 目录
    for i, (relpath, old, new) in enumerate(all_ops):
        lang = LANGS[i % 3]
        path = ROOT + '\\' + lang + '\\chapters\\' + relpath.replace('/', '\\')
        tasks.append((path, old, new))
    return tasks

tasks = build_tasks()
mode = sys.argv[1] if len(sys.argv) > 1 else 'check'

errors = []
for path, old, new in tasks:
    with io.open(path, 'r', encoding='utf-8', newline='') as f:
        t = f.read()
    c = t.count(old)
    if c != 1:
        errors.append((path, old[:45], c))

if errors:
    print('=== %d ANCHORS NOT EXACTLY-1 ===' % len(errors))
    for path, frag, c in errors:
        print('count=%d | %s | %s' % (c, path.replace(ROOT + '\\', ''), frag))
    if mode != 'apply':
        sys.exit(1)
    print('ABORT: apply mode requires all anchors unique.')
    sys.exit(1)

print('All %d anchors unique. ' % len(tasks))

if mode == 'apply':
    done = {}
    for path, old, new in tasks:
        if path not in done:
            done[path] = io.open(path, 'r', encoding='utf-8', newline='').read()
        done[path] = done[path].replace(old, new)
    for path, t in done.items():
        with io.open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(t)
        print('Updated:', path.replace(ROOT + '\\', ''))
    print('Applied %d citations across %d files.' % (len(tasks), len(done)))
