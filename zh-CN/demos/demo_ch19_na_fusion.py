"""
第19章 Demo: NA融合——深度学习感知+强化学习决策的端到端优化
展示Neural+Action在晶圆厂三大部门的应用
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHeI', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

fig = plt.figure(figsize=(20, 14))
gs = GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# ========== 左上: 端到端感知-决策架构 ==========
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.set_title('NA融合：端到端感知-决策架构', fontsize=12, fontweight='bold', color='#2196F3')

# 感知层 (Neural)
stages_perception = [
    (1, 8, '晶圆图像\n(CNN)', '#2196F3'),
    (3.5, 8, '传感器\n时序(LSTM)', '#2196F3'),
    (6, 8, 'MES数据\n(MLP)', '#2196F3'),
]
for x, y, label, color in stages_perception:
    box = FancyBboxPatch((x-0.8, y-0.6), 1.6, 1.2, boxstyle='round,pad=0.1',
                         facecolor=color, alpha=0.3, edgecolor=color, linewidth=2)
    ax1.add_patch(box)
    ax1.text(x, y, label, ha='center', va='center', fontsize=8, fontweight='bold')

# 融合层
box_fuse = FancyBboxPatch((2.5, 5), 5, 1.2, boxstyle='round,pad=0.1',
                           facecolor='#9C27B0', alpha=0.2, edgecolor='#9C27B0', linewidth=2)
ax1.add_patch(box_fuse)
ax1.text(5, 5.6, '特征融合层 (Concat + Attention)', ha='center', va='center', fontsize=9, fontweight='bold', color='#9C27B0')

# 决策层 (Action/RL)
stages_action = [
    (1.5, 2, 'RL Agent\n(PPO)', '#FF9800'),
    (5, 2, '策略网络\n输出动作', '#FF9800'),
    (8.5, 2, '环境反馈\nReward', '#FF9800'),
]
for x, y, label, color in stages_action:
    box = FancyBboxPatch((x-0.8, y-0.6), 1.6, 1.2, boxstyle='round,pad=0.1',
                         facecolor=color, alpha=0.3, edgecolor=color, linewidth=2)
    ax1.add_patch(box)
    ax1.text(x, y, label, ha='center', va='center', fontsize=8, fontweight='bold')

# 箭头连接
for x, _, _, _ in stages_perception:
    ax1.annotate('', xy=(x, 6.2), xytext=(x, 7.2),
                arrowprops=dict(arrowstyle='->', color='#2196F3', lw=1.5))
ax1.annotate('', xy=(5, 6.2), xytext=(5, 5.8),
            arrowprops=dict(arrowstyle='->', color='#9C27B0', lw=2))
for x, _, _, _ in stages_action:
    ax1.annotate('', xy=(x, 3.2), xytext=(x, 4.8),
                arrowprops=dict(arrowstyle='->', color='#FF9800', lw=1.5))

# 反馈循环
ax1.annotate('', xy=(8.5, 8), xytext=(8.5, 3),
            arrowprops=dict(arrowstyle='->', color='#F44336', lw=2,
                          connectionstyle='arc3,rad=-0.3'))
ax1.text(9.2, 5.5, '反馈\n循环', ha='center', va='center', fontsize=8, color='#F44336', fontweight='bold')

# 标签
ax1.text(0.2, 8, 'Neural\n(感知)', fontsize=10, fontweight='bold', color='#2196F3', va='center')
ax1.text(0.2, 2, 'Action\n(决策)', fontsize=10, fontweight='bold', color='#FF9800', va='center')

ax1.axis('off')

# ========== 中上: RL训练曲线 ==========
ax2 = fig.add_subplot(gs[0, 1])
episodes = np.arange(0, 500)
# 模拟RL训练过程
reward_perception = -50 + 0.15 * episodes + 20 * np.sin(episodes * 0.05) + np.random.randn(500) * 3
reward_perception = np.clip(reward_perception, -60, 30)
reward_na = -50 + 0.25 * episodes * (1 - np.exp(-episodes / 100)) + np.random.randn(500) * 2
reward_na = np.clip(reward_na, -60, 50)

# 移动平均
window = 20
reward_na_smooth = np.convolve(reward_na, np.ones(window)/window, mode='valid')
reward_pure_rl = -50 + 0.12 * episodes + 15 * np.sin(episodes * 0.03) + np.random.randn(500) * 4
reward_pure_rl_smooth = np.convolve(reward_pure_rl, np.ones(window)/window, mode='valid')

ax2.plot(episodes[window-1:], reward_na_smooth, color='#9C27B0', linewidth=2.5, label='NA融合 (感知增强RL)')
ax2.plot(episodes[window-1:], reward_pure_rl_smooth, color='#FF9800', linewidth=2, linestyle='--', label='纯RL (无感知)')
ax2.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
ax2.fill_between(episodes[window-1:], reward_na_smooth, reward_pure_rl_smooth,
                  where=reward_na_smooth > reward_pure_rl_smooth,
                  alpha=0.2, color='#9C27B0', label='NA优势区间')
ax2.set_xlabel('训练回合', fontsize=10)
ax2.set_ylabel('累计奖励', fontsize=10)
ax2.set_title('RL训练收敛对比：NA融合 vs 纯RL', fontsize=11, fontweight='bold')
ax2.legend(fontsize=9, loc='lower right')
ax2.grid(alpha=0.3)

# ========== 右上: 三部门应用雷达图 ==========
ax3 = fig.add_subplot(gs[0, 2], polar=True)
categories = ['感知精度', '决策速度', '适应性', '收敛速度', '可解释性', '部署难度\n(越低越好)']
N = len(categories)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]

na_data = [0.92, 0.85, 0.88, 0.82, 0.45, 0.65]
pure_rl = [0.60, 0.80, 0.75, 0.55, 0.30, 0.75]
pure_dl = [0.90, 0.70, 0.50, 0.90, 0.25, 0.55]
na_data += na_data[:1]
pure_rl += pure_rl[:1]
pure_dl += pure_dl[:1]

ax3.plot(angles, na_data, 'o-', linewidth=2, color='#9C27B0', label='NA融合')
ax3.fill(angles, na_data, alpha=0.2, color='#9C27B0')
ax3.plot(angles, pure_rl, 's--', linewidth=1.5, color='#FF9800', label='纯RL')
ax3.fill(angles, pure_rl, alpha=0.1, color='#FF9800')
ax3.plot(angles, pure_dl, '^--', linewidth=1.5, color='#2196F3', label='纯DL')
ax3.fill(angles, pure_dl, alpha=0.1, color='#2196F3')
ax3.set_xticks(angles[:-1])
ax3.set_xticklabels(categories, fontsize=8)
ax3.set_title('NA融合 vs 纯RL vs 纯DL\n能力对比', fontsize=11, fontweight='bold', pad=20)
ax3.legend(fontsize=8, loc='upper right', bbox_to_anchor=(1.3, 1.1))

# ========== 左中: PID/YED应用——良率优化 ==========
ax4 = fig.add_subplot(gs[1, 0])
# 模拟DOE参数空间搜索过程
np.random.seed(123)
param_space = np.random.randn(200, 2) * 2
param_space[:, 0] = param_space[:, 0] * 5 + 25  # 温度 20-30
param_space[:, 1] = param_space[:, 1] * 3 + 15  # 压力 12-18
yield_values = 80 + 5 * np.exp(-((param_space[:, 0]-22)**2 + (param_space[:, 1]-14)**2) / 8) + np.random.randn(200) * 2

# RL搜索轨迹
rl_path_x = [28, 26, 24, 22.5, 22, 21.8, 22, 22.1, 22]
rl_path_y = [17, 16, 15, 14.2, 14, 14.1, 13.9, 14, 14]

scatter = ax4.scatter(param_space[:, 0], param_space[:, 1], c=yield_values, cmap='RdYlGn',
                       s=30, alpha=0.6, edgecolors='gray', linewidths=0.3)
ax4.plot(rl_path_x, rl_path_y, 'o-', color='#9C27B0', linewidth=2, markersize=6,
         markerfacecolor='white', markeredgecolor='#9C27B0', markeredgewidth=2, label='RL搜索路径')
ax4.plot(22, 14, '*', color='red', markersize=20, label='最优解')
ax4.set_xlabel('温度 (C)', fontsize=10)
ax4.set_ylabel('压力 (Pa)', fontsize=10)
ax4.set_title('PID/YED: NA融合的DOE参数空间搜索\n(CNN感知+RL决策)', fontsize=11, fontweight='bold')
ax4.legend(fontsize=9, loc='upper right')
plt.colorbar(scatter, ax=ax4, label='良率(%)', shrink=0.8)

# ========== 中中: MFG应用——智能派工对比 ==========
ax5 = fig.add_subplot(gs[1, 1])
time_steps = np.arange(0, 24)
# FIFO派工
fifo_wip = 200 + 30 * np.sin(time_steps * 0.3) + np.random.randn(24) * 10
fifo_wip = np.clip(fifo_wip, 150, 280)
# NA融合派工
na_wip = 180 + 15 * np.sin(time_steps * 0.3) + np.random.randn(24) * 5
na_wip = np.clip(na_wip, 150, 220)

ax5.fill_between(time_steps, fifo_wip, na_wip, alpha=0.15, color='#F44336')
ax5.plot(time_steps, fifo_wip, 'o-', color='#F44336', linewidth=2, markersize=4, label='FIFO派工')
ax5.plot(time_steps, na_wip, 's-', color='#9C27B0', linewidth=2, markersize=4, label='NA融合派工')
ax5.axhline(y=200, color='gray', linestyle=':', alpha=0.5, label='目标WIP')
ax5.set_xlabel('时间 (h)', fontsize=10)
ax5.set_ylabel('WIP数量', fontsize=10)
ax5.set_title('MFG: WIP波动对比\n(感知预测+RL动态派工)', fontsize=11, fontweight='bold')
ax5.legend(fontsize=9)
ax5.grid(alpha=0.3)

# ========== 右中: PE/EE应用——设备自适应控制 ==========
ax6 = fig.add_subplot(gs[1, 2])
time_fine = np.linspace(0, 100, 500)
# 设备参数漂移
drift = 0.05 * time_fine + 0.3 * np.sin(time_fine * 0.15)
# 传统R2R控制 (周期性校正)
r2r_control = drift.copy()
for i in range(10, 500, 50):
    r2r_control[i:i+50] -= r2r_control[i] * 0.6
# NA融合控制 (连续自适应)
na_control = drift.copy()
na_control = na_control * 0.3 + 0.05 * np.sin(time_fine * 0.2) * 0.3

ax6.plot(time_fine, drift, color='#F44336', linewidth=2, label='无控制(参数漂移)', alpha=0.7)
ax6.plot(time_fine, r2r_control, color='#FF9800', linewidth=2, label='传统R2R控制', alpha=0.8)
ax6.plot(time_fine, na_control, color='#9C27B0', linewidth=2.5, label='NA融合控制')
ax6.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
ax6.fill_between(time_fine, r2r_control, na_control, alpha=0.1, color='#9C27B0')
ax6.set_xlabel('批次序号', fontsize=10)
ax6.set_ylabel('参数偏差', fontsize=10)
ax6.set_title('PE/EE: 设备参数漂移控制对比\n(LSTM感知+RL自适应)', fontsize=11, fontweight='bold')
ax6.legend(fontsize=9)
ax6.grid(alpha=0.3)

# ========== 底部: 三部门NA融合效果汇总 ==========
ax7 = fig.add_subplot(gs[2, :])
departments = ['PID/YED\n良率优化', 'PID/YED\nDOE搜索', 'MFG\nWIP管理', 'MFG\n派工效率',
               'PE/EE\n参数控制', 'PE/EE\n预测维护']
traditional_vals = [82, 75, 65, 70, 72, 68]
na_vals = [94, 91, 88, 92, 95, 89]

x = np.arange(len(departments))
w = 0.35
bars1 = ax7.bar(x - w/2, traditional_vals, w, label='传统方法', color='#FF6B6B', alpha=0.8)
bars2 = ax7.bar(x + w/2, na_vals, w, label='NA融合', color='#9C27B0', alpha=0.8)

for i in range(len(departments)):
    improvement = na_vals[i] - traditional_vals[i]
    ax7.text(i, max(traditional_vals[i], na_vals[i]) + 2, f'+{improvement}pp',
             ha='center', fontsize=10, fontweight='bold', color='#2196F3')

ax7.set_xticks(x)
ax7.set_xticklabels(departments, fontsize=10)
ax7.set_ylabel('性能指标 (%, 越高越好)', fontsize=11)
ax7.set_title('NA融合在晶圆厂三大部门的量化效果汇总', fontsize=13, fontweight='bold')
ax7.legend(fontsize=11, loc='upper left')
ax7.set_ylim(0, 110)
ax7.grid(axis='y', alpha=0.3)

fig.suptitle('第19章 Demo：NA融合（Neural+Action）——深度学习感知 + 强化学习决策的端到端优化',
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch19_na_fusion.png',
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch19 NA fusion demo saved.")
plt.close()
