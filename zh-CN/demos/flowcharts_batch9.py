"""
第32章 世界模型 配图生成脚本(第一部分)
Part 1: 世界模型三组件 / 四层架构 / 虚拟DOE闭环
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

IMG = r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images'

def draw_flowbox(ax, x, y, w, h, text, color='#2196F3', text_color='white', fontsize=9):
    box = mpatches.FancyBboxPatch((x - w/2, y - h/2), w, h,
                                   boxstyle="round,pad=0.15",
                                   facecolor=color, edgecolor=color, alpha=0.9, linewidth=2)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight='bold', color=text_color, wrap=True)
    return (x, y, w, h)

def draw_arrow(ax, x1, y1, x2, y2, color='#666', lw=1.8):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw))

# ============================================================
# 图32-1: 世界模型三组件 (32.1.2)
# ============================================================
fig, ax = plt.subplots(figsize=(13, 4.5))
ax.set_xlim(0, 13); ax.set_ylim(0, 3.5); ax.axis('off')

draw_flowbox(ax, 2.2, 2.0, 3.0, 1.5, '感知编码器\nPerception Encoder\n(高维状态→低维表征)', '#1565C0', fontsize=9)
draw_flowbox(ax, 6.5, 2.0, 3.0, 1.5, '动力学模型\nDynamics Model\n(状态转移 s→s\')', '#E65100', fontsize=9)
draw_flowbox(ax, 10.8, 2.0, 3.0, 1.5, '行动解码器\nAction Decoder\n(状态+目标→行动)', '#2E7D32', fontsize=9)

draw_arrow(ax, 3.7, 2.0, 5.0, 2.0, color='#666', lw=2)
ax.text(4.35, 2.35, '压缩', fontsize=8, color='#555', ha='center')
draw_arrow(ax, 8.0, 2.0, 9.3, 2.0, color='#666', lw=2)
ax.text(8.65, 2.35, '预测', fontsize=8, color='#555', ha='center')

# 闭环: 行动反馈回感知
draw_arrow(ax, 12.3, 1.2, 2.2, 1.2, color='#B0BEC5', lw=1.5)
draw_arrow(ax, 2.2, 1.2, 2.2, 1.25, color='#B0BEC5', lw=1.5)
ax.text(7.25, 0.85, '行动作用于环境 → 新状态 → 再感知 (闭环)', fontsize=9, color='#607D8B',
        ha='center', bbox=dict(boxstyle='round', facecolor='white', edgecolor='#B0BEC5'))

ax.set_title('图32-1 世界模型三组件 / World Model Three Components (感知→预测→行动闭环)',
             fontsize=13, fontweight='bold', pad=10)
fig.tight_layout()
fig.savefig(f'{IMG}\\flow_ch32_world_model_components.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('图32-1 三组件 saved')

# ============================================================
# 图32-2: 晶圆厂世界模型四层架构 (32.2.1)
# ============================================================
fig, ax = plt.subplots(figsize=(13, 7))
ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')

layers = [
    ('L1 设备级 Equipment', 6.4, '#E8EAF6', '#5C6BC0',
     ['腔体温度/压力动力学', '设备状态预测', '工艺参数预演']),
    ('L2 工艺级 Process', 4.8, '#E3F2FD', '#42A5F5',
     ['工艺代理模型', 'CD/膜厚/良率预测', '虚拟量测增强']),
    ('L3 产线级 Line', 3.2, '#E8F5E9', '#66BB6A',
     ['WIP流动预测', '瓶颈转移预演', '调度方案预演']),
    ('L4 整厂级 Fab', 1.6, '#FFF3E0', '#FFA726',
     ['产能规划', 'What-If情景', '战略决策支持']),
]
for name, y, bg, edge, items in layers:
    ax.add_patch(plt.Rectangle((0.8, y-0.55), 10.4, 1.1, facecolor=bg, edgecolor=edge, lw=1.5))
    ax.text(1.05, y+0.15, name, fontsize=10, fontweight='bold', color=edge)
    for i, item in enumerate(items):
        draw_flowbox(ax, 4.4 + i*2.5, y, 2.2, 0.75, item, color=edge, fontsize=8)

# 层间箭头: 数据向上聚合, 决策向下传导
for y1, y2 in [(5.85, 5.35), (4.25, 3.75), (2.65, 2.15)]:
    draw_arrow(ax, 1.25, y1, 1.25, y2, color='#B0BEC5', lw=2)
    draw_arrow(ax, 1.55, y2+0.1, 1.55, y1-0.1, color='#B0BEC5', lw=1.2)
ax.text(1.75, 5.6, '数据向上聚合\nprediction aggregation', fontsize=7.5, color='#78909C')
ax.text(1.75, 3.0, '决策向下传导\nscenario replay', fontsize=7.5, color='#78909C')

ax.set_title('图32-2 晶圆厂世界模型四层架构 / Four-Layer Fab World Model (L1设备→L2工艺→L3产线→L4整厂)',
             fontsize=13, fontweight='bold', pad=10)
fig.tight_layout()
fig.savefig(f'{IMG}\\flow_ch32_four_layers.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('图32-2 四层架构 saved')

# ============================================================
# 图32-3: 虚拟DOE贝叶斯优化循环 (32.4.3)
# ============================================================
fig, ax = plt.subplots(figsize=(13, 5))
ax.set_xlim(0, 13); ax.set_ylim(0, 4); ax.axis('off')

stages = [
    ('世界模型拟合响应面\n(参数→结果)', '#1565C0'),
    ('采集函数选点\n(利用+探索)', '#E65100'),
    ('真实产线少量实验\n(获取真实结果)', '#F9A825'),
    ('更新世界模型\n(加入训练数据)', '#2E7D32'),
]
for i, (txt, c) in enumerate(stages):
    x = 1.7 + i * 2.7
    draw_flowbox(ax, x, 2.2, 2.4, 1.4, txt, color=c, fontsize=8.5)
    if i < len(stages)-1:
        draw_arrow(ax, x+1.2, 2.2, x+1.5, 2.2, color='#666', lw=2)
draw_arrow(ax, 11.9, 1.4, 1.7, 1.4, color='#B0BEC5', lw=1.5)
draw_arrow(ax, 1.7, 1.4, 1.7, 1.5, color='#B0BEC5', lw=1.5)
ax.text(6.8, 1.0, '「想象-验证-校正」循环 / imagine-verify-correct loop', fontsize=9, color='#607D8B',
        ha='center', bbox=dict(boxstyle='round', facecolor='white', edgecolor='#B0BEC5'))

ax.set_title('图32-3 虚拟DOE与贝叶斯优化循环 / Virtual DOE & Bayesian Optimization Loop',
             fontsize=13, fontweight='bold', pad=10)
fig.tight_layout()
fig.savefig(f'{IMG}\\flow_ch32_virtual_doe_loop.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('图32-3 虚拟DOE循环 saved')
print('Part 1 done.')

# ============================================================
# 图32-4: 数字孪生驱动的排程闭环 (32.5.3)
# ============================================================
fig, ax = plt.subplots(figsize=(13, 4.5))
ax.set_xlim(0, 13); ax.set_ylim(0, 4); ax.axis('off')

draw_flowbox(ax, 1.8, 2.4, 2.8, 1.5, '真实产线状态\n(Real line state)', '#1565C0', fontsize=9)
draw_flowbox(ax, 5.2, 2.4, 2.8, 1.5, '世界模型状态同步\n(State sync)', '#E65100', fontsize=9)
draw_flowbox(ax, 8.6, 2.4, 2.8, 1.5, '方案预演\n(调度/排程/What-If)', '#F9A825', fontsize=9)
draw_flowbox(ax, 11.8, 2.4, 2.0, 1.5, '选择最优方案\n下发执行', '#2E7D32', fontsize=9)

draw_arrow(ax, 3.2, 2.4, 3.8, 2.4, color='#666', lw=2)
draw_arrow(ax, 6.6, 2.4, 7.2, 2.4, color='#666', lw=2)
draw_arrow(ax, 10.0, 2.4, 10.8, 2.4, color='#666', lw=2)

# 闭环: 执行结果反馈
draw_arrow(ax, 11.8, 1.6, 1.8, 1.6, color='#B0BEC5', lw=1.5)
draw_arrow(ax, 1.8, 1.6, 1.8, 1.65, color='#B0BEC5', lw=1.5)
ax.text(6.8, 1.2, '执行结果反馈 → 世界模型校准 → 预测精度持续提升', fontsize=9, color='#607D8B',
        ha='center', bbox=dict(boxstyle='round', facecolor='white', edgecolor='#B0BEC5'))

ax.set_title('图32-4 数字孪生驱动的排程闭环 / Digital-Twin-Driven Scheduling Closed Loop',
             fontsize=13, fontweight='bold', pad=10)
fig.tight_layout()
fig.savefig(f'{IMG}\\flow_ch32_scheduling_closed_loop.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('图32-4 排程闭环 saved')

# ============================================================
# 图32-5: 世界模型四阶段演进 (32.7.4)
# ============================================================
fig, ax = plt.subplots(figsize=(13, 4.5))
ax.set_xlim(0, 13); ax.set_ylim(0, 4); ax.axis('off')

stages = [
    ('阶段一\n单点数字孪生\n(设备/工艺级被动镜像)', '#90A4AE'),
    ('阶段二\n单点世界模型\n(预演+闭环校准)', '#42A5F5'),
    ('阶段三\n跨层世界模型\n(四层协同预演)', '#FFA726'),
    ('阶段四\n世界模型+AI融合\n(LLM/Agent/Ontology)', '#2E7D32'),
]
for i, (txt, c) in enumerate(stages):
    x = 1.7 + i * 2.7
    draw_flowbox(ax, x, 2.3, 2.5, 1.7, txt, color=c, fontsize=9)
    if i < len(stages)-1:
        draw_arrow(ax, x+1.25, 2.3, x+1.45, 2.3, color='#666', lw=2)
        ax.text(x+1.36, 2.65, '演进', fontsize=7.5, color='#555', ha='center')

ax.text(6.8, 0.9, '每一阶段都建立在上一阶段之上, 闭环校正是贯穿始终的生命线', fontsize=9,
        color='#607D8B', ha='center',
        bbox=dict(boxstyle='round', facecolor='white', edgecolor='#B0BEC5'))
ax.set_title('图32-5 世界模型四阶段演进路径 / World-Model Four-Stage Evolution Roadmap',
             fontsize=13, fontweight='bold', pad=10)
fig.tight_layout()
fig.savefig(f'{IMG}\\flow_ch32_evolution_roadmap.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('图32-5 演进路径 saved')
print('Part 2 done.')

