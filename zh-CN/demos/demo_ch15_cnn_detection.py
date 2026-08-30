"""
第15章 Demo: 深度学习缺陷检测可视化
模拟CNN在晶圆缺陷检测中的特征提取与分类过程
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

fig = plt.figure(figsize=(18, 10))
gs = GridSpec(2, 5, figure=fig, hspace=0.35, wspace=0.3)

# 模拟输入晶圆图
size = 50
cy, cx = 25, 25
Y, X = np.ogrid[:size, :size]
dist = np.sqrt((Y-cy)**2 + (X-cx)**2)
mask = dist <= 22
wafer = np.zeros((size, size))
wafer[mask] = 0.3 + np.random.normal(0, 0.05, mask.sum())
ring = (dist >= 16) & (dist <= 21) & mask
wafer[ring] += 0.5 + np.random.normal(0, 0.08, ring.sum())
for _ in range(25):
    y, x = np.random.randint(0, size, 2)
    if mask[y, x]:
        wafer[y, x] += np.random.uniform(0.3, 0.6)
wafer = np.clip(wafer, 0, 1)

# 原始输入
ax0 = fig.add_subplot(gs[0, 0])
ax0.imshow(wafer, cmap='hot', interpolation='bilinear')
ax0.set_title('输入：原始晶圆图\n(50×50像素)', fontsize=11, fontweight='bold')
ax0.axis('off')

# 模拟CNN各层特征图
conv_layers = [
    ('Conv1 - 边缘特征', 6, 'viridis'),
    ('Conv2 - 纹理特征', 8, 'plasma'),
    ('Conv3 - 缺陷模式', 4, 'inferno'),
    ('Conv4 - 高级特征', 4, 'magma'),
]

for layer_idx, (layer_name, n_features, cmap) in enumerate(conv_layers):
    ax = fig.add_subplot(gs[0, layer_idx + 1])
    feature_map = np.random.rand(10, 10)
    if layer_name == 'Conv3 - 缺陷模式':
        feature_map[3:7, 3:7] = np.random.rand(4, 4) * 0.8 + 0.4
    ax.imshow(feature_map, cmap=cmap, interpolation='bilinear')
    ax.set_title(layer_name, fontsize=10, fontweight='bold')
    ax.set_xticks([])
    ax.set_yticks([])

# 下排左：特征图热力图（多个滤波器）
ax5 = fig.add_subplot(gs[1, 0:2])
n_filters = 16
filter_results = np.zeros((4, 4))
for i in range(4):
    for j in range(4):
        filter_results[i, j] = np.random.beta(2, 5)
filter_results[1, 1] = 0.92  # 最激活的滤波器
filter_results[1, 2] = 0.85
filter_results[2, 1] = 0.78

im = ax5.imshow(filter_results, cmap='YlOrRd', interpolation='nearest', vmin=0, vmax=1)
ax5.set_title('Conv2层16个滤波器的激活强度\n(高亮滤波器对边缘环形模式最敏感)', fontsize=11, fontweight='bold')
for i in range(4):
    for j in range(4):
        ax5.text(j, i, f'{filter_results[i,j]:.2f}', ha='center', va='center', fontsize=9,
                color='white' if filter_results[i,j] > 0.5 else 'black')
plt.colorbar(im, ax=ax5, label='激活强度', fraction=0.046)

# 下排右：分类结果概率分布
ax6 = fig.add_subplot(gs[1, 2:4])
classes = ['边缘环形\n缺陷', '中心聚集\n缺陷', '划痕\n缺陷', '随机\n散布', '正常\n(无缺陷)']
probabilities = np.array([0.94, 0.02, 0.01, 0.02, 0.01])
colors_prob = ['#F44336', '#FF9800', '#2196F3', '#9C27B0', '#4CAF50']

bars = ax6.barh(classes, probabilities, color=colors_prob, alpha=0.85, edgecolor='white')
for bar, prob in zip(bars, probabilities):
    ax6.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
             f'{prob:.1%}', va='center', fontsize=11, fontweight='bold')

ax6.set_xlabel('分类概率', fontsize=12)
ax6.set_title('CNN分类器输出：缺陷类型概率分布\n(置信度: 94%)', fontsize=12, fontweight='bold')
ax6.set_xlim(0, 1.15)
ax6.axvline(x=0.5, color='gray', linestyle='--', alpha=0.5, label='决策阈值')
ax6.legend(fontsize=9)
ax6.grid(axis='x', alpha=0.3)

fig.suptitle('第15章 Demo：CNN驱动的晶圆缺陷检测与特征可视化 (连接主义)', 
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch15_cnn_detection.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch15 CNN detection demo saved.")
plt.close()
