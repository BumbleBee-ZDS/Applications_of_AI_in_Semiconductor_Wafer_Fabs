"""
第26章 流程图: 具身智能 Agent 三层架构(认知层 Ontology → 决策层 LLM/VLA → 行动层 机器人)
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

def draw_arrow(ax, x1, y1, x2, y2, color='#666', label=None, lx=0, ly=0):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.8))
    if label:
        ax.text((x1+x2)/2 + lx, (y1+y2)/2 + ly, label, ha='center', fontsize=8.5, color='#555')

fig, ax = plt.subplots(figsize=(13, 6.5))
ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')

# 三层架构
draw_flowbox(ax, 6, 6.5, 9.5, 1.7, '认知层: Ontology 世界模型\n(设备/材料/工艺/空间的语义建模)', '#283593', fontsize=10)
draw_flowbox(ax, 6, 4.2, 9.5, 1.7, '决策层: LLM / VLA + 任务规划\n(自然语言指令 → 行动序列)', '#1565C0', fontsize=10)
draw_flowbox(ax, 6, 1.9, 9.5, 1.7, '行动层: 机械臂 / AGV / 天车 / 巡检机器人\n(执行物理动作并反馈)', '#00838F', fontsize=10)

# 箭头
draw_arrow(ax, 6, 5.6, 6, 5.1, label='语义查询/规则校验')
draw_arrow(ax, 6, 3.4, 6, 2.9, label='行动指令')
draw_arrow(ax, 6, 1.0, 6, 1.3, color='#999')
draw_arrow(ax, 3.5, 1.0, 3.5, 5.6, color='#999')
draw_arrow(ax, 3.5, 5.6, 4.8, 6.5, color='#999')
ax.text(2.2, 3.3, '感知反馈\n(状态/异常)', fontsize=9, color='#777', rotation=90)

# 右侧说明
ax.text(9.6, 7.4, '可验证: 对照规则校验行动计划', fontsize=9, color='#283593', fontweight='bold')
ax.text(9.6, 5.1, '可编排: 调用 Ontology 对象与动作', fontsize=9, color='#1565C0', fontweight='bold')
ax.text(9.6, 2.8, '执行端: 物理世界闭环', fontsize=9, color='#00838F', fontweight='bold')

ax.set_title('第26章: 具身智能 Agent 三层架构（Ontology × LLM/VLA × 机器人）', fontsize=13, fontweight='bold', pad=12)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch26_embodied_ai_flow.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Flow Ch26 Embodied AI saved.')
