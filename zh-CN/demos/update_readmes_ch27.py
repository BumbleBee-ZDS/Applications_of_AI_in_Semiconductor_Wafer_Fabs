# -*- coding: utf-8 -*-
"""更新三个 README 与三个 OUTLINE：登记第27章动手实验实验室"""
import io, os

ROOT = r'H:\code\traework\AI在半导体晶圆厂的应用'
BT = chr(96) * 3  # ```

stats = []

def upd(path, pairs):
    t = io.open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in t else '\n'
    cnt = 0
    for old, new in pairs:
        old = old.replace('\n', nl)
        new = new.replace('\n', nl)
        if old in t:
            t = t.replace(old, new, 1)
            cnt += 1
        else:
            stats.append('MISS: %s :: %s...' % (os.path.basename(path), old[:40]))
    io.open(path, 'w', encoding='utf-8', newline='').write(t)
    stats.append('%s: %d/%d applied' % (os.path.basename(os.path.dirname(path)) + '/' + os.path.basename(path), cnt, len(pairs)))

# ---------- 根 README（简体，作为全书入口） ----------
upd(os.path.join(ROOT, 'README.md'), [
    # 徽章
    ('26%20Chapters-1a237e', '27%20Chapters-1a237e'),
    # 本书数据行
    ('> **本书数据**：26 章 · 3 种语言 · 20+ Demo 脚本 · 47 张配图 · 100+ 产业案例引用',
     '> **本书数据**：27 章 · 3 种语言 · 20+ Demo 脚本 · 9 个动手实验 · 47 张配图 · 100+ 产业案例引用'),
    # 结构树：追加第七部分
    ('└── 第 26 章 具身智能的应用——当AI走进晶圆厂的物理世界\n' + BT,
     '└── 第 26 章 具身智能的应用——当AI走进晶圆厂的物理世界\n'
     '\n第七部分  动手实验实验室\n└── 第 27 章 动手实验实验室——把关键概念跑起来（9 个可运行实验）\n' + BT),
    # 运行 Demo 段落后追加运行实验段落
    ('python demo_ch23_agent_system.py     # 多智能体协同框架\n' + BT,
     'python demo_ch23_agent_system.py     # 多智能体协同框架\n' + BT + '\n'
     '### 运行动手实验（第27章）\n\n'
     '9 个可运行的完整实验项目位于 `zh-CN/demos/experiments/`，详见第27章。以依赖最轻的 Ontology Text2SQL 为例：\n'
     '\n```bash\n'
     'cd zh-CN/demos/experiments/fab_ontology_text2sql\n'
     'pip install -r requirements.txt\n'
     'streamlit run app.py\n' + BT),
    # 项目结构树
    ('│   ├── demos/      # 20+ Demo可视化脚本',
     '│   ├── demos/      # 20+ Demo可视化脚本 + 9个动手实验（experiments/）'),
    ('│   ├── chapters/   # 25章正文（Markdown）',
     '│   ├── chapters/   # 27章正文（Markdown）'),
])

# ---------- 繁体 README ----------
upd(os.path.join(ROOT, 'zh-TW', 'README.md'), [
    ('└── 第 26 章 具身智慧的應用——當AI走進晶圓廠的物理世界\n' + BT,
     '└── 第 26 章 具身智慧的應用——當AI走進晶圓廠的物理世界\n'
     '\n第七部分  動手實驗實驗室\n└── 第 27 章 動手實驗實驗室——把關鍵概念跑起來（9 個可執行實驗）\n' + BT),
])

# ---------- 英文 README ----------
upd(os.path.join(ROOT, 'en', 'README.md'), [
    ('└── Chapter 26   Applications of Embodied AI — When AI Steps into the Physical World of the Fab\n' + BT,
     '└── Chapter 26   Applications of Embodied AI — When AI Steps into the Physical World of the Fab\n'
     '\nPart 7  Hands-On Lab\n└── Chapter 27   Hands-On Lab — Running the Key Concepts (9 runnable experiments)\n' + BT),
])

print('\n'.join(stats))
