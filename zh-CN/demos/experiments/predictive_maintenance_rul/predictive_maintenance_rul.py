"""
🔬 预测性维护 RUL 实验 / Predictive Maintenance RUL
对应第12章(成熟量产期·预测性维护)
Corresponds to Chapter 12 (Mature Mass Production · Predictive Maintenance)

Part 1: 合成退化数据与 RUL 预测  Degradation data & RUL prediction
Part 2: 维护策略成本对比        Maintenance strategy cost comparison
"""
import os
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(7)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(OUT, exist_ok=True)

# ============================================================
# Part 1: 合成退化数据 / Synthetic degradation data
# ============================================================
N = 300                          # 运行天数 operating days
t = np.arange(N)
# 健康特征: 基线 + 缓慢退化 + 噪声 / health feature: baseline + drift + noise
baseline = 10.0
drift = 0.0016 * t ** 1.9        # 加速退化 accelerated degradation
noise = np.random.normal(0, 0.35, N)
health = baseline + drift + noise
threshold = 26.0                 # 失效阈值 failure threshold

# 失效点(首次越过阈值)/ failure point (first crossing)
fail_idx = np.argmax(health >= threshold)
print('=' * 60)
print('[Part 1] 退化数据 / Degradation Data')
print(f'  设备在第 {fail_idx} 天越过失效阈值 {threshold} (实际RUL=0)')
print(f'  Equipment crosses failure threshold {threshold} at day {fail_idx}.')

# 用失效前 80% 生命周期的数据拟合退化模型, 在设备仍健康时外推预测 RUL
# fit the degradation model on the first 80% of lifetime (while still healthy),
# then extrapolate to predict RUL BEFORE failure
train_n = min(200, int(fail_idx * 0.8))
y = health[:train_n] - baseline     # 退化增量 degradation increment
x = t[:train_n].astype(float)
# 幂律拟合: y = a * x^b  ->  log(y) = log(a) + b*log(x)
# 注意 x 从 1 开始(避免 log(0)); y 过小值截断
# fit power law on x>=1 to avoid log(0); clip tiny y
mask = x >= 1
logy = np.log(np.clip(y[mask], 1e-3, None))
logx = np.log(x[mask])
b, loga = np.polyfit(logx, logy, 1)
a = np.exp(loga)
pred_drift = a * t ** b
pred_health = baseline + pred_drift
pred_fail = np.argmax(pred_health >= threshold)
pred_rul = pred_fail - train_n

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(t, health, 'b-', lw=1.2, alpha=0.8, label='实际健康特征 actual')
ax.plot(t, pred_health, 'r--', lw=2, label=f'拟合外推 fitted (a={a:.4f}, b={b:.2f})')
ax.axhline(threshold, color='k', ls=':', lw=1.5)
ax.text(2, threshold + 0.6, f'失效阈值 {threshold}', fontsize=10)
ax.axvline(train_n, color='gray', ls='--', lw=1.2)
ax.text(train_n + 1, 15, f'预测点 day {train_n}\n(预测RUL≈{pred_rul}天)', fontsize=9)
ax.axvspan(fail_idx, N, color='red', alpha=0.1, label='实际故障区间 actual failure zone')
ax.set_xlabel('运行天数 operating days')
ax.set_ylabel('健康特征值 health feature')
ax.set_title('设备退化与 RUL 预测 / Degradation & RUL Prediction')
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'degradation.png'), dpi=150)
plt.close(fig)

print(f'  在第 {train_n} 天预测剩余寿命 RUL ≈ {pred_rul} 天 (实际 {fail_idx - train_n} 天)')
print('  结论: 提前预警, 在设备故障前安排维护, 避免非计划停机。')

# ============================================================
# Part 2: 维护策略成本对比 / Maintenance strategy cost comparison
# ============================================================
# 假设: 计划停机损失 5 万/次; 非计划故障停机损失 50 万/次; 每30天定期PM
# Assume: planned downtime cost 50k; unplanned failure cost 500k; PM every 30 days
planned_cost = 5        # 万元 10k CNY
failure_cost = 50       # 万元
pm_interval = 30        # 定期PM间隔 days

# 策略A: 定期PM (每30天停一次, 不管是否健康)
# Strategy A: periodic PM every 30 days
a_pm_count = N // pm_interval
a_cost = a_pm_count * planned_cost

# 策略B: 预测性维护 (在第train_n天预测到RUL, 在RUL-5天安排计划停机)
# Strategy B: predictive — schedule planned maintenance before predicted failure
b_pm_time = pred_fail - 5      # 提前5天安排 planned 5 days before predicted failure
b_cost = 1 * planned_cost      # 只安排1次计划停机 one planned stop
# 预测有误差: 若计划时间晚于实际故障, 仍发生非计划故障
if b_pm_time >= fail_idx:
    b_cost += failure_cost     # 预测失误导致非计划停机 missed prediction -> failure

# 策略C: 不维护 (直到故障) / Strategy C: no maintenance until failure
c_cost = (N // 150) * failure_cost   # 每150天故障一次 fail every ~150 days

strategies = ['定期PM\nperiodic', '预测性维护\npredictive', '不维护\nnone']
costs = [a_cost, b_cost, c_cost]

fig, ax = plt.subplots(figsize=(7, 4.5))
bars = ax.bar(strategies, costs, color=['#2196F3', '#4CAF50', '#F44336'], alpha=0.9)
for bar, c in zip(bars, costs):
    ax.text(bar.get_x() + bar.get_width()/2, c + 0.5, f'{c:.0f}万', ha='center', fontweight='bold')
ax.set_ylabel('维护总成本 (万元) total cost (10k CNY)')
ax.set_title(f'维护策略成本对比 / Maintenance Strategy Cost (运行{N}天, {N} days)')
ax.grid(alpha=0.3, axis='y')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'cost_comparison.png'), dpi=150)
plt.close(fig)

print('\n[Part 2] 维护策略对比 / Maintenance Strategy Comparison')
print(f'  定期PM: {a_cost}万 (频繁停机浪费)  periodic: frequent stops waste capacity')
print(f'  预测性维护: {b_cost}万 (按需停机, 最优)  predictive: on-demand, optimal')
print(f'  不维护: {c_cost}万 (非计划停机代价高昂)  none: unplanned failures cost most')
best = strategies[np.argmin(costs)]
print(f'  结论: 最优策略为 {best} —— 数据驱动的维护时机决策。')
print('  Takeaway: data-driven maintenance timing minimizes total cost.')

print('\n全部完成 / Done. 图片输出于 / Figures saved to:', OUT)
