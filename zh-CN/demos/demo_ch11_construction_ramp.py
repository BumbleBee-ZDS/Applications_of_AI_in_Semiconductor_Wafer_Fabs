"""
第11章 Demo: 建设期与爬坡期三大任务
良率分析 + 虚拟量测 + 缺陷检测(新类发现)
"""
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(11)

fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))

# ============ 左: 良率分析——晶圆图缺陷模式 ============
ax = axes[0]
y, x = np.mgrid[0:100, 0:100]
wafer = np.zeros((100, 100))
# 中心 + 边缘环形缺陷
cx, cy, r1, r2 = 50, 50, 38, 42
ring = ((x-cx)**2 + (y-cy)**2) > r1**2
ring &= ((x-cx)**2 + (y-cy)**2) < r2**2
wafer[ring] = 1
# 随机颗粒缺陷
for _ in range(60):
    xi, yi = np.random.randint(5, 95, 2)
    if (xi-50)**2 + (yi-50)**2 < 45**2:
        wafer[yi, xi] = 1
# 晶圆边界(圆形)
circle = (x-50)**2 + (y-50)**2 <= 49**2
ax.imshow(np.ma.masked_where(~circle, wafer), cmap='Reds', interpolation='nearest')
ax.set_xlim(0, 100); ax.set_ylim(100, 0)
ax.set_title('良率分析: 晶圆图模式\n(边缘环形+随机颗粒)', fontsize=11, fontweight='bold')
ax.set_xticks([]); ax.set_yticks([])

# ============ 中: 虚拟量测——预测 vs 实际 ============
ax = axes[1]
n = 40
actual = 100 + np.random.normal(0, 2.2, n)
pred = actual + np.random.normal(0, 1.2, n)
lots = np.arange(n)
ax.plot(lots, actual, 'o-', color='#2196F3', lw=1.5, ms=4, label='实际量测值')
ax.plot(lots, pred, 's--', color='#FF9800', lw=1.2, ms=3.5, label='虚拟量测预测值')
ax.fill_between(lots, pred - 2.5, pred + 2.5, color='#FF9800', alpha=0.15, label='预测置信区间')
ax.axvline(20, color='#999', ls=':', lw=1.2)
ax.text(20.5, 104.5, '免检/抽检决策区', fontsize=9, color='#555')
ax.set_title('虚拟量测: FDC信号预测量测结果\n(建设期: 每片晶圆都有量测数据)', fontsize=11, fontweight='bold')
ax.set_xlabel('批次序号', fontsize=10)
ax.set_ylabel('膜厚量测值 (nm)', fontsize=10)
ax.legend(fontsize=8, loc='lower left')
ax.grid(alpha=0.3)

# ============ 右: 缺陷检测——新缺陷类发现 ============
ax = axes[2]
from sklearn.datasets import make_blobs
X, _ = make_blobs(n_samples=300, centers=3, cluster_std=0.55, random_state=7)
X_new, _ = make_blobs(n_samples=60, centers=1, cluster_std=0.35, random_state=3)
X_new = X_new + np.array([4.5, -2.0])
ax.scatter(X[:, 0], X[:, 1], c='#90CAF9', s=28, alpha=0.8, label='已知缺陷类型(ADC分类)')
ax.scatter(X_new[:, 0], X_new[:, 1], c='#F44336', s=40, marker='*', label='未知缺陷(新类发现)')
ax.set_title('缺陷检测: 新缺陷类发现\n(建设期AI先于工程师发现未知缺陷)', fontsize=11, fontweight='bold')
ax.set_xlabel('特征1 (尺寸)', fontsize=10)
ax.set_ylabel('特征2 (形貌)', fontsize=10)
ax.legend(fontsize=8.5, loc='upper left')
ax.grid(alpha=0.3)

plt.suptitle('第11章 Demo: 建设期与爬坡期三大任务——良率分析 / 虚拟量测 / 缺陷检测', fontsize=13, fontweight='bold', y=1.0)
plt.tight_layout()
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch11_construction_ramp.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Demo Ch11 Construction Ramp saved.')
