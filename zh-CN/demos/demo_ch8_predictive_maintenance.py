"""
第8章 Demo: 设备预测性维护与RUL预测
模拟LSTM预测设备剩余使用寿命(RUL)及设备退化趋势
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

# 模拟设备退化数据（RF匹配器阻抗漂移）
n_cycles = 500
time = np.arange(n_cycles)

# 真实退化曲线（非线性，带噪声）
true_degradation = 100 * (1 - np.exp(-time / 200)) + 0.02 * time**1.2 / 100
true_degradation = true_degradation / true_degradation[-1] * 100
noise = np.random.normal(0, 1.5, n_cycles)
observed = true_degradation + noise

# 模拟LSTM预测（在t=350时开始预测）
predict_start = 350
history_time = time[:predict_start]
history_obs = observed[:predict_start]
future_time = time[predict_start:]
true_future = true_degradation[predict_start:]

# LSTM预测值和置信区间
lstm_pred = true_future + np.random.normal(0, 2, len(future_time))
lstm_upper = lstm_pred + 3 + np.arange(len(future_time)) * 0.05
lstm_lower = lstm_pred - 3 - np.arange(len(future_time)) * 0.05

# 传统方法（线性外推）的预测
from_time = history_obs[-50:]
linear_slope = np.polyfit(np.arange(50), from_time, 1)[0]
linear_pred = history_obs[-1] + linear_slope * np.arange(1, len(future_time) + 1)

# 阈值线
failure_threshold = 85
predicted_rul = predict_start + np.where(lstm_pred >= failure_threshold)[0][0] if np.any(lstm_pred >= failure_threshold) else n_cycles
actual_rul = np.where(true_degradation >= failure_threshold)[0][0] if np.any(true_degradation >= failure_threshold) else n_cycles
linear_rul = predict_start + np.where(linear_pred >= failure_threshold)[0][0] if np.any(linear_pred >= failure_threshold) else n_cycles

fig = plt.figure(figsize=(18, 12))
gs = GridSpec(3, 3, figure=fig, hspace=0.4, wspace=0.3)

# 左上（跨2列）：设备退化曲线与RUL预测
ax1 = fig.add_subplot(gs[0, 0:2])
ax1.fill_between(future_time, lstm_lower, lstm_upper, alpha=0.2, color='#2196F3', label='LSTM 95%置信区间')
ax1.plot(history_time, history_obs, color='#333', linewidth=1.5, label='历史观测数据', alpha=0.8)
ax1.plot(future_time, true_future, color='#4CAF50', linewidth=2, linestyle='-', label='真实退化曲线', alpha=0.8)
ax1.plot(future_time, lstm_pred, color='#2196F3', linewidth=2.5, linestyle='--', label='LSTM预测')
ax1.plot(future_time, linear_pred, color='#FF6B6B', linewidth=2, linestyle=':', label='线性外推（传统方法）')
ax1.axhline(y=failure_threshold, color='#F44336', linewidth=2, linestyle='--', alpha=0.7, label=f'故障阈值 ({failure_threshold}%)')

# 标注预测RUL
ax1.axvline(x=predict_start, color='gray', linewidth=1, linestyle='--', alpha=0.5)
ax1.annotate(f'预测起始点\n(t={predict_start})', xy=(predict_start, 50), fontsize=9, ha='center',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
ax1.annotate(f'LSTM预测RUL:\n{predicted_rul - predict_start} 批次', 
            xy=(predicted_rul, failure_threshold), xytext=(predicted_rul+20, failure_threshold-15),
            arrowprops=dict(arrowstyle='->', color='#2196F3', lw=1.5),
            fontsize=9, color='#2196F3', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#E3F2FD', alpha=0.9))
ax1.annotate(f'实际RUL:\n{actual_rul - predict_start} 批次', 
            xy=(actual_rul, failure_threshold), xytext=(actual_rul-80, failure_threshold+10),
            arrowprops=dict(arrowstyle='->', color='#4CAF50', lw=1.5),
            fontsize=9, color='#4CAF50', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#E8F5E9', alpha=0.9))

ax1.set_xlabel('运行批次', fontsize=11)
ax1.set_ylabel('设备退化程度 (%)', fontsize=11)
ax1.set_title('设备退化曲线与RUL预测（RF匹配器阻抗漂移）', fontsize=13, fontweight='bold')
ax1.legend(fontsize=8, loc='upper left')
ax1.set_xlim(0, n_cycles)
ax1.set_ylim(0, 105)
ax1.grid(alpha=0.3)

# 右上：FDC信号时序（模拟异常检测）
ax2 = fig.add_subplot(gs[0, 2])
t_fdc = np.linspace(0, 10, 500)
normal_signal = np.sin(2 * np.pi * t_fdc) * 10 + np.random.randn(500) * 0.5
abnormal_start = 400
abnormal_signal = normal_signal.copy()
abnormal_signal[abnormal_start:] += np.sin(2 * np.pi * 12 * t_fdc[abnormal_start:]) * 3 + np.linspace(0, 5, 100)

ax2.plot(t_fdc[:abnormal_start], normal_signal[:abnormal_start], color='#4CAF50', linewidth=1, label='正常信号')
ax2.plot(t_fdc[abnormal_start-1:], abnormal_signal[abnormal_start-1:], color='#F44336', linewidth=1.5, label='异常信号（振荡）')
ax2.axvline(x=t_fdc[abnormal_start], color='#FF9800', linewidth=2, linestyle='--', alpha=0.7)
ax2.annotate('LSTM检测到异常', xy=(t_fdc[abnormal_start], 0), fontsize=8, color='#FF9800',
            bbox=dict(boxstyle='round', facecolor='#FFF3E0', alpha=0.9))
ax2.set_xlabel('时间 (s)', fontsize=10)
ax2.set_ylabel('RF功率信号', fontsize=10)
ax2.set_title('FDC信号异常检测', fontsize=12, fontweight='bold')
ax2.legend(fontsize=8)
ax2.grid(alpha=0.3)

# 中左：预测误差对比
ax3 = fig.add_subplot(gs[1, 0])
lstm_error = np.abs(lstm_pred - true_future)
linear_error = np.abs(linear_pred - true_future)
ax3.plot(future_time, lstm_error, color='#2196F3', linewidth=2, label='LSTM预测误差')
ax3.plot(future_time, linear_error, color='#FF6B6B', linewidth=2, label='线性外推误差')
ax3.set_xlabel('运行批次', fontsize=10)
ax3.set_ylabel('绝对误差', fontsize=10)
ax3.set_title('预测误差对比', fontsize=12, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(alpha=0.3)

# 中中：RUL预测对比柱状图
ax4 = fig.add_subplot(gs[1, 1])
methods = ['真实RUL', 'LSTM\n预测', '线性外推\n预测', '固定周期\nPM']
rul_vals = [actual_rul - predict_start, predicted_rul - predict_start, 
            linear_rul - predict_start, 100]  # 固定周期假设
colors_bar = ['#4CAF50', '#2196F3', '#FF6B6B', '#FF9800']
bars = ax4.bar(methods, rul_vals, color=colors_bar, alpha=0.85, edgecolor='white')
for bar, val in zip(bars, rul_vals):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val}', 
             ha='center', fontsize=10, fontweight='bold')
ax4.set_ylabel('预测RUL（批次）', fontsize=11)
ax4.set_title('RUL预测方法对比', fontsize=12, fontweight='bold')
ax4.grid(axis='y', alpha=0.3)

# 中右：维护决策矩阵
ax5 = fig.add_subplot(gs[1, 2])
risk_levels = ['低风险\n(RUL>100)', '中风险\n(50<RUL<100)', '高风险\n(RUL<50)']
actions = ['继续运行\n+持续监测', '计划PM\n(7天内)', '紧急PM\n(立即)']
risk_matrix = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
])
risk_colors = ['#4CAF50', '#FF9800', '#F44336']
for i, (risk, color) in enumerate(zip(risk_levels, risk_colors)):
    ax5.barh(i, 1, color=color, alpha=0.7)
    ax5.text(0.5, i, actions[i], ha='center', va='center', fontsize=9, fontweight='bold', color='white')
ax5.set_yticks(range(3))
ax5.set_yticklabels(risk_levels, fontsize=9)
ax5.set_xlim(0, 1)
ax5.set_title('基于RUL的维护决策矩阵', fontsize=12, fontweight='bold')
ax5.axis('off')

# 底部：PM优化效果对比
ax6 = fig.add_subplot(gs[2, :])
metrics = ['MTBF\n(平均故障间隔)', 'MTTR\n(平均修复时间)', '设备可用率\n(%)', '非计划停机\n(小时/月)', '备件成本\n(万元/月)']
fixed_pm = [200, 4.5, 92, 12, 8.5]
pred_pm = [320, 3.2, 97, 4, 5.2]
x_m = np.arange(len(metrics))
w = 0.35
bars1 = ax6.bar(x_m - w/2, fixed_pm, w, label='固定周期PM', color='#FF6B6B', alpha=0.8)
bars2 = ax6.bar(x_m + w/2, pred_pm, w, label='预测性PM', color='#4CAF50', alpha=0.8)
for bars in [bars1, bars2]:
    for bar in bars:
        ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                f'{bar.get_height():.1f}', ha='center', fontsize=8)
ax6.set_xticks(x_m)
ax6.set_xticklabels(metrics, fontsize=10)
ax6.set_title('预测性维护 vs 固定周期PM：关键指标对比', fontsize=13, fontweight='bold')
ax6.legend(fontsize=10)
ax6.grid(axis='y', alpha=0.3)

fig.suptitle('第8章 Demo：LSTM驱动的设备预测性维护系统 (PE/EE)', 
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch8_predictive_maintenance.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch8 predictive maintenance demo saved.")
plt.close()
