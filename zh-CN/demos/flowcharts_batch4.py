"""
part3b 流程图生成脚本
第9章 良率爬坡方法论流程 + 第10章 产能爬坡流程
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def draw_flowbox(ax, x, y, w, h, text, color='#2196F3', text_color='white', fontsize=9):
    box = mpatches.FancyBboxPatch((x - w/2, y - h/2), w, h,
                                   boxstyle="round,pad=0.15",
                                   facecolor=color, edgecolor=color, alpha=0.9, linewidth=2)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight='bold', color=text_color, wrap=True)
    return (x, y, w, h)

def draw_arrow(ax, x1, y1, x2, y2, color='#666'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.8))

# ============================================================
# 1. Ch9: 良率爬坡方法论流程
# ============================================================
fig, ax = plt.subplots(figsize=(16, 5))
ax.set_xlim(0, 16)
ax.set_ylim(0, 5)
ax.axis('off')

stages = [
    (1.6, 2.5, '缺陷检测\n(扫描/量测)', '#2196F3'),
    (4.6, 2.5, '根因分析 RCA\n(5W1H/知识图谱)', '#FF9800'),
    (7.6, 2.5, '工艺窗口量化\n(DOE/PWI/Cpk)', '#4CAF50'),
    (10.6, 2.5, '良率模型预测\n(统计模型/ML)', '#F44336'),
    (13.6, 2.5, 'DTCO\n(设计-工艺协同)', '#9C27B0'),
]
for x, y, text, color in stages:
    draw_flowbox(ax, x, y, 2.4, 1.5, text, color=color, fontsize=9)
for i in range(len(stages)-1):
    draw_arrow(ax, stages[i][0]+1.2, 2.5, stages[i+1][0]-1.2, 2.5)

# 学习循环反馈箭头
draw_arrow(ax, 14.8, 1.6, 1.6, 1.6, color='#999')
draw_arrow(ax, 1.6, 1.6, 1.6, 1.75, color='#999')
ax.text(8.2, 1.1, '学习循环: 实验 → 分析 → 改进 (每周迭代)', ha='center',
        fontsize=10, color='#555', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

ax.set_title('第9章: 良率爬坡四大方法论支柱', fontsize=14, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch9_yield_ramp_flow.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Flow Ch9 Yield Ramp saved.')

# ============================================================
# 2. Ch10: 产能爬坡流程
# ============================================================
fig, ax = plt.subplots(figsize=(16, 5))
ax.set_xlim(0, 16)
ax.set_ylim(0, 5)
ax.axis('off')

stages = [
    (1.6, 2.5, '设备到位\n(IAT安装验收)', '#2196F3'),
    (4.6, 2.5, '通线验证\n(PQ/PV/机台匹配)', '#FF9800'),
    (7.6, 2.5, '分阶段放行\n(验证晶圆→量产)', '#4CAF50'),
    (10.6, 2.5, '排程/物流/PM优化\n(动态调度/AMHS)', '#F44336'),
    (13.6, 2.5, '满产运营\n(产能利用率≥90%)', '#9C27B0'),
]
for x, y, text, color in stages:
    draw_flowbox(ax, x, y, 2.4, 1.5, text, color=color, fontsize=9)
for i in range(len(stages)-1):
    draw_arrow(ax, stages[i][0]+1.2, 2.5, stages[i+1][0]-1.2, 2.5)

# 瓶颈转移反馈
draw_arrow(ax, 14.8, 1.6, 1.6, 1.6, color='#999')
draw_arrow(ax, 1.6, 1.6, 1.6, 1.75, color='#999')
ax.text(8.2, 1.1, '瓶颈转移循环: 识别瓶颈 → 缓解 → 追踪下一个瓶颈', ha='center',
        fontsize=10, color='#555', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

ax.set_title('第10章: 产能爬坡流程与瓶颈管理', fontsize=14, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch10_capacity_ramp_flow.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Flow Ch10 Capacity Ramp saved.')
