"""
第23章 Demo: Agent系统在晶圆厂的实践——多智能体协同框架
展示Agent在工艺分析、良率异常响应、动态调度中的协作
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
import matplotlib.patches as mpatches

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHeI', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

fig = plt.figure(figsize=(20, 14))
gs = GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# ========== 左上: 多Agent协同架构 ==========
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.set_title('晶圆厂多Agent协同架构', fontsize=12, fontweight='bold', color='#2196F3')

# 中央协调Agent
center = FancyBboxPatch((3, 7.5), 4, 1.2, boxstyle='round,pad=0.15',
                         facecolor='#9C27B0', alpha=0.3, edgecolor='#9C27B0', linewidth=2.5)
ax1.add_patch(center)
ax1.text(5, 8.1, 'Coordinator Agent\n(感知-规划-分发)', ha='center', va='center', fontsize=9, fontweight='bold')

# 四个专业Agent
agents = [
    (1.2, 5, 'PID Agent\n工艺分析\n推理+RAG', '#2196F3'),
    (4, 5, 'YED Agent\n良率监控\nML+KG', '#4CAF50'),
    (6.8, 5, 'MFG Agent\n调度优化\nRL+MILP', '#FF9800'),
    (9, 5, 'EE Agent\n设备健康\n时序+RL', '#F44336'),
]
for x, y, label, color in agents:
    box = FancyBboxPatch((x-1, y-0.7), 2, 1.4, boxstyle='round,pad=0.1',
                         facecolor=color, alpha=0.2, edgecolor=color, linewidth=1.5)
    ax1.add_patch(box)
    ax1.text(x, y, label, ha='center', va='center', fontsize=7.5, fontweight='bold')
    ax1.annotate('', xy=(x, 5.7), xytext=(5, 7.5),
                arrowprops=dict(arrowstyle='<->', color='#9C27B0', lw=1.5))

# 记忆层
mem_box = FancyBboxPatch((1, 2.5), 8, 1, boxstyle='round,pad=0.1',
                         facecolor='#607D8B', alpha=0.15, edgecolor='#607D8B', linewidth=1.5)
ax1.add_patch(mem_box)
ax1.text(5, 3, '共享记忆层 (短期+长期记忆, 向量数据库)', ha='center', va='center', fontsize=9, fontweight='bold')

for x, _, _, _ in agents:
    ax1.annotate('', xy=(x, 3.5), xytext=(x, 4.3),
                arrowprops=dict(arrowstyle='->', color='#607D8B', lw=1, alpha=0.5))

# 工具层
tools = ['MES\nAPI', 'FDC\nAPI', 'SPC\nAPI', 'KG\n查询', 'CP/FT\n数据', 'OEE\n计算']
for i, tool in enumerate(tools):
    x = 1 + i * 1.5
    box = FancyBboxPatch((x-0.5, 0.5), 1, 0.8, boxstyle='round,pad=0.05',
                         facecolor='#FFD54F', alpha=0.2, edgecolor='#FFD54F', linewidth=1)
    ax1.add_patch(box)
    ax1.text(x, 0.9, tool, ha='center', va='center', fontsize=6.5, fontweight='bold')

ax1.text(0.1, 1, '工具层', fontsize=8, fontweight='bold', color='#FBC02D', rotation=90, va='center')

ax1.axis('off')

# ========== 中上: Agent响应良率异常流程 ==========
ax2 = fig.add_subplot(gs[0, 1:])
ax2.set_xlim(0, 20)
ax2.set_ylim(0, 6)
ax2.set_title('Agent协同响应: 良率异常全流程 (从检测到解决)', fontsize=12, fontweight='bold', color='#2196F3')

steps = [
    (1.5, 'T+0min\nYED Agent\n检测良率\n下降7pp', '#4CAF50'),
    (4.5, 'T+2min\nCoordinator\n分发任务\n给4个Agent', '#9C27B0'),
    (7.5, 'T+5min\nPID Agent\n分析根因\n(RAG+KG)', '#2196F3'),
    (10.5, 'T+8min\nMFG Agent\nWIP调整\n(RL调度)', '#FF9800'),
    (13.5, 'T+12min\nEE Agent\n设备检查\n(时序分析)', '#F44336'),
    (16.5, 'T+15min\nCoordinator\n验证+执行\n(闭环确认)', '#9C27B0'),
    (19, 'T+18min\n解决\n良率恢复\n(自动验证)', '#4CAF50'),
]
for x, label, color in steps:
    box = FancyBboxPatch((x-1.3, 1.5), 2.6, 2.5, boxstyle='round,pad=0.1',
                         facecolor=color, alpha=0.2, edgecolor=color, linewidth=2)
    ax2.add_patch(box)
    lines = label.split('\n')
    for j, line in enumerate(lines):
        ax2.text(x, 3.5 - j * 0.5, line, ha='center', va='center', fontsize=7.5, fontweight='bold')

for i in range(len(steps) - 1):
    x_start = steps[i][0] + 1.3
    x_end = steps[i+1][0] - 1.3
    ax2.annotate('', xy=(x_end, 2.75), xytext=(x_start, 2.75),
                arrowprops=dict(arrowstyle='->', color='#666', lw=2))

# 时间轴
ax2.axhline(y=0.8, color='#999', linewidth=0.5)
for x, _, color in steps:
    ax2.plot(x, 0.8, 'o', color=color, markersize=6)

ax2.axis('off')

# ========== 第二行左: Agent vs 传统流程对比 ==========
ax3 = fig.add_subplot(gs[1, 0])
metrics = ['检测时间\n(min)', '根因分析\n(min)', '响应执行\n(min)', '总解决\n时间(h)',
           '准确率\n(%)', '人员介入\n(次)']
traditional = [30, 120, 60, 3.5, 75, 5]
agent_system = [0.2, 5, 3, 0.3, 94, 0.5]

x = np.arange(len(metrics))
w = 0.35
ax3.bar(x - w/2, traditional, w, label='传统人工流程', color='#FF6B6B', alpha=0.8)
ax3.bar(x + w/2, agent_system, w, label='Agent协同', color='#9C27B0', alpha=0.9)

for i in range(len(metrics)):
    speedup = traditional[i] / agent_system[i] if agent_system[i] > 0 else 0
    ax3.text(i, max(traditional[i], agent_system[i]) + 2, f'{speedup:.0f}x',
             ha='center', fontsize=9, fontweight='bold', color='#2196F3')

ax3.set_xticks(x)
ax3.set_xticklabels(metrics, fontsize=8)
ax3.set_title('传统流程 vs Agent协同\n(良率异常响应)', fontsize=11, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(axis='y', alpha=0.3)

# ========== 第二行中: Agent记忆与学习 ==========
ax4 = fig.add_subplot(gs[1, 1])
episodes = np.arange(0, 100)
# 随着Agent积累经验, 解决时间递减
resolution_time = 20 * np.exp(-episodes / 25) + 2 + np.random.randn(100) * 0.5
accuracy = 70 + 25 * (1 - np.exp(-episodes / 30)) + np.random.randn(100) * 2
accuracy = np.clip(accuracy, 70, 97)

ax4_twin = ax4.twinx()
ax4.plot(episodes, resolution_time, 'o-', color='#FF9800', linewidth=2, markersize=3, label='解决时间(min)')
ax4_twin.plot(episodes, accuracy, 's-', color='#4CAF50', linewidth=2, markersize=3, label='准确率(%)')

ax4.fill_between(episodes, resolution_time, resolution_time.min(), alpha=0.1, color='#FF9800')
ax4.set_xlabel('处理案例数', fontsize=10)
ax4.set_ylabel('解决时间 (min)', fontsize=10, color='#FF9800')
ax4_twin.set_ylabel('准确率 (%)', fontsize=10, color='#4CAF50')
ax4.set_title('Agent记忆与学习曲线\n(经验积累提升性能)', fontsize=11, fontweight='bold')
ax4.legend(loc='upper right', fontsize=9)
ax4_twin.legend(loc='center right', fontsize=9)
ax4.grid(alpha=0.3)

# ========== 第二行右: 整厂Agent架构 ==========
ax5 = fig.add_subplot(gs[1, 2])
ax5.set_xlim(0, 10)
ax5.set_ylim(0, 10)
ax5.set_title('整厂Agent架构: 从单点到系统级', fontsize=12, fontweight='bold', color='#2196F3')

# L0: 单点AI
l0_box = FancyBboxPatch((0.5, 0.5), 2, 1, boxstyle='round,pad=0.1',
                         facecolor='#81C784', alpha=0.2, edgecolor='#81C784', linewidth=1.5)
ax5.add_patch(l0_box)
ax5.text(1.5, 1, 'L0: 单点AI\n(缺陷分类)', ha='center', va='center', fontsize=7, fontweight='bold')

# L1: 部门Agent
l1_box = FancyBboxPatch((3, 0.5), 2.5, 1, boxstyle='round,pad=0.1',
                         facecolor='#FFB74D', alpha=0.2, edgecolor='#FFB74D', linewidth=1.5)
ax5.add_patch(l1_box)
ax5.text(4.25, 1, 'L1: 部门Agent\n(PID/YED\n调度/设备)', ha='center', va='center', fontsize=7, fontweight='bold')

# L2: 跨部门Agent
l2_box = FancyBboxPatch((5.8, 0.5), 2.5, 1, boxstyle='round,pad=0.1',
                         facecolor='#E57373', alpha=0.2, edgecolor='#E57373', linewidth=1.5)
ax5.add_patch(l2_box)
ax5.text(7.05, 1, 'L2: 跨部门Agent\n(协同优化\n异常响应)', ha='center', va='center', fontsize=7, fontweight='bold')

# L3: 整厂智能
l3_box = FancyBboxPatch((8.5, 0.5), 1.3, 1, boxstyle='round,pad=0.1',
                         facecolor='#BA68C8', alpha=0.2, edgecolor='#BA68C8', linewidth=1.5)
ax5.add_patch(l3_box)
ax5.text(9.15, 1, 'L3:\n整厂\n智能', ha='center', va='center', fontsize=6.5, fontweight='bold')

# 箭头
for i in range(3):
    x_start = [2.5, 5.5, 8.3][i]
    x_end = [3, 5.8, 8.5][i]
    ax5.annotate('', xy=(x_end, 1), xytext=(x_start, 1),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

# 能力增长曲线
levels = np.array([1, 2, 3, 4])
capability = [20, 55, 80, 95]
maturity = [100, 80, 40, 10]  # 成熟度(当前L0最成熟)

ax5_twin = ax5.twinx()
ax5_twin.bar(levels + 5, capability, 0.4, color='#2196F3', alpha=0.5, label='AI能力覆盖(%)')
ax5_twin.plot(levels + 5, maturity, 'o-', color='#FF9800', linewidth=2, markersize=8, label='技术成熟度(%)')

for i, (cap, mat) in enumerate(zip(capability, maturity)):
    ax5_twin.text(levels[i] + 5, cap + 2, f'{cap}%', ha='center', fontsize=7, fontweight='bold')
    ax5_twin.text(levels[i] + 5, mat + 2, f'{mat}%', ha='center', fontsize=7, color='#FF9800')

ax5.set_xlim(0, 10)
ax5.set_ylim(0, 3)
ax5_twin.set_ylim(0, 110)
ax5_twin.set_ylabel('百分比 (%)', fontsize=10)
ax5.set_title('整厂Agent四级架构\n与成熟度分析', fontsize=11, fontweight='bold')
ax5_twin.legend(fontsize=8, loc='upper left')
ax5.axis('off')

# ========== 第三行左: Agent通信网络 ==========
ax6 = fig.add_subplot(gs[2, 0])
np.random.seed(99)
# 模拟Agent间通信
import networkx as nx
G = nx.Graph()
agents_net = ['Coordinator', 'PID', 'YED', 'MFG', 'EE', 'Memory', 'KG', 'MES']
G.add_nodes_from(agents_net)

edges = [
    ('Coordinator', 'PID', 15),
    ('Coordinator', 'YED', 12),
    ('Coordinator', 'MFG', 18),
    ('Coordinator', 'EE', 10),
    ('PID', 'YED', 8),
    ('PID', 'KG', 6),
    ('YED', 'MFG', 5),
    ('MFG', 'EE', 7),
    ('MFG', 'MES', 20),
    ('EE', 'MES', 12),
    ('Coordinator', 'Memory', 25),
    ('PID', 'Memory', 8),
    ('YED', 'Memory', 6),
    ('MFG', 'Memory', 10),
    ('EE', 'Memory', 7),
    ('PID', 'KG', 4),
    ('YED', 'KG', 5),
]

pos = {
    'Coordinator': (0.5, 0.7),
    'PID': (0.2, 0.4), 'YED': (0.35, 0.25),
    'MFG': (0.65, 0.25), 'EE': (0.8, 0.4),
    'Memory': (0.5, 0.45), 'KG': (0.3, 0.1),
    'MES': (0.7, 0.1),
}

for u, v, w in edges:
    G.add_edge(u, v, weight=w)

# 绘制边
for u, v, data in G.edges(data=True):
    w = data.get('weight', 1)
    ax6.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
             color='#999', alpha=min(0.3 + w/30, 1.0), linewidth=w/5)

# 绘制节点
node_colors = {'Coordinator': '#9C27B0', 'PID': '#2196F3', 'YED': '#4CAF50',
               'MFG': '#FF9800', 'EE': '#F44336', 'Memory': '#607D8B', 'KG': '#795548', 'MES': '#FFD54F'}
for node in G.nodes():
    x, y = pos[node]
    color = node_colors.get(node, '#999')
    ax6.scatter(x, y, s=500, c=color, alpha=0.7, edgecolors='white', linewidths=2, zorder=5)
    ax6.text(x, y, node, ha='center', va='center', fontsize=7, fontweight='bold', color='white', zorder=6)

ax6.set_xlim(-0.05, 1.05)
ax6.set_ylim(-0.05, 0.9)
ax6.set_title('Agent通信网络\n(节点=Agent, 边宽=消息频率)', fontsize=11, fontweight='bold')
ax6.axis('off')

# ========== 第三行中: 动态调度Agent效果 ==========
ax7 = fig.add_subplot(gs[2, 1])
time_steps = np.arange(0, 48)
# 传统调度: WIP波动大
fifo_util = 65 + 20 * np.sin(time_steps * 0.3) + np.random.randn(48) * 8
fifo_util = np.clip(fifo_util, 50, 95)
# Agent调度: 平滑且高利用率
agent_util = 85 + 6 * np.sin(time_steps * 0.2) + np.random.randn(48) * 3
agent_util = np.clip(agent_util, 78, 95)

ax7.fill_between(time_steps, fifo_util, agent_util, alpha=0.1, color='#9C27B0')
ax7.plot(time_steps, fifo_util, 'o-', color='#FF6B6B', linewidth=1.5, markersize=3, label='传统FIFO调度')
ax7.plot(time_steps, agent_util, 's-', color='#9C27B0', linewidth=2, markersize=3, label='Agent动态调度')
ax7.axhline(y=90, color='#4CAF50', linestyle=':', alpha=0.5, label='目标利用率(90%)')
ax7.fill_between(time_steps, agent_util, 90, where=agent_util >= 90,
                  alpha=0.15, color='#4CAF50')
ax7.set_xlabel('时间 (h)', fontsize=10)
ax7.set_ylabel('设备利用率 (%)', fontsize=10)
ax7.set_title('MFG Agent: 动态调度效果\n(48h连续运行)', fontsize=11, fontweight='bold')
ax7.legend(fontsize=9)
ax7.grid(alpha=0.3)

# ========== 第三行右: 数字孪生+Agent闭环 ==========
ax8 = fig.add_subplot(gs[2, 2])
ax8.set_xlim(0, 10)
ax8.set_ylim(0, 10)
ax8.set_title('数字孪生 + Agent闭环', fontsize=12, fontweight='bold', color='#2196F3')

# 数字孪生层
dt_box = FancyBboxPatch((1, 6.5), 8, 1.5, boxstyle='round,pad=0.15',
                         facecolor='#2196F3', alpha=0.15, edgecolor='#2196F3', linewidth=2)
ax8.add_patch(dt_box)
ax8.text(5, 7.25, '数字孪生层 (实时镜像物理工厂)', ha='center', va='center', fontsize=9, fontweight='bold')

# Agent决策层
ag_box = FancyBboxPatch((1, 3.5), 8, 1.5, boxstyle='round,pad=0.15',
                         facecolor='#9C27B0', alpha=0.15, edgecolor='#9C27B0', linewidth=2)
ax8.add_patch(ag_box)
ax8.text(5, 4.25, 'Agent决策层 (推理+优化+验证)', ha='center', va='center', fontsize=9, fontweight='bold')

# 物理执行层
ph_box = FancyBboxPatch((1, 0.5), 8, 1.5, boxstyle='round,pad=0.15',
                         facecolor='#4CAF50', alpha=0.15, edgecolor='#4CAF50', linewidth=2)
ax8.add_patch(ph_box)
ax8.text(5, 1.25, '物理工厂层 (设备+WIP+工艺)', ha='center', va='center', fontsize=9, fontweight='bold')

# 双向箭头
ax8.annotate('', xy=(3, 5), xytext=(3, 6.5),
            arrowprops=dict(arrowstyle='<->', color='#2196F3', lw=2.5))
ax8.text(2.3, 5.75, '状态\n同步', ha='center', fontsize=7, color='#2196F3', fontweight='bold')
ax8.annotate('', xy=(7, 6.5), xytext=(7, 5),
            arrowprops=dict(arrowstyle='<->', color='#9C27B0', lw=2.5))
ax8.text(7.7, 5.75, '仿真\n验证', ha='center', fontsize=7, color='#9C27B0', fontweight='bold')

ax8.annotate('', xy=(3, 2), xytext=(3, 3.5),
            arrowprops=dict(arrowstyle='<->', color='#9C27B0', lw=2.5))
ax8.text(2.3, 2.75, '指令\n执行', ha='center', fontsize=7, color='#9C27B0', fontweight='bold')
ax8.annotate('', xy=(7, 3.5), xytext=(7, 2),
            arrowprops=dict(arrowstyle='<->', color='#4CAF50', lw=2.5))
ax8.text(7.7, 2.75, '反馈\n数据', ha='center', fontsize=7, color='#4CAF50', fontweight='bold')

# 闭环标注
ax8.annotate('', xy=(9.5, 0.5), xytext=(9.5, 8),
            arrowprops=dict(arrowstyle='->', color='#F44336', lw=2,
                          connectionstyle='arc3,rad=-0.3'))
ax8.text(9.8, 4.25, '闭环\n反馈', ha='center', fontsize=8, color='#F44336', fontweight='bold', rotation=90)

ax8.axis('off')

fig.suptitle('第23章 Demo：Agent系统在晶圆厂的实践——多智能体协同框架与整厂级智能',
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch23_agent_system.png',
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch23 Agent system demo saved.")
plt.close()
