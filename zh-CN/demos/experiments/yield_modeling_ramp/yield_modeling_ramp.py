"""
🔬 良率模型与爬坡模拟 / Yield Modeling & Ramp Simulation
对应第9章(良率爬坡)与第11章(建设期/爬坡期)
Corresponds to Chapter 9 (Yield Ramp) & Chapter 11 (Construction/Ramp Phase)

Part 1: 良率统计模型对比  Yield model comparison (Poisson / Negative Binomial)
Part 2: S形爬坡曲线模拟  S-curve ramp simulation with learning rates
Part 3: 虚拟量测入门     Starter Virtual Metrology (VM)
"""
import os
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(OUT, exist_ok=True)

# ============================================================
# Part 1: 良率统计模型 / Yield statistical models
# ============================================================
def poisson_yield(D0, A):
    """Poisson 模型: Y = exp(-D0*A)。假设缺陷随机分布。"""
    return np.exp(-D0 * A)

def negative_binomial_yield(D0, A, alpha):
    """负二项式模型: Y = (1 + D0*A/alpha)^(-alpha)。
    alpha 越小, 缺陷聚集越严重, 良率越低。"""
    return (1 + D0 * A / alpha) ** (-alpha)

def murphy_yield(D0, A):
    """Murphy 模型(缺陷密度波动修正): Y = (1 - exp(-D0*A)) / (D0*A)"""
    x = D0 * A
    return (1 - np.exp(-x)) / x

# 固定芯片面积, 看良率随缺陷密度的变化
A = 1.0                      # 归一化芯片面积 chip area (arbitrary unit)
D0 = np.linspace(0.05, 2.0, 100)  # 缺陷密度 defect density

y_poisson = poisson_yield(D0, A)
y_nb_small = negative_binomial_yield(D0, A, alpha=2)   # 强聚集 heavily clustered
y_nb_large = negative_binomial_yield(D0, A, alpha=20)  # 弱聚集 mildly clustered
y_murphy = murphy_yield(D0, A)

fig, ax = plt.subplots(figsize=(7, 5))
ax.plot(D0, y_poisson, 'k-', lw=2, label='Poisson (随机分布 random)')
ax.plot(D0, y_nb_small, 'r--', lw=2, label='负二项式 NB, α=2 (强聚集 clustered)')
ax.plot(D0, y_nb_large, 'g--', lw=2, label='负二项式 NB, α=20 (弱聚集)')
ax.plot(D0, y_murphy, 'b:', lw=2, label='Murphy (密度波动修正)')
ax.set_xlabel('缺陷密度 D₀ (defects/area)')
ax.set_ylabel('良率 Yield Y')
ax.set_title('良率统计模型对比 / Yield Model Comparison\n(芯片面积 A=1)')
ax.legend(fontsize=8)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'yield_models.png'), dpi=150)
plt.close(fig)

print('=' * 60)
print('[Part 1] 良率模型对比 / Yield Model Comparison')
print(f'  D0=1.0, A=1.0 时: Poisson={y_poisson[-1]:.3f}, '
      f'NB(α=2)={y_nb_small[-1]:.3f}, NB(α=20)={y_nb_large[-1]:.3f}, '
      f'Murphy={y_murphy[-1]:.3f}')
print('  结论: 缺陷聚集越严重(α越小), 同一缺陷密度下良率越低。')
print('  Takeaway: more clustered defects -> lower yield at same D0.')

# ============================================================
# Part 2: 良率爬坡 S 曲线 / S-curve yield ramp
# ============================================================
def ramp_curve(t, y_start, y_max, k, t0):
    """Logistic 型爬坡曲线 / logistic ramp curve"""
    return y_max / (1 + (y_max / y_start - 1) * np.exp(-k * (t - t0)))

months = np.linspace(0, 24, 300)
y_fast = ramp_curve(months, 30, 93, 0.38, 8.5)   # 快学习率 fast learner
y_slow = ramp_curve(months, 30, 82, 0.22, 9.0)   # 慢学习率 slow learner

