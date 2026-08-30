"""
全书流程图生成脚本
为各章节中的关键流程生成可视化流程图
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

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

def draw_diamond(ax, x, y, w, h, text, color='#FF9800', fontsize=8):
    diamond = mpatches.FancyBboxPatch((x - w/2, y - h/2), w, h,
                                       boxstyle="round,pad=0.05",
                                       facecolor=color, edgecolor=color, alpha=0.85, linewidth=2)
    ax.add_patch(diamond)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight='bold', color='white')
    return (x, y, w, h)


# ============================================================
# 1. Ch6: NPI流程图
# ============================================================
fig, ax = plt.subplots(figsize=(16, 4))
ax.set_xlim(0, 16)
ax.set_ylim(0, 4)
ax.axis('off')

stages = [
    (1.5, 2, '工艺设计\n(0-3月)', '#2196F3'),
    (4.5, 2, 'DOE验证\n(3-6月)', '#4CAF50'),
    (7.5, 2, '良率爬坡\n(6-12月)', '#FF9800'),
    (10.5, 2, '量产移交\n(12-15月)', '#F44336'),
    (13.5, 2, '量产监控\n(持续)', '#9C27B0'),
]
for x, y, text, color in stages:
    draw_flowbox(ax, x, y, 2.2, 1.2, text, color=color, fontsize=9)
for i in range(len(stages)-1):
    draw_arrow(ax, stages[i][0]+1.1, 2, stages[i+1][0]-1.1, 2)

# 添加里程碑标注
milestones = ['工艺流程定义', '最优参数确认', '良率>90%', 'SPEC Release', '持续优化']
for i, (ms, (x, y, _, _)) in enumerate(zip(milestones, stages)):
    ax.text(x, 0.7, f'里程碑:\n{ms}', ha='center', fontsize=8, color='#333',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

ax.set_title('第6章：NPI（新产品导入）流程与里程碑', fontsize=14, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch6_npi.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch6 NPI saved.")


# ============================================================
# 2. Ch7: 智能派工流程图
# ============================================================
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis('off')

# 输入层
draw_flowbox(ax, 3, 7, 2, 0.7, 'MES: 批次信息', '#2196F3', fontsize=8)
draw_flowbox(ax, 3, 6, 2, 0.7, 'FDC: 设备状态', '#4CAF50', fontsize=8)
draw_flowbox(ax, 3, 5, 2, 0.7, 'APS: 生产计划', '#FF9800', fontsize=8)
draw_flowbox(ax, 3, 4, 2, 0.7, 'YMS: 良率数据', '#9C27B0', fontsize=8)

# 感知层
draw_flowbox(ax, 7, 6.5, 2.5, 1.0, '感知层 (Neural)\nGNN编码全厂状态\nLSTM编码设备健康', '#00BCD4', fontsize=8)
draw_arrow(ax, 4, 7, 5.75, 6.7, '#2196F3')
draw_arrow(ax, 4, 6, 5.75, 6.5, '#4CAF50')
draw_arrow(ax, 4, 5, 5.75, 6.3, '#FF9800')
draw_arrow(ax, 4, 4, 5.75, 6.1, '#9C27B0')

# 决策层
draw_flowbox(ax, 7, 4, 2.5, 1.0, '决策层 (Action)\nRL策略网络\n输出派工指令', '#FF5722', fontsize=8)
draw_arrow(ax, 7, 6, 7, 4.5, '#333')

# 约束检查
draw_diamond(ax, 10.5, 4, 2, 0.8, '满足工艺\n约束?', '#FF9800', fontsize=8)
draw_arrow(ax, 8.25, 4, 9.5, 4, '#FF5722')

# 执行
draw_flowbox(ax, 13, 5.5, 1.8, 0.7, '执行派工', '#4CAF50', fontsize=8)
draw_arrow(ax, 11, 4.5, 13, 5.15, '#4CAF50')
ax.text(12, 4.8, '是', fontsize=9, color='#4CAF50', fontweight='bold')

# 调整
draw_flowbox(ax, 13, 2.5, 1.8, 0.7, '调整方案', '#F44336', fontsize=8)
draw_arrow(ax, 11, 3.5, 13, 2.85, '#F44336')
ax.text(12, 3, '否', fontsize=9, color='#F44336', fontweight='bold')
draw_arrow(ax, 13, 2.85, 8.5, 3.8, '#F44336')

# 反馈
draw_flowbox(ax, 7, 1, 2.5, 0.7, '结果反馈\n(奖励信号)', '#795548', fontsize=8)
draw_arrow(ax, 13, 5.15, 13, 3, '#666')
draw_arrow(ax, 7, 3.5, 7, 1.35, '#666')
draw_arrow(ax, 5.75, 1, 5.75, 5.5, '#795548')

ax.set_title('第7章：RL驱动的智能派工流程（感知→决策→约束→执行→反馈）', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch7_dispatch.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch7 dispatch saved.")


# ============================================================
# 3. Ch8: PM计划流程图
# ============================================================
fig, ax = plt.subplots(figsize=(14, 6))
ax.set_xlim(0, 14)
ax.set_ylim(0, 6)
ax.axis('off')

draw_flowbox(ax, 2, 5, 2.2, 0.7, 'PM年度计划\n(符号规划)', '#2196F3', fontsize=8)
draw_flowbox(ax, 2, 3.5, 2.2, 0.7, '设备FDC信号\n(LSTM感知)', '#4CAF50', fontsize=8)
draw_arrow(ax, 2, 4.65, 2, 3.85, '#333')

draw_flowbox(ax, 5.5, 4.5, 2, 0.7, 'RUL预测', '#FF9800', fontsize=8)
draw_arrow(ax, 3.1, 5, 4.5, 4.65, '#2196F3')
draw_arrow(ax, 3.1, 3.5, 4.5, 4.35, '#4CAF50')

draw_diamond(ax, 8.5, 4.5, 1.8, 0.8, 'RUL <\n阈值?', '#FF9800', fontsize=8)
draw_arrow(ax, 6.5, 4.5, 7.6, 4.5, '#333')

# 是 → 自适应PM
draw_flowbox(ax, 11.5, 5.5, 2.2, 0.7, '自适应PM\n(RL选时机)', '#F44336', fontsize=8)
draw_arrow(ax, 9.2, 4.8, 10.4, 5.3, '#F44336')
ax.text(10, 5.2, '是', fontsize=9, color='#F44336', fontweight='bold')

# 否 → 继续监测
draw_flowbox(ax, 11.5, 3.5, 2.2, 0.7, '继续运行\n+持续监测', '#4CAF50', fontsize=8)
draw_arrow(ax, 9.2, 4.2, 10.4, 3.65, '#4CAF50')
ax.text(10, 3.8, '否', fontsize=9, color='#4CAF50', fontweight='bold')

# PM执行
draw_flowbox(ax, 7, 2, 2, 0.7, '执行PM', '#795548', fontsize=8)
draw_arrow(ax, 11.5, 5.15, 7.5, 2.35, '#795548')
draw_arrow(ax, 11.5, 3.15, 7.5, 2.0, '#795548')

# 验证
draw_flowbox(ax, 3, 2, 2, 0.7, '验证批次\n(Neural感知)', '#00BCD4', fontsize=8)
draw_arrow(ax, 6, 2, 4, 2, '#333')

# 知识更新
draw_flowbox(ax, 3, 0.5, 2.5, 0.6, '更新KG: PM效果记录', '#9C27B0', fontsize=8)
draw_arrow(ax, 3, 1.65, 3, 0.8, '#666')
draw_arrow(ax, 3, 0.5, 0.5, 0.5, '#9C27B0')
draw_arrow(ax, 0.5, 0.5, 0.5, 3.5, '#9C27B0')
draw_arrow(ax, 0.5, 3.5, 0.9, 3.5, '#9C27B0')

ax.set_title('第8章：预测性维护PM计划流程（符号规划+感知+自适应执行）', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch8_pm.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch8 PM saved.")


# ============================================================
# 4. Ch18: NB融合良率根因分析流程图
# ============================================================
fig, ax = plt.subplots(figsize=(16, 5))
ax.set_xlim(0, 16)
ax.set_ylim(0, 5)
ax.axis('off')

steps = [
    (1.5, 3, 1.8, 1.0, '感知层\n(Neural)\nCNN识别\n缺陷模式', '#2196F3'),
    (4.2, 3, 1.8, 1.0, '检索层\n(Symbolic)\nKG检索\n相关工艺', '#4CAF50'),
    (6.9, 3, 1.8, 1.0, '推理层\n(Symbolic)\n规则引擎\n检查SPC', '#FF9800'),
    (9.6, 3, 1.8, 1.0, '生成层\n(Neural)\nLLM生成\n分析报告', '#9C27B0'),
    (12.3, 3, 1.8, 1.0, '验证层\n(Symbolic)\n规则验证\n一致性', '#F44336'),
    (14.5, 3, 1.5, 1.0, '输出\n可追溯\n分析报告', '#00BCD4'),
]

for x, y, w, h, text, color in steps:
    draw_flowbox(ax, x, y, w, h, text, color=color, fontsize=8)

for i in range(len(steps)-1):
    x_end = steps[i][0] + steps[i][2]/2
    x_start = steps[i+1][0] - steps[i+1][2]/2
    draw_arrow(ax, x_end, 3, x_start, 3, '#666')

# 反馈循环
draw_arrow(ax, 12.3, 2.5, 12.3, 1.5, '#F44336')
draw_arrow(ax, 12.3, 1.5, 1.5, 1.5, '#F44336')
draw_arrow(ax, 1.5, 1.5, 1.5, 2.5, '#F44336')
ax.text(7, 1.2, '验证失败 → 重新感知与推理', ha='center', fontsize=9, color='#F44336', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#FFEBEE', alpha=0.8))

# 标注
labels = ['94%置信度', 'SPC 3.2σ', '超2σ控制限', '工程师可读', '逻辑一致', '']
for i, label in enumerate(labels):
    if label:
        ax.text(steps[i][0], 4.2, label, ha='center', fontsize=8, color=steps[i][5],
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor=steps[i][5]))

ax.set_title('第18章：NB融合——可验证的良率根因分析流程\n（Neural感知 → Symbolic检索 → Symbolic推理 → Neural生成 → Symbolic验证）',
             fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch18_nb_rca.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch18 NB RCA saved.")


# ============================================================
# 5. Ch19: NA融合感知-决策闭环
# ============================================================
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.axis('off')

# 感知层
draw_flowbox(ax, 3, 7, 2.5, 0.8, '感知层 (Neural)\nCNN: 晶圆图特征\nLSTM: FDC信号特征', '#2196F3', fontsize=8)
draw_flowbox(ax, 3, 5, 2.5, 0.8, '状态编码\nGNN: 全厂拓扑\n多模态融合', '#00BCD4', fontsize=8)
draw_arrow(ax, 3, 6.6, 3, 5.4, '#2196F3')

# 决策层
draw_flowbox(ax, 3, 3, 2.5, 0.8, '决策层 (Action)\nRL策略网络\nπ_θ(a|s)', '#FF5722', fontsize=8)
draw_arrow(ax, 3, 4.6, 3, 3.4, '#00BCD4')

# 行动
draw_flowbox(ax, 3, 1, 2.5, 0.8, '行动执行\n参数调整/派工\nPM触发', '#4CAF50', fontsize=8)
draw_arrow(ax, 3, 2.6, 3, 1.4, '#FF5722')

# 环境（晶圆厂）
draw_flowbox(ax, 8, 4, 3, 1.2, '晶圆厂环境\n(真实生产环境)\n\n批次处理 → 量测结果', '#795548', fontsize=9)

# 反馈
draw_arrow(ax, 3, 0.6, 8, 3.4, '#4CAF50')
ax.text(5.5, 1.5, '行动→环境', fontsize=9, color='#4CAF50', fontweight='bold')

draw_arrow(ax, 8, 4.6, 8, 7, '#795548')
ax.text(8.5, 6, '观测\n(良率/SPC)', fontsize=9, color='#795548', fontweight='bold')

draw_arrow(ax, 6.5, 7, 4.25, 7, '#2196F3')
ax.text(5.5, 7.3, '感知', fontsize=9, color='#2196F3', fontweight='bold')

# 奖励信号
draw_flowbox(ax, 8, 1.5, 2.5, 0.7, '奖励信号\nr = f(良率, 交期, 利用率)', '#FF9800', fontsize=8)
draw_arrow(ax, 8, 3.4, 8, 1.85, '#FF9800')
draw_arrow(ax, 6.75, 1.5, 4.25, 1.5, '#FF9800')
draw_arrow(ax, 3, 1, 3, 2.6, '#FF9800')
ax.text(3.5, 1.5, '策略更新', fontsize=8, color='#FF9800', fontweight='bold')

ax.set_title('第19章：NA融合——感知-决策闭环\n（Neural感知 → Action决策 → 环境交互 → 奖励反馈 → 策略更新）',
             fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch19_na_loop.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch19 NA loop saved.")


# ============================================================
# 6. Ch20: SA融合规划-执行架构
# ============================================================
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis('off')

# 符号规划层
draw_flowbox(ax, 3.5, 7, 3, 0.7, '符号规划层 (Symbolic)\nHTN任务分解', '#2196F3', fontsize=9)

sub_tasks = [
    (1.5, 5.5, '子任务1:\n工艺设计', '#42A5F5'),
    (3.5, 5.5, '子任务2:\nDOE验证', '#42A5F5'),
    (5.5, 5.5, '子任务3:\n良率爬坡', '#42A5F5'),
]
for x, y, text, color in sub_tasks:
    draw_flowbox(ax, x, y, 1.6, 0.7, text, color=color, fontsize=8)
    draw_arrow(ax, 3.5, 6.65, x, 5.85, '#2196F3')

# 行为执行层
for i, (x, _, text, color) in enumerate(sub_tasks):
    draw_flowbox(ax, x, 3.5, 1.6, 0.7, f'RL执行\n自适应', '#FF5722', fontsize=8)
    draw_arrow(ax, x, 5.15, x, 3.85, '#FF5722')

# 不确定性处理
draw_diamond(ax, 1.5, 2, 1.4, 0.6, '偏离?', '#FF9800', fontsize=8)
draw_diamond(ax, 3.5, 2, 1.4, 0.6, '偏离?', '#FF9800', fontsize=8)
draw_diamond(ax, 5.5, 2, 1.4, 0.6, '偏离?', '#FF9800', fontsize=8)

for x in [1.5, 3.5, 5.5]:
    draw_arrow(ax, x, 3.15, x, 2.3, '#333')

# 自适应调整
draw_flowbox(ax, 9, 5.5, 3, 0.7, '自适应调整 (Action)\nRL重新规划子任务\n局部优化', '#4CAF50', fontsize=9)
for x in [1.5, 3.5, 5.5]:
    draw_arrow(ax, x + 0.7, 2, 7.5, 5.3, '#FF9800')
    ax.text(x + 1.5, 3.5, '是', fontsize=8, color='#FF9800', fontweight='bold')

draw_arrow(ax, 9, 5.15, 9, 3.85, '#4CAF50')
draw_flowbox(ax, 9, 3.5, 2.5, 0.7, '局部重规划\n不改变全局', '#00BCD4', fontsize=8)
draw_arrow(ax, 7.75, 3.5, 6.3, 3.5, '#00BCD4')

# 符号层验证
draw_flowbox(ax, 9, 1.5, 3, 0.7, '符号层验证\n全局一致性检查', '#9C27B0', fontsize=9)
draw_arrow(ax, 9, 3.15, 9, 1.85, '#9C27B0')
draw_arrow(ax, 7.5, 1.5, 3.5, 1.5, '#9C27B0')
draw_arrow(ax, 3.5, 1.5, 3.5, 2, '#9C27B0')

ax.text(12, 2, '反馈循环:\n规划→执行→\n自适应→验证', fontsize=9, color='#9C27B0', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#F3E5F5', alpha=0.9))

ax.set_title('第20章：SA融合——符号规划+行为执行的分层架构\n（HTN规划 → RL执行 → 自适应调整 → 全局一致性验证）',
             fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch20_sa_architecture.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch20 SA architecture saved.")


# ============================================================
# 7. Ch21: NSA全融合闭环
# ============================================================
fig, ax = plt.subplots(figsize=(12, 10))
ax.set_xlim(0, 12)
ax.set_ylim(0, 10)
ax.axis('off')

# 中心圆 - NSA
circle = plt.Circle((6, 5), 1.2, color='#9C27B0', alpha=0.3)
ax.add_patch(circle)
circle2 = plt.Circle((6, 5), 0.8, color='#9C27B0', alpha=0.5)
ax.add_patch(circle2)
ax.text(6, 5, 'NSA\n全融合', ha='center', va='center', fontsize=12, fontweight='bold', color='white')

# 三个维度
dimensions = [
    (6, 8.5, '感知 (Neural)\nCNN/LSTM/GNN\n多模态感知', '#2196F3', 'down'),
    (2, 3, '认知 (Symbolic)\n知识图谱+推理\n规则引擎', '#4CAF50', 'right'),
    (10, 3, '行动 (Action)\nRL策略+控制\n自主执行', '#FF5722', 'left'),
]

for x, y, text, color, _ in dimensions:
    draw_flowbox(ax, x, y, 3, 1.0, text, color=color, fontsize=9)
    # 连接到中心
    dx = 6 - x
    dy = 5 - y
    dist = np.sqrt(dx**2 + dy**2)
    draw_arrow(ax, x + dx/dist * 1.5, y + dy/dist * 0.5,
              6 - dx/dist * 1.3, 5 - dy/dist * 0.8, color, )

# 外层：世界模型
wm = mpatches.FancyBboxPatch((1, 1), 10, 8.5, boxstyle="round,pad=0.3",
                               facecolor='none', edgecolor='#795548', linewidth=2, linestyle='--')
ax.add_patch(wm)
ax.text(11, 9, '世界模型 / 数字孪生', fontsize=10, color='#795548', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# 四阶段演进
stages = [
    (1.5, 0.3, '阶段1\nAI辅助', '#81C784'),
    (4, 0.3, '阶段2\nAI增强', '#FFB74D'),
    (6.5, 0.3, '阶段3\nAI自主', '#E57373'),
    (9, 0.3, '阶段4\n具身智能', '#BA68C8'),
]
for x, y, text, color in stages:
    draw_flowbox(ax, x, y, 1.8, 0.5, text, color=color, fontsize=8)
for i in range(len(stages)-1):
    draw_arrow(ax, stages[i][0]+0.9, 0.3, stages[i+1][0]-0.9, 0.3, '#666')

# 闭环箭头
ax.annotate('', xy=(6, 7.8), xytext=(8.5, 4),
            arrowprops=dict(arrowstyle='->', color='#FF5722', lw=2, connectionstyle='arc3,rad=-0.3'))
ax.annotate('', xy=(3.5, 4), xytext=(6, 7.8),
            arrowprops=dict(arrowstyle='->', color='#2196F3', lw=2, connectionstyle='arc3,rad=-0.3'))
ax.annotate('', xy=(8.5, 3.5), xytext=(3.5, 3),
            arrowprops=dict(arrowstyle='->', color='#4CAF50', lw=2, connectionstyle='arc3,rad=0.2'))

ax.set_title('第21章：NSA全融合——感知-认知-行动闭环与具身智能演进\n（世界模型驱动的完整智能闭环 → 从AI辅助到具身智能）',
             fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch21_nsa_loop.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch21 NSA loop saved.")

print("\n=== All flowcharts generated successfully ===")
