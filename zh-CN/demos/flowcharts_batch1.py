"""
流程图批次1: Ch1-5 基石篇 + 三大学派技术演进
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def box(ax, x, y, w, h, text, color='#2196F3', fs=9):
    b = mpatches.FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.12",
        facecolor=color, edgecolor=color, alpha=0.9, linewidth=2)
    ax.add_patch(b)
    ax.text(x, y, text, ha='center', va='center', fontsize=fs, fontweight='bold', color='white')

def arrow(ax, x1, y1, x2, y2, color='#666'):
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
        arrowprops=dict(arrowstyle='->', color=color, lw=1.8))

def diamond(ax, x, y, w, h, text, color='#FF9800', fs=8):
    d = mpatches.FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.05",
        facecolor=color, edgecolor=color, alpha=0.85, linewidth=2)
    ax.add_patch(d)
    ax.text(x, y, text, ha='center', va='center', fontsize=fs, fontweight='bold', color='white')


# === Ch1: AI在晶圆厂的价值定位 ===
fig, ax = plt.subplots(figsize=(14, 6))
ax.set_xlim(0, 14); ax.set_ylim(0, 6); ax.axis('off')
box(ax, 2, 5, 3, 0.8, '晶圆厂困境\n复杂性爆炸', '#F44336', 10)
box(ax, 2, 3.5, 3, 0.8, '摩尔定律放缓\n良率提升成本递增', '#FF5722', 9)
box(ax, 2, 2, 3, 0.8, '人力经验天花板\n资深工程师退休', '#FF9800', 9)
arrow(ax, 2, 4.6, 2, 3.9, '#F44336')
arrow(ax, 2, 3.1, 2, 2.4, '#FF5722')
box(ax, 7, 3.5, 3, 1.2, 'AI价值定位\n\n降本 | 增效 | 经验数字化', '#2196F3', 10)
arrow(ax, 3.5, 2, 5.5, 3.2, '#FF9800')
arrow(ax, 3.5, 3.5, 5.5, 3.5, '#FF5722')
arrow(ax, 3.5, 5, 5.5, 3.8, '#F44336')
box(ax, 11.5, 5, 3, 0.7, '降本\n减少闲置与报废', '#4CAF50', 9)
box(ax, 11.5, 3.5, 3, 0.7, '增效\n缩短开发周期', '#4CAF50', 9)
box(ax, 11.5, 2, 3, 0.7, '经验数字化\n隐性知识转模型', '#4CAF50', 9)
arrow(ax, 8.5, 3.8, 10, 4.8, '#2196F3')
arrow(ax, 8.5, 3.5, 10, 3.5, '#2196F3')
arrow(ax, 8.5, 3.2, 10, 2.2, '#2196F3')
ax.set_title('第1章：AI在晶圆厂的价值定位', fontsize=14, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch1_value.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch1 saved.")

# === Ch2: AI三大学派演进时间线 ===
fig, ax = plt.subplots(figsize=(18, 8))
ax.set_xlim(0, 18); ax.set_ylim(0, 8); ax.axis('off')
# 三条平行时间线
streams = [
    (6.5, '符号主义', '#2196F3', [
        (1, '1956\nDartmouth'), (4, '1960s\nGPS'), (7, '1970s\nMYCIN'),
        (10, '1980s\n专家系统'), (13, '2000s\n知识图谱'), (16, '2020s\n神经符号')
    ]),
    (4, '连接主义', '#4CAF50', [
        (1, '1943\nM-P模型'), (4, '1958\n感知机'), (7, '1969\nXOR批判'),
        (10, '1986\n反向传播'), (13, '2012\nAlexNet'), (16, '2017+\nTransformer')
    ]),
    (1.5, '行为主义', '#FF9800', [
        (1, '1948\n控制论'), (4, '1950s\nSkinner'), (7, '1989\nQ-Learning'),
        (10, '2013\nDQN'), (13, '2016\nAlphaGo'), (16, '2020s\nRLHF')
    ]),
]
for y, name, color, events in streams:
    ax.plot([0.5, 17], [y, y], color=color, linewidth=3, alpha=0.6)
    ax.text(0.2, y, name, fontsize=11, fontweight='bold', color=color, ha='right')
    for x, label in events:
        ax.plot(x, y, 'o', color=color, markersize=8, zorder=5)
        y_offset = 0.8 if y == 6.5 else (-0.8 if y == 1.5 else 0.8)
        ax.text(x, y + y_offset, label, fontsize=7, ha='center', color=color, fontweight='bold')
# 融合箭头
arrow(ax, 17, 6.5, 17.5, 4, '#9C27B0')
arrow(ax, 17, 4, 17.5, 4, '#9C27B0')
arrow(ax, 17, 1.5, 17.5, 4, '#9C27B0')
box(ax, 17.5, 4, 0.8, 1.5, '融\n合', '#9C27B0', 9)
ax.set_title('第2章：AI三大学派70年演进时间线——从分立到融合', fontsize=14, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch2_timeline.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch2 saved.")

# === Ch3: 符号主义技术演进 ===
fig, ax = plt.subplots(figsize=(14, 5))
ax.set_xlim(0, 14); ax.set_ylim(0, 5); ax.axis('off')
stages = [
    (1.8, '逻辑推理\nLogic Theorist\nGPS\n(1956-60s)', '#1565C0'),
    (4.8, '专家系统\nMYCIN\nDENDRAL\n(1970s)', '#1976D2'),
    (7.8, '知识表示\nOWL/RDF\n本体论\n(1990s-2000s)', '#1E88E5'),
    (10.8, '知识图谱\nGoogle KG\nNeo4j\n(2010s)', '#42A5F5'),
    (13.2, '神经符号\nLLM+KG\nRAG/CoT\n(2020s)', '#64B5F6'),
]
for x, text, color in stages:
    box(ax, x, 3, 2.2, 1.4, text, color=color, fs=8)
for i in range(len(stages)-1):
    arrow(ax, stages[i][0]+1.1, 3, stages[i+1][0]-1.1, 3, '#666')
# 底部特征
features = ['手工编码规则', '领域知识库', '标准语义', '大规模实体关系', '学习+推理融合']
for i, (x, _, _) in enumerate(stages):
    ax.text(x, 1.2, features[i], ha='center', fontsize=8, color='#666',
        bbox=dict(boxstyle='round', facecolor='#F5F5F5', alpha=0.8))
ax.set_title('第3章：符号主义技术演进——从逻辑推理到神经符号', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch3_symbolism.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch3 saved.")

# === Ch4: 连接主义技术演进 ===
fig, ax = plt.subplots(figsize=(14, 5))
ax.set_xlim(0, 14); ax.set_ylim(0, 5); ax.axis('off')
stages = [
    (1.8, 'M-P模型\n神经元\n(1943)', '#1B5E20'),
    (4.8, '感知机\nRosenblatt\n(1958)', '#2E7D32'),
    (7.8, '反向传播\nBP算法\n(1986)', '#388E3C'),
    (10.8, '深度学习\nAlexNet\n(2012)', '#43A047'),
    (13.2, '大模型\nTransformer\nGPT/BERT\n(2017+)', '#66BB6A'),
]
for x, text, color in stages:
    box(ax, x, 3, 2.2, 1.4, text, color=color, fs=8)
for i in range(len(stages)-1):
    arrow(ax, stages[i][0]+1.1, 3, stages[i+1][0]-1.1, 3, '#666')
features = ['数学模型', '学习算法', '梯度下降', '卷积/ReLU', '注意力机制']
for i, (x, _, _) in enumerate(stages):
    ax.text(x, 1.2, features[i], ha='center', fontsize=8, color='#666',
        bbox=dict(boxstyle='round', facecolor='#F5F5F5', alpha=0.8))
ax.set_title('第4章：连接主义技术演进——从感知机到大模型', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch4_connectionism.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch4 saved.")

# === Ch5: 行为主义技术演进 ===
fig, ax = plt.subplots(figsize=(14, 5))
ax.set_xlim(0, 14); ax.set_ylim(0, 5); ax.axis('off')
stages = [
    (1.8, '控制论\nWiener\n(1948)', '#E65100'),
    (4.8, '强化学习\nQ-Learning\n(1989)', '#EF6C00'),
    (7.8, '深度RL\nDQN\n(2013)', '#F57C00'),
    (10.8, 'AlphaGo\nAlphaZero\n(2016-18)', '#FB8C00'),
    (13.2, 'RLHF\nPPO\n多智能体\n(2020s)', '#FFA726'),
]
for x, text, color in stages:
    box(ax, x, 3, 2.2, 1.4, text, color=color, fs=8)
for i in range(len(stages)-1):
    arrow(ax, stages[i][0]+1.1, 3, stages[i+1][0]-1.1, 3, '#666')
features = ['反馈控制', '时序差分', '神经网络+RL', '自我博弈', '人类反馈对齐']
for i, (x, _, _) in enumerate(stages):
    ax.text(x, 1.2, features[i], ha='center', fontsize=8, color='#666',
        bbox=dict(boxstyle='round', facecolor='#F5F5F5', alpha=0.8))
ax.set_title('第5章：行为主义技术演进——从控制论到RLHF', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch5_behaviorism.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch5 saved.")

print("\n=== Batch 1 flowcharts done ===")
