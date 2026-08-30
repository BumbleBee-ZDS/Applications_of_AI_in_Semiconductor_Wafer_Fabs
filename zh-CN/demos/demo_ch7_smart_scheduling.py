"""
第7章 Demo: 智能派工系统对比
模拟传统FIFO派工 vs RL智能派工的调度效果
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

# 模拟8台设备、12个批次的调度
n_tools = 8
n_lots = 12
tool_names = [f'Tool-{chr(65+i)}0{i}' for i in range(n_tools)]
lot_names = [f'Lot-{1001+i}' for i in range(n_lots)]
product_types = ['Product-X', 'Product-Y', 'Product-Z']
lot_products = [np.random.choice(product_types) for _ in range(n_lots)]
product_colors = {'Product-X': '#2196F3', 'Product-Y': '#FF9800', 'Product-Z': '#4CAF50'}

# 传统FIFO调度
fifo_schedule = []
for i in range(n_lots):
    tool = i % n_tools
    start = max(0, i // n_tools * 4 + np.random.uniform(0, 1))
    duration = np.random.uniform(2.5, 4.5)
    fifo_schedule.append((tool, start, duration, i))

# RL智能调度（优化后：减少等待、平衡负载）
rl_schedule = []
tool_end_times = [0] * n_tools
# RL会优先将紧急批次分到最先可用的设备
lot_priorities = np.random.permutation(n_lots)
for lot_idx in lot_priorities:
    # RL选择最早可用的设备
    tool = np.argmin(tool_end_times)
    start = tool_end_times[tool]
    duration = np.random.uniform(2.0, 3.5)  # RL调度通常更高效
    rl_schedule.append((tool, start, duration, lot_idx))
    tool_end_times[tool] = start + duration

fig = plt.figure(figsize=(18, 12))
gs = GridSpec(3, 2, figure=fig, hspace=0.4, wspace=0.25)

# 左上：传统FIFO甘特图
ax1 = fig.add_subplot(gs[0, 0])
for tool_idx in range(n_tools):
    for sched in fifo_schedule:
        if sched[0] == tool_idx:
            _, start, dur, lot_idx = sched
            color = product_colors[lot_products[lot_idx]]
            ax1.barh(tool_idx, dur, left=start, height=0.6, color=color, alpha=0.8, edgecolor='white')
            ax1.text(start + dur/2, tool_idx, f'L{1001+lot_idx}', ha='center', va='center', fontsize=7, color='white', fontweight='bold')

ax1.set_yticks(range(n_tools))
ax1.set_yticklabels(tool_names, fontsize=9)
ax1.set_xlabel('时间 (小时)', fontsize=11)
ax1.set_title('传统FIFO派工调度', fontsize=13, fontweight='bold', color='#FF6B6B')
ax1.set_xlim(0, 20)
ax1.grid(axis='x', alpha=0.3)

# 右上：RL智能调度甘特图
ax2 = fig.add_subplot(gs[0, 1])
for tool_idx in range(n_tools):
    for sched in rl_schedule:
        if sched[0] == tool_idx:
            _, start, dur, lot_idx = sched
            color = product_colors[lot_products[lot_idx]]
            ax2.barh(tool_idx, dur, left=start, height=0.6, color=color, alpha=0.8, edgecolor='white')
            ax2.text(start + dur/2, tool_idx, f'L{1001+lot_idx}', ha='center', va='center', fontsize=7, color='white', fontweight='bold')

ax2.set_yticks(range(n_tools))
ax2.set_yticklabels(tool_names, fontsize=9)
ax2.set_xlabel('时间 (小时)', fontsize=11)
ax2.set_title('RL智能派工调度', fontsize=13, fontweight='bold', color='#4CAF50')
ax2.set_xlim(0, 20)
ax2.grid(axis='x', alpha=0.3)

# 图例
legend_patches = [mpatches.Patch(color=c, label=p, alpha=0.8) for p, c in product_colors.items()]
ax2.legend(handles=legend_patches, loc='lower right', fontsize=9)

# 左下：设备利用率对比
ax3 = fig.add_subplot(gs[1, 0])
fifo_util = np.random.uniform(55, 75, n_tools)
rl_util = np.random.uniform(75, 92, n_tools)
x = np.arange(n_tools)
w = 0.35
ax3.bar(x - w/2, fifo_util, w, label='FIFO调度', color='#FF6B6B', alpha=0.8)
ax3.bar(x + w/2, rl_util, w, label='RL调度', color='#4CAF50', alpha=0.8)
ax3.set_xticks(x)
ax3.set_xticklabels([f'T{i+1}' for i in range(n_tools)], fontsize=9)
ax3.set_ylabel('设备利用率 (%)', fontsize=11)
ax3.set_title('设备利用率对比', fontsize=13, fontweight='bold')
ax3.legend(fontsize=10)
ax3.grid(axis='y', alpha=0.3)

# 右下：关键KPI对比
ax4 = fig.add_subplot(gs[1, 1])
kpis = ['平均完工时间\n(h)', '设备利用率\n(%)', '交期达成率\n(%)', '瓶颈设备\n空闲时间(h)']
fifo_vals = [16.5, 65, 78, 4.2]
rl_vals = [12.8, 84, 92, 1.5]
x_kpi = np.arange(len(kpis))
ax4.bar(x_kpi - 0.2, fifo_vals, 0.4, label='FIFO', color='#FF6B6B', alpha=0.8)
ax4.bar(x_kpi + 0.2, rl_vals, 0.4, label='RL', color='#4CAF50', alpha=0.8)
for i, (fv, rv) in enumerate(zip(fifo_vals, rl_vals)):
    improvement = ((rv - fv) / fv * 100) if fv > 0 else 0
    if i in [0, 3]:  # 越低越好的指标
        improvement = -improvement
    ax4.text(i, max(fv, rv) + 2, f'{improvement:+.0f}%', ha='center', fontsize=9, fontweight='bold', color='#2196F3')
ax4.set_xticks(x_kpi)
ax4.set_xticklabels(kpis, fontsize=9)
ax4.set_title('关键绩效指标对比 (红色越低越好，绿色越高越好)', fontsize=12, fontweight='bold')
ax4.legend(fontsize=10)
ax4.grid(axis='y', alpha=0.3)

# 底部：RL训练过程（奖励曲线）
ax5 = fig.add_subplot(gs[2, :])
episodes = np.arange(1, 201)
fifo_reward = np.full(200, -15) + np.random.randn(200) * 2
rl_reward = -20 + 15 * (1 - np.exp(-episodes / 40)) + np.random.randn(200) * 1.5
ax5.fill_between(episodes, rl_reward - 2, rl_reward + 2, alpha=0.2, color='#4CAF50')
ax5.plot(episodes, rl_reward, color='#4CAF50', linewidth=2, label='RL策略平均奖励')
ax5.axhline(y=-15, color='#FF6B6B', linewidth=2, linestyle='--', label='FIFO基线奖励')
ax5.set_xlabel('训练轮次 (Episode)', fontsize=11)
ax5.set_ylabel('累积奖励', fontsize=11)
ax5.set_title('RL调度策略训练过程：累积奖励收敛曲线', fontsize=13, fontweight='bold')
ax5.legend(fontsize=10)
ax5.grid(alpha=0.3)

fig.suptitle('第7章 Demo：RL驱动的智能派工系统 vs 传统FIFO调度 (MFG)', 
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch7_smart_scheduling.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch7 smart scheduling demo saved.")
plt.close()
