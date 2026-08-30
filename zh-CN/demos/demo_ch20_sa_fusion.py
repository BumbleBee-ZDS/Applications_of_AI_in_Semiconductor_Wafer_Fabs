"""
第20章 Demo: SA融合——符号规划+行为执行的晶圆厂任务编排
展示Symbolic+Action在NPI管理、异常响应、设备维护中的应用
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patches as mpatches

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHeI', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

fig = plt.figure(figsize=(20, 14))
gs = GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# ========== 左上: HTN任务分解树 ==========
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_xlim(0, 14)
ax1.set_ylim(0, 10)
ax1.set_title('SA融合: HTN任务分解与执行', fontsize=12, fontweight='bold', color='#2196F3')

# 根节点
root = FancyBboxPatch((5, 8.5), 4, 1.2, boxstyle='round,pad=0.1',
                       facecolor='#2196F3', alpha=0.3, edgecolor='#2196F3', linewidth=2)
ax1.add_patch(root)
ax1.text(7, 9.1, 'NPI工艺开发项目\n(根目标)', ha='center', va='center', fontsize=9, fontweight='bold')

# 第二层: 符号分解 (Symbolic)
layer2 = [
    (1.5, 6, '工艺设计', '#2196F3'),
    (5, 6, '设备调试', '#2196F3'),
    (8.5, 6, '试产验证', '#2196F3'),
    (12, 6, '良率提升', '#2196F3'),
]
for x, y, label, color in layer2:
    box = FancyBboxPatch((x-1.2, y-0.5), 2.4, 1, boxstyle='round,pad=0.1',
                         facecolor=color, alpha=0.2, edgecolor=color, linewidth=1.5)
    ax1.add_patch(box)
    ax1.text(x, y, label, ha='center', va='center', fontsize=8, fontweight='bold')
    ax1.annotate('', xy=(x, 6.5), xytext=(7, 8.5),
                arrowprops=dict(arrowstyle='->', color='#2196F3', lw=1.5))

# 第三层: RL执行 (Action)
layer3 = [
    (0.5, 3, 'DOE参数\n搜索(RL)', '#FF9800'),
    (2.5, 3, 'Recipe\n生成(RL)', '#FF9800'),
    (4, 3, '设备匹配\n(RL)', '#FF9800'),
    (6, 3, 'PM调度\n(RL)', '#FF9800'),
    (7.5, 3, 'CP测试\n(RL)', '#FF9800'),
    (9.5, 3, '良率分析\n(RL)', '#FF9800'),
    (11, 3, '缺陷优化\n(RL)', '#FF9800'),
    (12.5, 3, 'Root Cause\n(RL)', '#FF9800'),
]
for x, y, label, color in layer3:
    box = FancyBboxPatch((x-0.7, y-0.4), 1.4, 0.8, boxstyle='round,pad=0.05',
                         facecolor=color, alpha=0.2, edgecolor=color, linewidth=1)
    ax1.add_patch(box)
    ax1.text(x, y, label, ha='center', va='center', fontsize=6.5, fontweight='bold')

# 连接第二层到第三层
parent_map = {0: [0, 1], 1: [2, 3], 2: [4, 5], 3: [6, 7]}
for p_idx, children in parent_map.items():
    px, _, _, _ = layer2[p_idx]
    for c_idx in children:
        cx, cy, _, _ = layer3[c_idx]
        ax1.annotate('', xy=(cx, 3.4), xytext=(px, 5.5),
                     arrowprops=dict(arrowstyle='->', color='#999', lw=0.8, alpha=0.6))

# 标签
ax1.text(0.2, 9, 'Symbolic\n(规划分解)', fontsize=9, fontweight='bold', color='#2196F3', va='center')
ax1.text(0.2, 3, 'Action\n(RL执行)', fontsize=9, fontweight='bold', color='#FF9800', va='center')
ax1.text(0.2, 6, 'Symbolic\n(子目标)', fontsize=8, fontweight='bold', color='#2196F3', va='center')

# 执行状态
status_labels = ['完成', '完成', '进行中', '完成', '待执行', '完成', '进行中', '待执行']
status_colors = ['#4CAF50', '#4CAF50', '#FF9800', '#4CAF50', '#9E9E9E', '#4CAF50', '#FF9800', '#9E9E9E']
for i, (status, color) in enumerate(zip(status_labels, status_colors)):
    x, _, _, _ = layer3[i]
    ax1.plot(x, 1.8, 'o', color=color, markersize=8)
    ax1.text(x, 1.3, status, ha='center', va='center', fontsize=6, color=color, fontweight='bold')

ax1.axis('off')

# ========== 中上: 符号规划+RL执行对比 ==========
ax2 = fig.add_subplot(gs[0, 1])
tasks = ['NPI周期\n(周)', '任务完成\n率(%)', '资源利用\n率(%)', '异常响应\n时间(h)', '计划偏差\n(%)']
pure_rl = [12, 78, 72, 4.5, 15]
pure_symbolic = [16, 85, 68, 6.0, 8]
sa_fusion = [9, 93, 88, 1.5, 3]

x = np.arange(len(tasks))
w = 0.25
ax2.bar(x - w, pure_rl, w, label='纯RL', color='#FF9800', alpha=0.8)
ax2.bar(x, pure_symbolic, w, label='纯符号规划', color='#2196F3', alpha=0.8)
ax2.bar(x + w, sa_fusion, w, label='SA融合', color='#9C27B0', alpha=0.8)

for i in range(len(tasks)):
    ax2.text(i + w, sa_fusion[i] + 1, f'{sa_fusion[i]}', ha='center', fontsize=8, fontweight='bold')

ax2.set_xticks(x)
ax2.set_xticklabels(tasks, fontsize=9)
ax2.set_title('纯RL vs 纯符号 vs SA融合\nNPI项目管理对比', fontsize=11, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(axis='y', alpha=0.3)

# ========== 右上: 异常响应流程自动化 ==========
ax3 = fig.add_subplot(gs[0, 2])
ax3.set_xlim(0, 10)
ax3.set_ylim(0, 10)
ax3.set_title('MFG: 异常响应流程自动化', fontsize=12, fontweight='bold', color='#2196F3')

flow = [
    (5, 9, '设备停机告警\n(事件触发)', '#F44336', '#FFF3E0'),
    (5, 7.5, '符号引擎: 匹配响应规则\nIF停机 AND 工艺=刻蚀\nTHEN 启动应急流程', '#2196F3', '#E3F2FD'),
    (2, 6, '子任务1: WIP\n转移(RL优化)', '#FF9800', '#FFF8E1'),
    (5, 6, '子任务2: PM\n调度(RL决策)', '#FF9800', '#FFF8E1'),
    (8, 6, '子任务3: 产能\n重分配(RL优化)', '#FF9800', '#FFF8E1'),
    (2, 4, '执行: 15批\nWIP转移至Tool-B', '#4CAF50', '#E8F5E9'),
    (5, 4, '执行: PM团队\n30分钟到达', '#4CAF50', '#E8F5E9'),
    (8, 4, '执行: 排程自动\n调整, 交期+0.3%', '#4CAF50', '#E8F5E9'),
    (5, 2, '验证: 设备恢复\n生产正常', '#9C27B0', '#F3E5F5'),
    (5, 0.5, '总耗时: 38分钟\n(传统: 4小时+)', '#9C27B0', '#F3E5F5'),
]
for x, y, label, edge, face in flow:
    box = FancyBboxPatch((x-1.5, y-0.5), 3, 1, boxstyle='round,pad=0.1',
                         facecolor=face, edgecolor=edge, linewidth=1.5)
    ax3.add_patch(box)
    ax3.text(x, y, label, ha='center', va='center', fontsize=7, fontweight='bold')

# 箭头
arrows = [(5, 8.5, 5, 8), (5, 7, 2, 6.5), (5, 7, 5, 6.5), (5, 7, 8, 6.5),
          (2, 5.5, 2, 4.5), (5, 5.5, 5, 4.5), (8, 5.5, 8, 4.5),
          (2, 3.5, 5, 2.5), (5, 3.5, 5, 2.5), (8, 3.5, 5, 2.5),
          (5, 1.5, 5, 1)]
for x1, y1, x2, y2 in arrows:
    ax3.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.2))

ax3.axis('off')

# ========== 左中: PM计划+自适应执行甘特图 ==========
ax4 = fig.add_subplot(gs[1, 0])
np.random.seed(77)
tasks_gantt = [
    ('PM-ToolA01\n(符号规划)', 0, 4, '#2196F3', '符号'),
    ('PM-ToolA01\n(RL执行)', 4, 3, '#FF9800', 'RL'),
    ('PM-ToolB03\n(符号规划)', 1, 3, '#2196F3', '符号'),
    ('PM-ToolB03\n(RL执行)', 3.5, 2.5, '#FF9800', 'RL'),
    ('PM-ToolC02\n(符号规划)', 5, 4, '#2196F3', '符号'),
    ('PM-ToolC02\n(RL执行)', 9, 2, '#FF9800', 'RL'),
    ('PM-ToolD01\n(符号规划)', 7, 3, '#2196F3', '符号'),
    ('PM-ToolD01\n(RL执行)', 10, 2.5, '#FF9800', 'RL'),
]
for i, (name, start, duration, color, exec_type) in enumerate(tasks_gantt):
    y = len(tasks_gantt) - i - 1
    ax4.barh(y, duration, left=start, height=0.6, color=color, alpha=0.7, edgecolor='white')
    ax4.text(start + duration/2, y, f'{exec_type}', ha='center', va='center', fontsize=7,
             color='white', fontweight='bold')

ax4.set_yticks(range(len(tasks_gantt)))
ax4.set_yticklabels([t[0].split('\n')[0] for t in tasks_gantt], fontsize=8)
ax4.set_xlabel('时间 (h)', fontsize=10)
ax4.set_title('PE/EE: PM计划(符号)+执行(RL)甘特图\n符号规划提供框架, RL优化执行顺序', fontsize=11, fontweight='bold')
ax4.set_xlim(0, 14)
ax4.grid(axis='x', alpha=0.3)

# 符号 vs RL图例
legend_elements = [mpatches.Patch(facecolor='#2196F3', alpha=0.7, label='符号规划阶段'),
                   mpatches.Patch(facecolor='#FF9800', alpha=0.7, label='RL执行阶段')]
ax4.legend(handles=legend_elements, fontsize=9, loc='upper right')

# ========== 中中: 多智能体符号-行为架构 ==========
ax5 = fig.add_subplot(gs[1, 1])
ax5.set_xlim(0, 10)
ax5.set_ylim(0, 10)
ax5.set_title('多智能体符号-行为架构', fontsize=12, fontweight='bold', color='#2196F3')

# 中央协调者
center = FancyBboxPatch((3.5, 7), 3, 1.2, boxstyle='round,pad=0.15',
                         facecolor='#9C27B0', alpha=0.3, edgecolor='#9C27B0', linewidth=2)
ax5.add_patch(center)
ax5.text(5, 7.6, '符号协调者\n(Symbolic Planner)', ha='center', va='center', fontsize=9, fontweight='bold')

# 四个RL Agent
agents = [
    (1.5, 4, 'PID Agent\n(RL)', '#FF9800'),
    (4, 4, 'MFG Agent\n(RL)', '#FF9800'),
    (6.5, 4, 'PE Agent\n(RL)', '#FF9800'),
    (8.5, 4, 'EE Agent\n(RL)', '#FF9800'),
]
for x, y, label, color in agents:
    box = FancyBboxPatch((x-0.8, y-0.5), 1.6, 1, boxstyle='round,pad=0.1',
                         facecolor=color, alpha=0.2, edgecolor=color, linewidth=1.5)
    ax5.add_patch(box)
    ax5.text(x, y, label, ha='center', va='center', fontsize=8, fontweight='bold')
    ax5.annotate('', xy=(x, 4.5), xytext=(5, 7),
                arrowprops=dict(arrowstyle='<->', color='#9C27B0', lw=1.5))

# 环境反馈
env_box = FancyBboxPatch((2, 1), 6, 1.2, boxstyle='round,pad=0.15',
                         facecolor='#4CAF50', alpha=0.2, edgecolor='#4CAF50', linewidth=2)
ax5.add_patch(env_box)
ax5.text(5, 1.6, '晶圆厂环境 (MES + FDC + SPC)', ha='center', va='center', fontsize=9, fontweight='bold')

for x, _, _, _ in agents:
    ax5.annotate('', xy=(x, 2.2), xytext=(x, 3.5),
                arrowprops=dict(arrowstyle='<->', color='#4CAF50', lw=1.2))

# 消息流标注
ax5.text(0.3, 5.5, '任务分配\n约束传递', fontsize=8, color='#9C27B0', fontweight='bold', rotation=90)
ax5.text(0.3, 2.5, '状态反馈\n奖励信号', fontsize=8, color='#4CAF50', fontweight='bold', rotation=90)

ax5.axis('off')

# ========== 右中: 符号约束对RL性能的提升 ==========
ax6 = fig.add_subplot(gs[1, 2])
episodes = np.arange(0, 300)
# 无约束RL: 收敛慢, 有波动
pure_rl_reward = -30 + 0.1 * episodes + 10 * np.sin(episodes * 0.1) + np.random.randn(300) * 5
pure_rl_reward = np.cumsum(pure_rl_reward) / np.arange(1, 301) * 10
# SA融合: 符号约束加速收敛
sa_reward = -30 + 0.2 * episodes * (1 - np.exp(-episodes / 50)) + np.random.randn(300) * 2
sa_reward = np.cumsum(sa_reward) / np.arange(1, 301) * 10

window = 15
pure_smooth = np.convolve(pure_rl_reward, np.ones(window)/window, mode='valid')
sa_smooth = np.convolve(sa_reward, np.ones(window)/window, mode='valid')

ax6.plot(episodes[window-1:], pure_smooth, color='#FF9800', linewidth=2, linestyle='--', label='纯RL (无约束)')
ax6.plot(episodes[window-1:], sa_smooth, color='#9C27B0', linewidth=2.5, label='SA融合 (符号约束)')
ax6.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
ax6.axvline(x=50, color='#2196F3', linestyle=':', alpha=0.5)
ax6.text(55, max(sa_smooth)*0.7, '符号约束\n加速收敛', fontsize=9, color='#2196F3', fontweight='bold')
ax6.set_xlabel('训练回合', fontsize=10)
ax6.set_ylabel('平均奖励', fontsize=10)
ax6.set_title('符号约束对RL收敛的加速效果', fontsize=11, fontweight='bold')
ax6.legend(fontsize=9)
ax6.grid(alpha=0.3)

# ========== 底部: SA融合效果雷达图 ==========
ax7 = fig.add_subplot(gs[2, :], polar=True)
categories = ['NPI周期\n缩短(%)', '异常响应\n加速(%)', 'PM效率\n提升(%)', '资源利用\n率(%)',
              '计划准确性\n(%)', '执行灵活性\n(1-10)', '跨部门\n协同(1-10)']
N = len(categories)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]

pure_symbolic_data = [20, 30, 25, 70, 90, 3, 5]
pure_rl_data = [40, 60, 50, 78, 55, 8, 4]
sa_data = [55, 85, 70, 90, 88, 9, 9]
sa_data += sa_data[:1]
pure_symbolic_data += pure_symbolic_data[:1]
pure_rl_data += pure_rl_data[:1]

ax7.plot(angles, sa_data, 'o-', linewidth=2.5, color='#9C27B0', label='SA融合')
ax7.fill(angles, sa_data, alpha=0.2, color='#9C27B0')
ax7.plot(angles, pure_symbolic_data, 's--', linewidth=1.5, color='#2196F3', label='纯符号规划')
ax7.fill(angles, pure_symbolic_data, alpha=0.1, color='#2196F3')
ax7.plot(angles, pure_rl_data, '^--', linewidth=1.5, color='#FF9800', label='纯RL')
ax7.fill(angles, pure_rl_data, alpha=0.1, color='#FF9800')
ax7.set_xticks(angles[:-1])
ax7.set_xticklabels(categories, fontsize=10)
ax7.set_title('SA融合 vs 纯符号 vs 纯RL：晶圆厂全维度对比', fontsize=13, fontweight='bold', pad=30)
ax7.legend(fontsize=11, loc='upper right', bbox_to_anchor=(1.25, 1.15))

fig.suptitle('第20章 Demo：SA融合（Symbolic+Action）——符号规划提供方向 + 行为执行提供灵活性',
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch20_sa_fusion.png',
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch20 SA fusion demo saved.")
plt.close()
