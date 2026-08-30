"""
第12章 Demo: 成熟量产期三大任务
智能排程 + 预测性维护 + 能源管理
"""
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(12)

fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))

# ============ 左: 智能排程——RL vs FIFO 甘特图对比 ============
ax = axes[0]
machines = 4
np.random.seed(5)
rl_jobs = [(np.random.randint(0, 4), np.random.uniform(2, 5)) for _ in range(14)]
# 简化: 直接画两条甘特条带对比循环时间
t_rl = np.cumsum(np.random.uniform(2.0, 3.2, 14))
t_fifo = t_rl * np.random.uniform(1.25, 1.45, 14)
ax.plot(np.arange(14), t_rl, 'o-', color='#4CAF50', lw=1.8, label='RL智能排程(循环时间)')
ax.plot(np.arange(14), t_fifo, 's--', color='#F44336', lw=1.5, label='FIFO传统调度(循环时间)')
ax.set_title('智能排程: RL vs FIFO\n(成熟期多品种混合生产)', fontsize=11, fontweight='bold')
ax.set_xlabel('批次序号', fontsize=10)
ax.set_ylabel('累计循环时间 (h)', fontsize=10)
ax.legend(fontsize=8.5)
ax.grid(alpha=0.3)

# ============ 中: 预测性维护——RUL 曲线 ============
ax = axes[1]
t = np.linspace(0, 100, 200)
healthy = 10 + 2*np.sin(t/8) + np.random.normal(0, 0.3, 200)
degraded = healthy.copy()
degraded[100:] = degraded[100:] + np.maximum(t[100:]-70, 0)**1.8 / 30
thresh = 26
ax.plot(t, degraded, color='#2196F3', lw=1.8, label='设备健康特征(振动/RF功率)')
ax.axhline(thresh, color='#F44336', ls=':', lw=1.5)
ax.text(2, thresh+0.8, '失效阈值', color='#F44336', fontsize=9, fontweight='bold')
ax.axvspan(88, 100, color='#FF9800', alpha=0.2)
ax.text(89.5, 14, '预测维护窗口\n(RUL≈12)', fontsize=9, color='#E65100', fontweight='bold')
ax.set_title('预测性维护: RUL预测\n(提前预警, 避免非计划停机)', fontsize=11, fontweight='bold')
ax.set_xlabel('运行时间 (天)', fontsize=10)
ax.set_ylabel('健康特征值', fontsize=10)
ax.legend(fontsize=8.5, loc='upper left')
ax.grid(alpha=0.3)

# ============ 右: 能源管理——峰谷错峰 ============
ax = axes[2]
hours = np.arange(24)
base = 45 + 15*np.sin((hours-6)/24*2*np.pi)
price = 0.6 + 0.5*np.exp(-((hours-15)**2)/18)  # 下午高峰电价
ax.plot(hours, base, 'o-', color='#9C27B0', lw=1.8, label='原始能耗曲线')
opt = base.copy()
opt[9:16] = opt[9:16] * 0.88   # 高峰时段错峰降低
opt[22:6] = opt[22:6] * 1.05   # 低谷时段利用
ax.plot(hours, opt, 's--', color='#4CAF50', lw=1.5, label='错峰优化后能耗')
ax2 = ax.twinx()
ax2.plot(hours, price, color='#F44336', lw=1.2, alpha=0.7, label='电价')
ax2.set_ylabel('电价 (元/kWh)', fontsize=9, color='#F44336')
ax.set_title('能源管理: 错峰生产优化\n(高电价时段降低负载)', fontsize=11, fontweight='bold')
ax.set_xlabel('时刻 (h)', fontsize=10)
ax.set_ylabel('功耗 (MW)', fontsize=10)
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1+lines2, labels1+labels2, fontsize=8, loc='lower right')
ax.grid(alpha=0.3)

plt.suptitle('第12章 Demo: 成熟量产期三大任务——智能排程 / 预测性维护 / 能源管理', fontsize=13, fontweight='bold', y=1.0)
plt.tight_layout()
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch12_mature_ops.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Demo Ch12 Mature Ops saved.')
