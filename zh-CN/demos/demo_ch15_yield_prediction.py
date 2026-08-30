"""
第15章 Demo: 良率预测模型与虚拟量测
展示深度学习在良率预测中的应用
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from sklearn.linear_model import LinearRegression

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

fig = plt.figure(figsize=(18, 12))
gs = GridSpec(3, 3, figure=fig, hspace=0.4, wspace=0.3)

# 模拟数据
n_samples = 200
n_features = 8
feature_names = ['RF功率', '腔体压力', '温度', '气体流量', '时间', '上步CD', '上步厚度', '设备ID']
X = np.random.randn(n_samples, n_features)
true_weights = np.random.randn(n_features) * 0.5
y = 85 + X @ true_weights + np.random.randn(n_samples) * 2
y = np.clip(y, 70, 99)

# 左上：特征重要性
ax1 = fig.add_subplot(gs[0, 0])
importance = np.abs(true_weights) / np.sum(np.abs(true_weights))
sorted_idx = np.argsort(importance)
ax1.barh(range(n_features), importance[sorted_idx], color='#2196F3', alpha=0.8)
ax1.set_yticks(range(n_features))
ax1.set_yticklabels([feature_names[i] for i in sorted_idx], fontsize=9)
ax1.set_xlabel('特征重要性', fontsize=10)
ax1.set_title('良率影响因素排序', fontsize=12, fontweight='bold')
ax1.grid(axis='x', alpha=0.3)

# 中上：良率预测散点图
ax2 = fig.add_subplot(gs[0, 1])
# 模拟预测
train_size = 150
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]
lr = LinearRegression()
lr.fit(X_train, y_train)
y_pred_lr = lr.predict(X_test)
# 模拟DNN预测（更准确）
y_pred_dnn = y_test + np.random.randn(len(y_test)) * 0.8

ax2.scatter(y_test, y_pred_lr, color='#FF9800', alpha=0.6, label=f'线性回归 (R2=0.78)')
ax2.scatter(y_test, y_pred_dnn, color='#2196F3', alpha=0.6, label=f'DNN (R2=0.94)')
ax2.plot([75, 98], [75, 98], 'k--', alpha=0.5, label='理想预测线')
ax2.set_xlabel('真实良率 (%)', fontsize=10)
ax2.set_ylabel('预测良率 (%)', fontsize=10)
ax2.set_title('良率预测：真实vs预测', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(alpha=0.3)

# 右上：残差分布
ax3 = fig.add_subplot(gs[0, 2])
residual_lr = y_test - y_pred_lr
residual_dnn = y_test - y_pred_dnn
ax3.hist(residual_lr, bins=15, alpha=0.5, color='#FF9800', label=f'线性回归 (MAE={np.mean(np.abs(residual_lr)):.2f})')
ax3.hist(residual_dnn, bins=15, alpha=0.5, color='#2196F3', label=f'DNN (MAE={np.mean(np.abs(residual_dnn)):.2f})')
ax3.set_xlabel('预测残差', fontsize=10)
ax3.set_ylabel('频次', fontsize=10)
ax3.set_title('预测残差分布', fontsize=12, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(alpha=0.3)

# 左中：虚拟量测 vs 实际量测
ax4 = fig.add_subplot(gs[1, 0])
n_wafers = 30
vm_pred = np.cumsum(np.random.randn(n_wafers) * 0.5) + 50
actual = vm_pred + np.random.randn(n_wafers) * 0.3
ax4.plot(range(n_wafers), actual, 'o-', color='#333', linewidth=1.5, markersize=5, label='实际量测')
ax4.plot(range(n_wafers), vm_pred, 's--', color='#FF5722', linewidth=1.5, markersize=5, label='虚拟量测(VM)')
ax4.fill_between(range(n_wafers), vm_pred-1.5, vm_pred+1.5, alpha=0.2, color='#FF5722')
ax4.set_xlabel('晶圆编号', fontsize=10)
ax4.set_ylabel('CD值 (nm)', fontsize=10)
ax4.set_title('虚拟量测 vs 实际量测', fontsize=12, fontweight='bold')
ax4.legend(fontsize=9)
ax4.grid(alpha=0.3)

# 中中：VM采样策略
ax5 = fig.add_subplot(gs[1, 1])
sampling_rates = [10, 30, 50, 70, 100]  # 采样率%
vm_accuracy = [88, 93, 96, 97, 98]
cost_saving = [90, 75, 55, 35, 0]
ax5_twin = ax5.twinx()
ax5.plot(sampling_rates, vm_accuracy, 'o-', color='#2196F3', linewidth=2, label='VM准确率')
ax5_twin.plot(sampling_rates, cost_saving, 's--', color='#4CAF50', linewidth=2, label='成本节省%')
ax5.set_xlabel('实际采样率 (%)', fontsize=10)
ax5.set_ylabel('VM准确率 (%)', fontsize=10, color='#2196F3')
ax5_twin.set_ylabel('成本节省 (%)', fontsize=10, color='#4CAF50')
ax5.set_title('VM采样策略：准确率vs成本', fontsize=12, fontweight='bold')
lines1, labels1 = ax5.get_legend_handles_labels()
lines2, labels2 = ax5_twin.get_legend_handles_labels()
ax5.legend(lines1+lines2, labels1+labels2, fontsize=8, loc='center right')
ax5.grid(alpha=0.3)

# 右中：模型训练曲线对比
ax6 = fig.add_subplot(gs[1, 2])
epochs = np.arange(1, 101)
# DNN
dnn_train = 1 - np.exp(-epochs/15) + np.random.randn(100)*0.01
dnn_val = 1 - np.exp(-epochs/20) - 0.03 + np.random.randn(100)*0.015
# Linear
lr_train = np.full(100, 0.78) + np.random.randn(100)*0.01
lr_val = np.full(100, 0.76) + np.random.randn(100)*0.01

ax6.plot(epochs, dnn_train, color='#2196F3', linewidth=2, label='DNN训练')
ax6.plot(epochs, dnn_val, color='#2196F3', linewidth=2, linestyle='--', label='DNN验证')
ax6.plot(epochs, lr_train, color='#FF9800', linewidth=1.5, alpha=0.7, label='线性回归训练')
ax6.plot(epochs, lr_val, color='#FF9800', linewidth=1.5, linestyle='--', alpha=0.7, label='线性回归验证')
ax6.set_xlabel('训练轮次', fontsize=10)
ax6.set_ylabel('R2 Score', fontsize=10)
ax6.set_title('模型训练曲线对比', fontsize=12, fontweight='bold')
ax6.legend(fontsize=8)
ax6.grid(alpha=0.3)

# 底排：多步良率预测趋势
ax7 = fig.add_subplot(gs[2, :])
weeks = np.arange(1, 21)
actual_yield = 88 + np.cumsum(np.random.randn(20) * 0.3) + np.sin(weeks/3) * 1.5
predicted_yield = np.roll(actual_yield, 2) + np.random.randn(20) * 0.5
predicted_yield[:2] = actual_yield[:2]
confidence_upper = predicted_yield + 1.5 + np.linspace(0, 3, 20)
confidence_lower = predicted_yield - 1.5 - np.linspace(0, 3, 20)

ax7.fill_between(weeks, confidence_lower, confidence_upper, alpha=0.15, color='#2196F3', label='95%置信区间')
ax7.plot(weeks[:12], actual_yield[:12], 'o-', color='#333', linewidth=2, markersize=6, label='历史良率')
ax7.plot(weeks[11:], actual_yield[11:], 'o-', color='#333', linewidth=2, markersize=6, alpha=0.3)
ax7.plot(weeks[11:], predicted_yield[11:], 's--', color='#2196F3', linewidth=2, markersize=6, label='预测良率')
ax7.axvline(x=12, color='gray', linestyle=':', alpha=0.5)
ax7.text(12.5, max(actual_yield)+1, '预测区间', fontsize=10, color='#2196F3', fontweight='bold')
ax7.set_xlabel('周次', fontsize=11)
ax7.set_ylabel('良率 (%)', fontsize=11)
ax7.set_title('多步良率预测：基于LSTM的8周良率趋势预测', fontsize=13, fontweight='bold')
ax7.legend(fontsize=9)
ax7.grid(alpha=0.3)

fig.suptitle('第15章 Demo：深度学习驱动的良率预测与虚拟量测系统', 
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch15_yield_prediction.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch15 yield prediction demo saved.")
plt.close()
