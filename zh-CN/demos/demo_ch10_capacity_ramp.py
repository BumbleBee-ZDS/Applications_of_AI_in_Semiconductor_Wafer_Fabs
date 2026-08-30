"""
第10章 Demo: 产能爬坡与产能规划
模拟晶圆厂产能爬坡曲线与瓶颈转移过程
"""
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(7)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6.5))

# ============ 左图: 产能爬坡曲线 ============
months = np.linspace(0, 24, 200)
design_cap = 30000  # 设计产能 3万片/月

def capacity_ramp(t):
    """模拟产能爬坡: 设备到位→通线→分阶段放行→满产"""
    base = design_cap * (1 / (1 + np.exp(-0.32 * (t - 10))))
    # 通线阶段引入的延迟波动
    return base * (1 + 0.03 * np.sin(t / 2.2))

out = capacity_ramp(months)
ax1.plot(months, out, color='#4CAF50', lw=2.5, label='实际产出（Wafer Out）')
ax1.axhline(design_cap, color='#F44336', lw=1.8, ls=':')
ax1.text(0.3, design_cap + 800, '设计产能 30000 片/月', color='#F44336', fontsize=11, fontweight='bold')

# 阶段划分
ax1.axvspan(0, 4, color='#9E9E9E', alpha=0.15)
ax1.axvspan(4, 12, color='#FF9800', alpha=0.12)
ax1.axvspan(12, 24, color='#2196F3', alpha=0.10)
ax1.text(1.2, 3000, '设备安装\n与通线验证', color='#555', fontsize=10, fontweight='bold')
ax1.text(6.2, 8000, '分阶段放行\n(良率未稳时控速)', color='#E65100', fontsize=10, fontweight='bold')
ax1.text(15.5, 14000, '满产与\n稳定运营', color='#0D47A1', fontsize=10, fontweight='bold')

idx = np.argmin(np.abs(out - design_cap * 0.9))
ax1.plot(months[idx], out[idx], 'o', color='#4CAF50', ms=8)
ax1.annotate(f'{months[idx]:.0f}个月达到90%产能', xy=(months[idx], out[idx]),
             xytext=(months[idx]-6.5, 20000), fontsize=10,
             arrowprops=dict(arrowstyle='->', color='#4CAF50', lw=1.5))

ax1.set_xlabel('投产时间（月）', fontsize=12)
ax1.set_ylabel('月度产出（片/月）', fontsize=12)
ax1.set_xlim(0, 24)
ax1.set_ylim(0, 34000)
ax1.set_title('晶圆厂产能爬坡曲线', fontsize=13, fontweight='bold')
ax1.legend(loc='lower right', fontsize=10)
ax1.grid(alpha=0.3)

# ============ 右图: 瓶颈转移示意 ============
tools = ['EUV光刻', '高精度量测', '先进刻蚀', 'CMP抛光', '薄膜沉积']
phases = np.arange(5)
util = np.array([98, 96, 93, 88, 84])   # 各阶段瓶颈利用率
colors = ['#F44336', '#FF9800', '#FFC107', '#4CAF50', '#2196F3']

bars = ax2.bar(phases, util, color=colors, alpha=0.9, width=0.6)
ax2.axhline(95, color='#F44336', lw=1.5, ls='--')
ax2.text(3.8, 96.5, '瓶颈线 95%', color='#F44336', fontsize=10, fontweight='bold')

for i, (t, u) in enumerate(zip(tools, util)):
    ax2.text(i, u + 1.5, f'{u:.0f}%', ha='center', fontsize=11, fontweight='bold')

ax2.text(-0.55, 76, '爬坡初期\n(瓶颈)', color='#F44336', fontsize=10, fontweight='bold',
         ha='center', bbox=dict(boxstyle='round', facecolor='#FFEBEE', alpha=0.9))
ax2.text(3.45, 76, '爬坡后期\n(已缓解)', color='#2196F3', fontsize=10, fontweight='bold',
         ha='center', bbox=dict(boxstyle='round', facecolor='#E3F2FD', alpha=0.9))

ax2.set_xticks(phases)
ax2.set_xticklabels(tools, fontsize=11)
ax2.set_ylabel('设备产能利用率（%）', fontsize=12)
ax2.set_ylim(0, 110)
ax2.set_title('产能爬坡中的瓶颈转移\n(产能爬坡 = 系统性瓶颈管理)', fontsize=13, fontweight='bold')
ax2.grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch10_capacity_ramp.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Demo Ch10 Capacity Ramp saved.')
