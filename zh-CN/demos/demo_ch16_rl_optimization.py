"""
第16章 Demo: 强化学习驱动的DOE参数优化
模拟RL在工艺参数空间中搜索最优工艺窗口
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib import cm

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

fig = plt.figure(figsize=(18, 12))
gs = GridSpec(3, 3, figure=fig, hspace=0.4, wspace=0.3)

# 左上：参数空间与优化轨迹（等高线图）
ax1 = fig.add_subplot(gs[0:2, 0:2])

# 模拟良率响应面
x = np.linspace(0, 10, 100)
y = np.linspace(0, 10, 100)
X, Y = np.meshgrid(x, y)
Z = 90 + 8 * np.exp(-((X-7)**2 + (Y-6)**2) / 8) - 5 * np.exp(-((X-3)**2 + (Y-3)**2) / 3) + np.random.randn(100, 100) * 0.3

contour = ax1.contourf(X, Y, Z, levels=20, cmap='RdYlGn', alpha=0.7)
plt.colorbar(contour, ax=ax1, label='良率 (%)')
ax1.contour(X, Y, Z, levels=[92, 94, 96], colors=['blue', 'navy', 'black'], linewidths=1.5, linestyles='--')

# 模拟贝叶斯优化+RL的探索轨迹
# 初始随机探索
initial_points = np.array([[2, 3], [8, 2], [4, 7], [3, 5], [7, 4]])
# RL引导的探索轨迹
rl_trajectory_x = [3, 4, 5, 6, 6.5, 7, 7, 7]
rl_trajectory_y = [5, 5.5, 5.8, 6, 6, 6, 6, 6]

ax1.scatter(initial_points[:, 0], initial_points[:, 1], c='#FF6B6B', s=100, marker='x', linewidths=2, label='初始随机DOE实验', zorder=5)
ax1.plot(rl_trajectory_x, rl_trajectory_y, 'o-', color='#2196F3', markersize=8, linewidth=2, label='RL引导的参数搜索', zorder=5)
ax1.scatter([7], [6], c='#4CAF50', s=200, marker='*', zorder=6, label='最优参数点 (良率96.2%)')

ax1.annotate('最优区域\n良率>96%', xy=(7, 6), xytext=(8.5, 8),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5),
            fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
ax1.annotate('初始探索区域\n(效率低)', xy=(3, 3), xytext=(1, 1),
            arrowprops=dict(arrowstyle='->', color='#FF6B6B', lw=1.5),
            fontsize=9, color='#FF6B6B',
            bbox=dict(boxstyle='round', facecolor='#FFEBEE', alpha=0.9))

ax1.set_xlabel('RF功率 (W, 归一化)', fontsize=12)
ax1.set_ylabel('腔体压力 (mTorr, 归一化)', fontsize=12)
ax1.set_title('RL驱动的DOE参数空间搜索', fontsize=13, fontweight='bold')
ax1.legend(fontsize=9, loc='lower right')

# 右上：RL奖励曲线
ax2 = fig.add_subplot(gs[0, 2])
episodes = np.arange(1, 51)
random_reward = np.full(50, 88) + np.random.randn(50) * 2
rl_reward = 88 + 8 * (1 - np.exp(-episodes / 15)) + np.random.randn(50) * 1

ax2.plot(episodes, random_reward, color='#FF6B6B', linewidth=1.5, alpha=0.7, label='随机DOE')
ax2.plot(episodes, rl_reward, color='#4CAF50', linewidth=2.5, label='RL优化DOE')
ax2.fill_between(episodes, rl_reward - 1.5, rl_reward + 1.5, alpha=0.15, color='#4CAF50')
ax2.set_xlabel('实验轮次', fontsize=10)
ax2.set_ylabel('良率 (%)', fontsize=10)
ax2.set_title('RL优化收敛曲线', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(alpha=0.3)

# 中右：实验次数对比
ax3 = fig.add_subplot(gs[1, 2])
methods = ['全因子\nDOE', '部分因子\nDOE', '贝叶斯\n优化', 'RL+数字\n孪生']
experiments = [3125, 125, 28, 15]
colors_bar = ['#F44336', '#FF9800', '#2196F3', '#4CAF50']
bars = ax3.bar(methods, experiments, color=colors_bar, alpha=0.85, edgecolor='white')
for bar, val in zip(bars, experiments):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 30, f'{val}次', 
             ha='center', fontsize=10, fontweight='bold')
ax3.set_ylabel('所需实验次数', fontsize=11)
ax3.set_title('不同DOE方法的实验效率\n(5参数, 5水平)', fontsize=12, fontweight='bold')
ax3.set_yscale('log')
ax3.grid(axis='y', alpha=0.3)

# 底部左：R2R控制效果
ax4 = fig.add_subplot(gs[2, 0])
batches = np.arange(1, 101)
target = 100
ewma_adj = np.zeros(100)
rl_adj = np.zeros(100)
drift = 0.02 * batches + 0.5 * np.sin(batches / 10)

for i in range(1, 100):
    ewma_adj[i] = ewma_adj[i-1] * 0.8 + (drift[i] - drift[i-1]) * 0.2
    rl_adj[i] = rl_adj[i-1] * 0.9 + (drift[i] - drift[i-1]) * 0.45 + np.random.randn() * 0.1

ewma_output = target + drift - ewma_adj + np.random.randn(100) * 0.3
rl_output = target + drift - rl_adj + np.random.randn(100) * 0.2

ax4.plot(batches, ewma_output, color='#FF9800', linewidth=1.5, alpha=0.8, label='EWMA控制')
ax4.plot(batches, rl_output, color='#4CAF50', linewidth=1.5, alpha=0.8, label='RL控制')
ax4.axhline(y=target, color='gray', linestyle='--', alpha=0.5, label='目标值')
ax4.fill_between(batches, target-1, target+1, alpha=0.1, color='#4CAF50', label='控制限±1')
ax4.set_xlabel('批次', fontsize=10)
ax4.set_ylabel('量测值', fontsize=10)
ax4.set_title('R2R控制：EWMA vs RL\n(非线性漂移场景)', fontsize=12, fontweight='bold')
ax4.legend(fontsize=8)
ax4.grid(alpha=0.3)

# 底部中：多参数优化对比
ax5 = fig.add_subplot(gs[2, 1])
params = ['RF功率', '腔体压力', '温度', '气体流量', '时间']
ewma_improvement = [0.5, 0.3, 0.2, 0.1, 0.4]
rl_improvement = [2.8, 2.2, 1.5, 0.8, 2.0]
x_p = np.arange(len(params))
w = 0.35
ax5.bar(x_p - w/2, ewma_improvement, w, label='EWMA', color='#FF9800', alpha=0.8)
ax5.bar(x_p + w/2, rl_improvement, w, label='RL', color='#4CAF50', alpha=0.8)
ax5.set_xticks(x_p)
ax5.set_xticklabels(params, fontsize=9)
ax5.set_ylabel('良率改善 (%)', fontsize=10)
ax5.set_title('各参数的良率改善\nRL vs EWMA', fontsize=12, fontweight='bold')
ax5.legend(fontsize=9)
ax5.grid(axis='y', alpha=0.3)

# 底部右：RL策略决策可视化
ax6 = fig.add_subplot(gs[2, 2])
states = ['设备\n正常', '轻微\n漂移', '中度\n漂移', '严重\n漂移', 'PM后\n恢复']
actions_rl = ['微调\n+0.5%', '微调\n+1.5%', '调整\n+3%', '停机\nPM', '重校\n基准']
actions_ewma = ['微调\n+0.3%', '微调\n+0.5%', '微调\n+0.8%', '微调\n+1.2%', '微调\n+0.2%']
colors_state = ['#4CAF50', '#8BC34A', '#FF9800', '#F44336', '#2196F3']

for i, (state, action, color) in enumerate(zip(states, actions_rl, colors_state)):
    y = 4 - i
    ax6.barh(y, 1, color=color, alpha=0.7, edgecolor='white')
    ax6.text(0.5, y, f'{state} → {action}', ha='center', va='center', fontsize=8, fontweight='bold', color='white')

ax6.set_xlim(0, 1)
ax6.set_ylim(-0.5, 4.5)
ax6.set_title('RL策略：状态→行动\n决策映射', fontsize=12, fontweight='bold')
ax6.axis('off')

fig.suptitle('第16章 Demo：强化学习驱动的工艺参数优化与R2R控制 (行为主义)', 
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch16_rl_optimization.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch16 RL optimization demo saved.")
plt.close()
