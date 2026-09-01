"""
第26章 新增流程图 (batch7):
1. 具身智能技术栈 (感知-理解-规划-执行 + 学习反馈闭环)
2. VLA(视觉-语言-行动)模型工作流程
3. 洁净室机械臂 EFEM 自动上下料工作流
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

# ============================================================
# 1. Ch26 图A: 具身智能技术栈 (感知-理解-规划-执行 + 学习闭环)
# ============================================================
fig, ax = plt.subplots(figsize=(13, 8))
ax.set_xlim(0, 13); ax.set_ylim(0, 9.5); ax.axis('off')

layers = [
    (8.2, '多模态感知层\n视觉(相机/3D) / 力觉 / 触觉 / 激光雷达', '#00838F', '感知物理环境'),
    (6.6, '世界模型层\n语义地图 / 数字孪生 / Ontology', '#1565C0', '理解"我在哪、周围是什么"'),
    (5.0, '认知规划层\n大语言模型 / 任务规划器', '#283593', '把意图分解为行动序列'),
    (3.4, '行动执行层\nVLA模型 / 运动控制 / 机械臂与移动底盘', '#2E7D32', '执行物理动作'),
    (1.8, '学习与反馈层\n模仿学习 / 强化学习 / 遥操作数据', '#6A1B9A', '从经验中改进'),
]
for y, text, color, _ in layers:
    draw_flowbox(ax, 6.0, y, 8.0, 1.2, text, color=color, fontsize=9.5)
for i in range(len(layers)-1):
    draw_arrow(ax, 6.0, layers[i][0]-0.6, 6.0, layers[i+1][0]+0.62, color='#444')
# 学习反馈闭环: 底部 → 认知规划层
ax.annotate('', xy=(1.6, 5.0), xytext=(1.6, 1.8),
            arrowprops=dict(arrowstyle='->', color='#999', lw=1.8))
draw_arrow(ax, 2.0, 1.8, 1.6, 1.8, color='#999')
draw_arrow(ax, 1.6, 5.0, 2.0, 5.0, color='#999')
ax.text(1.15, 3.4, '经验反馈\n持续改进', ha='center', fontsize=9, color='#777', rotation=90)
# 右侧作用注释
for y, _, color, role in layers:
    ax.text(10.4, y, role, ha='left', va='center', fontsize=9, color=color, fontweight='bold')

ax.set_title('第26章: 具身智能"感知-理解-规划-执行"技术栈（含学习反馈闭环）', fontsize=13, fontweight='bold', pad=12)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch26_tech_stack.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Flow Ch26 Tech Stack saved.')

# ============================================================
# 2. Ch26 图B: VLA(视觉-语言-行动)模型工作流程
# ============================================================
fig, ax = plt.subplots(figsize=(15, 5.5))
ax.set_xlim(0, 15); ax.set_ylim(0, 5.5); ax.axis('off')

draw_flowbox(ax, 2.1, 3.7, 3.4, 1.3, '相机视觉输入\n(图像 / 3D点云)', '#00838F', fontsize=9.5)
draw_flowbox(ax, 2.1, 1.9, 3.4, 1.3, '自然语言指令\n("把3号晶圆盒搬到刻蚀机EFEM载台")', '#FF9800', fontsize=8.5)
draw_flowbox(ax, 6.9, 2.8, 3.2, 2.0, 'VLA 大模型\n(视觉-语言-行动统一)', '#283593', fontsize=10)
draw_flowbox(ax, 10.6, 2.8, 2.4, 1.5, '动作序列\n(轨迹/抓取姿态/关节控制)', '#1565C0', fontsize=8.5)
draw_flowbox(ax, 13.5, 2.8, 2.2, 1.5, '机械臂\n物理执行', '#2E7D32', fontsize=9.5)

draw_arrow(ax, 3.8, 3.5, 5.3, 3.1, color='#444')
draw_arrow(ax, 3.8, 2.1, 5.3, 2.5, color='#444')
draw_arrow(ax, 8.5, 2.8, 9.4, 2.8, color='#444', label='端到端生成', ly=0.25)
draw_arrow(ax, 11.8, 2.8, 12.4, 2.8, color='#444')
# 环境反馈回路: 机械臂 → VLA 模型底部
draw_arrow(ax, 13.5, 2.0, 13.5, 0.9, color='#999')
draw_arrow(ax, 13.5, 0.9, 6.9, 0.9, color='#999')
draw_arrow(ax, 6.9, 0.9, 6.9, 1.65, color='#999')
ax.text(10.2, 0.5, '环境状态变化 → 新的视觉输入（闭环）', ha='center', fontsize=9, color='#777')

ax.text(7.5, 5.1, '从"为每个任务编写程序"走向"用自然语言指挥通用操作"', ha='center',
        fontsize=10, color='#555', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
ax.set_title('第26章: VLA(视觉-语言-行动)模型工作流程', fontsize=13, fontweight='bold', pad=12)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch26_vla_pipeline.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Flow Ch26 VLA Pipeline saved.')

# ============================================================
# 3. Ch26 图C: 洁净室机械臂 EFEM 自动上下料工作流
# ============================================================
fig, ax = plt.subplots(figsize=(16.5, 5.2))
ax.set_xlim(0, 16.5); ax.set_ylim(0, 5.2); ax.axis('off')

main = [
    (1.35, 'MES下发\n作业指令', '#1565C0'),
    (4.0, '视觉采集\nFOUP姿态', '#00838F'),
    (6.65, 'VLA生成\n抓取计划', '#283593'),
    (9.3, 'Ontology\n规则校验', '#6A1B9A'),
    (11.95, '执行\n上下料动作', '#2E7D32'),
    (14.6, '反馈\nMES/APC', '#1565C0'),
]
for x, text, color in main:
    draw_flowbox(ax, x, 3.4, 2.3, 1.4, text, color=color, fontsize=9)
for i in range(len(main)-1):
    draw_arrow(ax, main[i][0]+1.15, 3.4, main[i+1][0]-1.15, 3.4, color='#444')
ax.text(10.62, 3.8, '通过', ha='center', fontsize=8.5, color='#2E7D32', fontweight='bold')

# 分支: 校验不通过 → 重规划/上报
draw_arrow(ax, 9.3, 2.7, 9.3, 1.8, color='#F44336')
draw_flowbox(ax, 9.3, 1.15, 2.2, 1.0, '不通过:\n重规划/上报', '#F44336', fontsize=8.5)
# 分支: 执行异常 → 立即停止并报警
draw_arrow(ax, 11.95, 2.7, 11.95, 1.8, color='#F44336')
draw_flowbox(ax, 11.95, 1.15, 2.2, 1.0, '破损/偏移:\n立即停止并报警', '#F44336', fontsize=8.5)

ax.text(8.25, 4.75, '从"固定动作"走向"自适应": 视觉引导抓取 × 规则校验 × 异常即停', ha='center',
        fontsize=10, color='#555', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
ax.set_title('第26章: 洁净室机械臂 EFEM 自动上下料工作流', fontsize=13, fontweight='bold', pad=12)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch26_efem_workflow.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Flow Ch26 EFEM Workflow saved.')
