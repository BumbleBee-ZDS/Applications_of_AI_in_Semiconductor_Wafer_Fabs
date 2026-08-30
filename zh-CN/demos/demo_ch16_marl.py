"""
第16章 Demo: 多智能体强化学习调度
模拟MARL在晶圆厂多设备协同调度中的应用
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

fig = plt.figure(figsize=(18, 12))
gs = GridSpec(3, 3, figure=fig, hspace=0.4, wspace=0.3)

# 左上：多智能体拓扑图
ax1 = fig.add_subplot(gs[0, 0])
import networkx as nx
G = nx.Graph()
agents = ['MFG\nAgent', 'PID\nAgent', 'PE\nAgent', 'EE\nAgent', 'YED\nAgent']
G.add_nodes_from(agents)
edges = [('MFG\nAgent', 'PID\nAgent'), ('MFG\nAgent', 'PE\nAgent'), ('MFG\nAgent', 'EE\nAgent'),
         ('PID\nAgent', 'YED\nAgent'), ('PE\nAgent', 'EE\nAgent'), ('PID\nAgent', 'PE\nAgent')]
G.add_edges_from(edges)
pos = nx.spring_layout(G, seed=42)
colors_map = {'MFG\nAgent': '#FF5722', 'PID\nAgent': '#2196F3', 'PE\nAgent': '#4CAF50',
              'EE\nAgent': '#FF9800', 'YED\nAgent': '#9C27B0'}
node_colors = [colors_map[n] for n in G.nodes()]
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2000, alpha=0.85, ax=ax1)
nx.draw_networkx_edges(G, pos, width=2, alpha=0.5, ax=ax1)
nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold', ax=ax1)
ax1.set_title('多智能体协同拓扑', fontsize=12, fontweight='bold')
ax1.axis('off')

# 中上：各Agent的奖励曲线
ax2 = fig.add_subplot(gs[0, 1:])
episodes = np.arange(1, 201)
agent_rewards = {
    'MFG Agent': -20 + 18*(1-np.exp(-episodes/30)) + np.random.randn(200)*1,
    'PID Agent': -15 + 12*(1-np.exp(-episodes/40)) + np.random.randn(200)*0.8,
    'PE Agent':  -18 + 15*(1-np.exp(-episodes/35)) + np.random.randn(200)*0.9,
    'EE Agent':  -12 + 10*(1-np.exp(-episodes/50)) + np.random.randn(200)*0.7,
}
colors_agents = ['#FF5722', '#2196F3', '#4CAF50', '#FF9800']
for (name, reward), color in zip(agent_rewards.items(), colors_agents):
    ax2.plot(episodes, reward, linewidth=2, label=name, color=color)
    ax2.fill_between(episodes, reward-1.5, reward+1.5, alpha=0.1, color=color)
ax2.set_xlabel('训练轮次', fontsize=10)
ax2.set_ylabel('累积奖励', fontsize=10)
ax2.set_title('各Agent的奖励收敛曲线（MARL训练过程）', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(alpha=0.3)

# 左中：协同 vs 独立决策
ax3 = fig.add_subplot(gs[1, 0])
metrics = ['完工时间\n(h)', '设备利用率\n(%)', '交期达成率\n(%)', '良率\n(%)', '冲突次数\n(次/天)']
independent = [18.5, 72, 80, 88, 12]
coordinated = [13.2, 88, 94, 92, 2]
x = np.arange(len(metrics))
w = 0.35
ax3.bar(x - w/2, independent, w, label='独立决策', color='#FF6B6B', alpha=0.8)
ax3.bar(x + w/2, coordinated, w, label='MARL协同', color='#4CAF50', alpha=0.8)
for i in range(len(metrics)):
    imp = ((coordinated[i] - independent[i]) / independent[i] * 100) if independent[i] > 0 else 0
    if i in [0, 4]:
        imp = -imp
    ax3.text(i, max(independent[i], coordinated[i]) + 1, f'{imp:+.0f}%', ha='center',
             fontsize=9, fontweight='bold', color='#2196F3')
ax3.set_xticks(x)
ax3.set_xticklabels(metrics, fontsize=9)
ax3.set_title('独立决策 vs MARL协同', fontsize=12, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(axis='y', alpha=0.3)

# 中中：WIP分布对比
ax4 = fig.add_subplot(gs[1, 1])
steps = np.arange(1, 11)
wip_independent = np.random.poisson(8, 10) + np.abs(np.sin(steps)) * 5
wip_coordinated = np.random.poisson(5, 10) + np.abs(np.sin(steps*0.5)) * 1
ax4.bar(steps - 0.15, wip_independent, 0.3, label='独立决策WIP', color='#FF6B6B', alpha=0.8)
ax4.bar(steps + 0.15, wip_coordinated, 0.3, label='MARL协同WIP', color='#4CAF50', alpha=0.8)
ax4.axhline(y=np.mean(wip_coordinated), color='#4CAF50', linestyle='--', alpha=0.5)
ax4.set_xlabel('工艺步骤', fontsize=10)
ax4.set_ylabel('WIP (片)', fontsize=10)
ax4.set_title('WIP分布对比\n(MARL更均衡)', fontsize=12, fontweight='bold')
ax4.legend(fontsize=9)
ax4.grid(axis='y', alpha=0.3)

# 右中：通信开销
ax5 = fig.add_subplot(gs[1, 2])
comm_types = ['状态同步', '任务协调', '异常通知', '资源请求', '结果反馈']
marl_comm = [15, 8, 3, 5, 12]
centralized_comm = [50, 30, 15, 25, 40]
x_c = np.arange(len(comm_types))
ax5.bar(x_c - 0.15, marl_comm, 0.3, label='MARL', color='#4CAF50', alpha=0.8)
ax5.bar(x_c + 0.15, centralized_comm, 0.3, label='集中式', color='#FF9800', alpha=0.8)
ax5.set_xticks(x_c)
ax5.set_xticklabels(comm_types, fontsize=8, rotation=20)
ax5.set_ylabel('通信次数/小时', fontsize=10)
ax5.set_title('通信开销对比', fontsize=12, fontweight='bold')
ax5.legend(fontsize=9)
ax5.grid(axis='y', alpha=0.3)

# 底排：全厂KPI随训练改善
ax6 = fig.add_subplot(gs[2, :])
training_phases = np.arange(0, 200, 5)
throughput = 800 + 200*(1-np.exp(-training_phases/50)) + np.random.randn(len(training_phases))*10
yield_trend = 85 + 7*(1-np.exp(-training_phases/60)) + np.random.randn(len(training_phases))*0.5
utilization = 65 + 25*(1-np.exp(-training_phases/40)) + np.random.randn(len(training_phases))*1

ax6.plot(training_phases, throughput, color='#2196F3', linewidth=2.5, label='产出 (片/天)')
ax6_twin = ax6.twinx()
ax6_twin.plot(training_phases, yield_trend, color='#4CAF50', linewidth=2.5, label='良率 (%)')
ax6_twin.plot(training_phases, utilization, color='#FF9800', linewidth=2.5, linestyle='--', label='设备利用率 (%)')

# 标注阶段
ax6.axvspan(0, 30, alpha=0.05, color='#F44336')
ax6.axvspan(30, 80, alpha=0.05, color='#FF9800')
ax6.axvspan(80, 200, alpha=0.05, color='#4CAF50')
ax6.text(15, 950, '探索期', fontsize=10, color='#F44336', fontweight='bold')
ax6.text(45, 950, '收敛期', fontsize=10, color='#FF9800', fontweight='bold')
ax6.text(130, 950, '优化期', fontsize=10, color='#4CAF50', fontweight='bold')

ax6.set_xlabel('训练轮次', fontsize=11)
ax6.set_ylabel('产出 (片/天)', fontsize=11, color='#2196F3')
ax6_twin.set_ylabel('良率 / 利用率 (%)', fontsize=11, color='#4CAF50')
ax6.set_title('MARL全厂KPI随训练的改善趋势', fontsize=13, fontweight='bold')
lines1, labels1 = ax6.get_legend_handles_labels()
lines2, labels2 = ax6_twin.get_legend_handles_labels()
ax6.legend(lines1+lines2, labels1+labels2, fontsize=9, loc='lower right')
ax6.grid(alpha=0.3)

fig.suptitle('第16章 Demo：多智能体强化学习(MARL)在晶圆厂协同调度中的应用', 
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch16_marl.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch16 MARL demo saved.")
plt.close()
