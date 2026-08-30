"""
第9章 Demo: 良率爬坡曲线模拟
模拟典型先进制程的S形良率爬坡曲线与学习速率对比
"""
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6.5))

# ============ 左图: S形良率爬坡曲线 ============
def s_curve(t, y_start, y_max, k, t0):
    """logistic 曲线模拟良率爬坡"""
    return y_max / (1 + (y_max / y_start - 1) * np.exp(-k * (t - t0)))

months = np.linspace(0, 24, 200)

# 快学习速率: 12-18个月达到85%
y_fast = s_curve(months, 30, 93, 0.38, 8.5)
# 慢学习速率: 24个月仍未达标
y_slow = s_curve(months, 30, 82, 0.22, 9.0)

ax1.plot(months, y_fast, color='#2196F3', lw=2.5, label='快学习速率 (学习率 0.38)')
ax1.plot(months, y_slow, color='#F44336', lw=2.5, ls='--', label='慢学习速率 (学习率 0.22)')

# 量产目标线
ax1.axhline(85, color='#4CAF50', lw=1.8, ls=':')
ax1.text(0.3, 86.5, '量产目标 85%', color='#4CAF50', fontsize=11, fontweight='bold')

# 死亡之谷区域
ax1.axvspan(0, 9, color='#FF9800', alpha=0.12)
ax1.text(2.2, 36, '"死亡之谷"\n(良率 30%-60%)', color='#E65100', fontsize=11, fontweight='bold')

# 关键节点标注
idx = np.argmin(np.abs(y_fast - 85))
ax1.plot(months[idx], y_fast[idx], 'o', color='#4CAF50', ms=8)
ax1.annotate(f'快学习率: {months[idx]:.0f}个月达85%', xy=(months[idx], y_fast[idx]),
             xytext=(months[idx]-4.5, 60), fontsize=10,
             arrowprops=dict(arrowstyle='->', color='#4CAF50', lw=1.5))
idx2 = np.argmin(np.abs(y_slow - 85))
ax1.plot(months[idx2], y_slow[idx2], 'o', color='#F44336', ms=8)
ax1.annotate(f'慢学习率: 24个月仍未达标', xy=(months[idx2], y_slow[idx2]),
             xytext=(months[idx2]-6.5, 42), fontsize=10,
             arrowprops=dict(arrowstyle='->', color='#F44336', lw=1.5))

ax1.set_xlabel('投产时间（月）', fontsize=12)
ax1.set_ylabel('良率（%）', fontsize=12)
ax1.set_xlim(0, 24)
ax1.set_ylim(20, 100)
ax1.set_title('典型先进制程良率爬坡曲线（S形）', fontsize=13, fontweight='bold')
ax1.legend(loc='lower right', fontsize=10)
ax1.grid(alpha=0.3)

# ============ 右图: 良率学习曲线(双对数) ============
wafers = np.logspace(2, 4, 100)  # 累计实验晶圆数 100~10000
y_learn_fast = 30 + 38 * np.log10(wafers / 100)   # 学习率 38 点/十进
y_learn_slow = 30 + 22 * np.log10(wafers / 100)   # 学习率 22 点/十进
y_learn_fast = np.clip(y_learn_fast, 30, 95)
y_learn_slow = np.clip(y_learn_slow, 30, 85)

ax2.plot(wafers, y_learn_fast, color='#2196F3', lw=2.5, label='快学习速率')
ax2.plot(wafers, y_learn_slow, color='#F44336', lw=2.5, ls='--', label='慢学习速率')
ax2.axhline(85, color='#4CAF50', lw=1.5, ls=':')
ax2.text(120, 87, '85% 目标', color='#4CAF50', fontsize=11, fontweight='bold')

ax2.set_xscale('log')
ax2.set_xlabel('累计实验晶圆数（片）', fontsize=12)
ax2.set_ylabel('良率（%）', fontsize=12)
ax2.set_xlim(100, 10000)
ax2.set_ylim(20, 100)
ax2.set_title('良率学习曲线（双对数坐标系）\n斜率 = 良率学习率', fontsize=13, fontweight='bold')
ax2.legend(loc='lower right', fontsize=10)
ax2.grid(alpha=0.3, which='both')

# 注释: 每片12寸晶圆成本 >4000美元
ax2.text(0.45, 0.06,
         '注: 每片12英寸实验晶圆成本超过4000美元\n学习速率直接决定爬坡成本',
         transform=ax2.transAxes, fontsize=10, color='#555',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

plt.tight_layout()
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch9_yield_ramp.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Demo Ch9 Yield Ramp saved.')