fig, ax = plt.subplots(figsize=(7, 5))
ax.plot(months, y_fast, 'b-', lw=2.5, label='快学习率 k=0.38 (fast)')
ax.plot(months, y_slow, 'r--', lw=2.5, label='慢学习率 k=0.22 (slow)')
ax.axhline(85, color='g', ls=':', lw=1.5)
ax.text(0.3, 86.5, '量产目标 85% / mass-production target', color='g', fontsize=10)
ax.axvspan(0, 9, color='orange', alpha=0.12)
ax.text(2, 36, '"死亡之谷"\n"Valley of Death"', color='#E65100', fontsize=10, fontweight='bold')
idx = np.argmin(np.abs(y_fast - 85))
ax.plot(months[idx], y_fast[idx], 'o', color='g', ms=7)
ax.annotate(f'{months[idx]:.0f}个月达85% months to 85%', xy=(months[idx], y_fast[idx]),
            xytext=(months[idx]-5, 60), fontsize=9,
            arrowprops=dict(arrowstyle='->', color='g'))
ax.set_xlabel('投产时间 投产月份 months')
ax.set_ylabel('良率 Yield (%)')
ax.set_title('良率爬坡 S 曲线 / Yield Ramp S-Curve')
ax.legend(loc='lower right', fontsize=9)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'ramp_curves.png'), dpi=150)
plt.close(fig)

print('\n[Part 2] 爬坡曲线 / Ramp Curves')
print(f'  快学习率达到85%所需时间: {months[idx]:.0f}个月; 慢学习率24个月仍未达标。')
print('  结论: 学习速率直接决定爬坡周期与成本(每片实验晶圆>4000美元)。')

# ============================================================
# Part 3: 虚拟量测入门 / Starter Virtual Metrology
# ============================================================
# 模拟: 用FDC信号(温度/压力/RF功率)预测膜厚量测值
# Simulate: predict film thickness from FDC signals (temp/pressure/RF power)
n = 200
temp = np.random.uniform(380, 420, n)        # 腔体温度 chamber temperature
pressure = np.random.uniform(2.0, 6.0, n)    # 腔体压力 chamber pressure
rf = np.random.uniform(800, 1200, n)         # RF功率 RF power

# 真实关系: 膜厚与温度正相关, 与RF负相关 + 噪声
thickness_true = 180 + 0.25 * (temp - 400) - 0.08 * (rf - 1000) \
                 + 0.5 * (pressure - 4.0) + np.random.normal(0, 1.5, n)

X = np.column_stack([temp, pressure, rf])
# 最小二乘线性回归 / ordinary least squares
Xb = np.column_stack([np.ones(n), X])
beta, *_ = np.linalg.lstsq(Xb, thickness_true, rcond=None)
thickness_pred = Xb @ beta

# 免检决策: 预测误差在阈值内则免检 / skip-inspection decision
err = np.abs(thickness_pred - thickness_true)
skip = err < 3.0
skip_rate = skip.mean()

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
axes[0].scatter(thickness_true, thickness_pred, s=12, alpha=0.6)
lim = [thickness_true.min(), thickness_true.max()]
axes[0].plot(lim, lim, 'r--', lw=1.5, label='y=x 理想线')
axes[0].set_xlabel('实际量测值 actual (nm)')
axes[0].set_ylabel('虚拟量测预测 predicted (nm)')
axes[0].set_title('虚拟量测预测 vs 实际 / VM Prediction vs Actual')
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].hist(err, bins=30, color='steelblue', edgecolor='white')
axes[1].axvline(3.0, color='r', ls='--', lw=1.5)
axes[1].text(3.2, axes[1].get_ylim()[1]*0.9, '免检阈值 3nm\nskip threshold', fontsize=9, color='r')
axes[1].set_xlabel('预测误差 |error| (nm)')
axes[1].set_ylabel('批次数量 # batches')
axes[1].set_title(f'预测误差分布 / Error Distribution (免检率 skip rate={skip_rate:.0%})')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'virtual_metrology.png'), dpi=150)
plt.close(fig)

print('\n[Part 3] 虚拟量测 / Virtual Metrology')
print(f'  线性模型预测膜厚, RMSE={np.sqrt((err**2).mean()):.2f} nm')
print(f'  免检率 skip-inspection rate = {skip_rate:.0%}  (误差<3nm 可免检)')
print('  结论: 虚拟量测用FDC信号替代实际量测, 释放量测设备产能。')
print('  Takeaway: VM frees metrology capacity via FDC-signal prediction.')

print('\n全部完成 / Done. 图片输出于 / Figures saved to:', OUT)
