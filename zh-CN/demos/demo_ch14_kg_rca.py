"""
第14章 Demo: 基于知识图谱的良率根因分析
模拟符号主义在PID/YED中的应用
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
from matplotlib.gridspec import GridSpec

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

fig = plt.figure(figsize=(18, 12))
gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)

# 左上：知识图谱可视化
ax1 = fig.add_subplot(gs[0, 0])
G = nx.DiGraph()

nodes = {
    '良率下降\n(85%)': {'pos': (0.5, 1.0), 'color': '#F44336', 'size': 2000, 'type': 'problem'},
    '边缘环形\n缺陷': {'pos': (0.5, 0.75), 'color': '#FF9800', 'size': 1500, 'type': 'defect'},
    'Step 23\n光刻': {'pos': (0.15, 0.5), 'color': '#2196F3', 'size': 1200, 'type': 'process'},
    'Step 47\n刻蚀': {'pos': (0.5, 0.5), 'color': '#2196F3', 'size': 1200, 'type': 'process'},
    'Step 89\nCMP': {'pos': (0.85, 0.5), 'color': '#2196F3', 'size': 1200, 'type': 'process'},
    'Tool-A03\n套刻精度3.2σ': {'pos': (0.15, 0.2), 'color': '#4CAF50', 'size': 1000, 'type': 'root_cause'},
    '腔体压力\n漂移0.15mTorr': {'pos': (0.5, 0.2), 'color': '#9E9E9E', 'size': 900, 'type': 'minor'},
    '抛光量\n正常': {'pos': (0.85, 0.2), 'color': '#9E9E9E', 'size': 900, 'type': 'normal'},
}

for node, attr in nodes.items():
    G.add_node(node, **attr)

edges = [
    ('良率下降\n(85%)', '边缘环形\n缺陷', {'weight': 0.95, 'color': '#F44336'}),
    ('边缘环形\n缺陷', 'Step 23\n光刻', {'weight': 0.82, 'color': '#FF9800'}),
    ('边缘环形\n缺陷', 'Step 47\n刻蚀', {'weight': 0.45, 'color': '#BDBDBD'}),
    ('边缘环形\n缺陷', 'Step 89\nCMP', {'weight': 0.12, 'color': '#E0E0E0'}),
    ('Step 23\n光刻', 'Tool-A03\n套刻精度3.2σ', {'weight': 0.88, 'color': '#4CAF50'}),
    ('Step 47\n刻蚀', '腔体压力\n漂移0.15mTorr', {'weight': 0.30, 'color': '#BDBDBD'}),
    ('Step 89\nCMP', '抛光量\n正常', {'weight': 0.05, 'color': '#E0E0E0'}),
]

for u, v, attr in edges:
    G.add_edge(u, v, **attr)

pos = {n: nodes[n]['pos'] for n in G.nodes()}

for u, v, attr in G.edges(data=True):
    width = attr['weight'] * 4
    alpha = max(0.3, attr['weight'])
    nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], width=width, 
                          edge_color=attr['color'], alpha=alpha, arrows=True, 
                          arrowsize=20, ax=ax1, connectionstyle="arc3,rad=0.1")

for node, attr in nodes.items():
    nx.draw_networkx_nodes(G, pos, nodelist=[node], node_color=attr['color'],
                          node_size=attr['size'], alpha=0.85, ax=ax1, node_shape='o')

labels = {n: n for n in G.nodes()}
nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold', ax=ax1, font_color='white')

ax1.set_title('良率根因分析知识图谱', fontsize=13, fontweight='bold')
ax1.set_xlim(-0.1, 1.1)
ax1.set_ylim(0, 1.15)
ax1.axis('off')

legend_elements = [
    mpatches.Patch(color='#F44336', label='问题（良率异常）'),
    mpatches.Patch(color='#FF9800', label='缺陷模式'),
    mpatches.Patch(color='#2196F3', label='工艺步骤'),
    mpatches.Patch(color='#4CAF50', label='已确认根因'),
    mpatches.Patch(color='#9E9E9E', label='已排除因素'),
]
ax1.legend(handles=legend_elements, loc='lower right', fontsize=8)

# 右上：规则引擎推理链
ax2 = fig.add_subplot(gs[0, 1])
rules = [
    ('规则R1', 'IF 缺陷模式=边缘环形\nTHEN 候选根因∈{光刻, 刻蚀, CMP}', 0.95, '#2196F3'),
    ('规则R2', 'IF 工艺步骤SPC值 > 2σ\nTHEN 该步骤为高度可疑', 0.88, '#4CAF50'),
    ('规则R3', 'IF 同设备多批次受影响\nTHEN 根因为设备级问题', 0.92, '#FF9800'),
    ('规则R4', 'IF SPC在控制限内\nTHEN 排除该步骤', 0.15, '#9E9E9E'),
]

for i, (rule, desc, confidence, color) in enumerate(rules):
    y = 3.5 - i * 0.9
    alpha = max(0.2, confidence)
    rect = mpatches.FancyBboxPatch((0.05, y - 0.3), 0.9, 0.6, 
                                     boxstyle="round,pad=0.05", 
                                     facecolor=color, alpha=alpha, edgecolor=color, linewidth=2)
    ax2.add_patch(rect)
    ax2.text(0.5, y, f'{rule}\n{desc}\n置信度: {confidence:.0%}', 
             ha='center', va='center', fontsize=9, fontweight='bold', color='white')
    if i < len(rules) - 1:
        ax2.annotate('', xy=(0.5, y - 0.35), xytext=(0.5, y - 0.55),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=2))

ax2.set_xlim(0, 1)
ax2.set_ylim(-0.5, 4)
ax2.set_title('规则引擎推理链', fontsize=13, fontweight='bold')
ax2.axis('off')

# 左下：推理结果时间线
ax3 = fig.add_subplot(gs[1, 0])
steps = ['感知:\nCNN识别\n边缘环形缺陷', '检索:\nKG查找\n相关工艺步骤', '推理:\n规则引擎\n检查SPC', '定位:\nTool-A03\n套刻精度超标', '报告:\nLLM生成\n分析报告']
times = [0.5, 1.2, 0.8, 0.3, 1.0]
cumulative = np.cumsum(times)
colors_timeline = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0']

for i, (step, t, color) in enumerate(zip(steps, times, colors_timeline)):
    start = cumulative[i] - t
    ax3.barh(0, t, left=start, height=0.5, color=color, alpha=0.8, edgecolor='white')
    ax3.text(start + t/2, 0, step, ha='center', va='center', fontsize=8, fontweight='bold', color='white')
    if i < len(steps) - 1:
        ax3.annotate('', xy=(cumulative[i] + 0.05, 0), xytext=(cumulative[i] - 0.05, 0),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))

ax3.set_xlim(0, sum(times) + 1)
ax3.set_ylim(-0.5, 0.5)
ax3.set_xlabel('时间 (秒)', fontsize=11)
ax3.set_title('根因分析推理时间线（总计3.8秒）', fontsize=13, fontweight='bold')
ax3.set_yticks([])
ax3.grid(axis='x', alpha=0.3)

# 右下：传统方法 vs KG方法对比
ax4 = fig.add_subplot(gs[1, 1])
methods = ['人工分析\n(传统)', '专家系统\n(早期)', '知识图谱\n+规则引擎\n(当前)']
time_vals = [240, 45, 3.8]  # 分钟
accuracy_vals = [75, 82, 94]  # %

x = np.arange(len(methods))
w = 0.35
ax4b = ax4.twinx()
bars1 = ax4.bar(x - w/2, time_vals, w, label='分析时间(分钟)', color='#FF6B6B', alpha=0.8)
bars2 = ax4b.bar(x + w/2, accuracy_vals, w, label='准确率(%)', color='#4CAF50', alpha=0.8)

for bar, val in zip(bars1, time_vals):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3, f'{val}min', 
             ha='center', fontsize=9, fontweight='bold')
for bar, val in zip(bars2, accuracy_vals):
    ax4b.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{val}%', 
              ha='center', fontsize=9, fontweight='bold')

ax4.set_xticks(x)
ax4.set_xticklabels(methods, fontsize=10)
ax4.set_ylabel('分析时间 (分钟)', fontsize=11, color='#FF6B6B')
ax4b.set_ylabel('准确率 (%)', fontsize=11, color='#4CAF50')
ax4.set_title('根因分析方法对比', fontsize=13, fontweight='bold')
lines1, labels1 = ax4.get_legend_handles_labels()
lines2, labels2 = ax4b.get_legend_handles_labels()
ax4.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc='upper center')
ax4.grid(axis='y', alpha=0.3)

fig.suptitle('第14章 Demo：基于知识图谱的良率根因分析系统 (符号主义)', 
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch14_kg_rca.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch14 KG RCA demo saved.")
plt.close()
