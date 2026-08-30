"""
第6章 Demo: 晶圆图缺陷模式分类
模拟CNN对四种典型晶圆缺陷模式的识别与分类
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

np.random.seed(42)

def generate_wafer_map(defect_type, size=50):
    """生成模拟晶圆图，含特定缺陷模式"""
    wafer = np.zeros((size, size))
    cy, cx = size // 2, size // 2
    Y, X = np.ogrid[:size, :size]
    dist = np.sqrt((Y - cy)**2 + (X - cx)**2)
    wafer_mask = dist <= size * 0.45
    wafer[wafer_mask] = 0.3 + np.random.normal(0, 0.05, wafer[wafer_mask].shape)

    if defect_type == 'edge_ring':
        ring = (dist >= size * 0.35) & (dist <= size * 0.43)
        wafer[ring & wafer_mask] += 0.6 + np.random.normal(0, 0.1, ring[ring & wafer_mask].shape if hasattr(ring[ring & wafer_mask], 'shape') else 1)
        n_random = 30
    elif defect_type == 'center':
        center = dist <= size * 0.15
        wafer[center] += 0.7 + np.random.normal(0, 0.08, wafer[center].shape)
        n_random = 30
    elif defect_type == 'scratch':
        angle = np.random.uniform(0, np.pi)
        t = np.linspace(-size*0.4, size*0.4, 200)
        sy = (cy + t * np.sin(angle)).astype(int)
        sx = (cx + t * np.cos(angle)).astype(int)
        valid = (sy >= 0) & (sy < size) & (sx >= 0) & (sx < size)
        for y, x in zip(sy[valid], sx[valid]):
            if wafer_mask[y, x]:
                wafer[y, x] += 0.8
        n_random = 20
    elif defect_type == 'random':
        n_random = 200

    for _ in range(n_random):
        y, x = np.random.randint(0, size, 2)
        if wafer_mask[y, x]:
            wafer[y, x] += np.random.uniform(0.3, 0.6)

    return np.clip(wafer, 0, 1)

defect_types = ['edge_ring', 'center', 'scratch', 'random']
defect_names_cn = ['边缘环形缺陷', '中心聚集缺陷', '划痕缺陷', '随机散布缺陷']
defect_names_en = ['Edge Ring', 'Center', 'Scratch', 'Random']
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']

fig = plt.figure(figsize=(18, 10))
gs = GridSpec(2, 4, figure=fig, hspace=0.35, wspace=0.3)

# 上排：四种缺陷的晶圆图
for i, (dtype, name_cn, name_en, color) in enumerate(zip(defect_types, defect_names_cn, defect_names_en, colors)):
    ax = fig.add_subplot(gs[0, i])
    wafer = generate_wafer_map(dtype)
    im = ax.imshow(wafer, cmap='YlOrRd', interpolation='bilinear')
    ax.set_title(f'{name_cn}\n{name_en}', fontsize=12, fontweight='bold', color=color)
    ax.axis('off')
    circle = plt.Circle((25, 25), 23, fill=False, color='gray', linewidth=1.5, linestyle='--')
    ax.add_patch(circle)

# 下排左：分类置信度柱状图
ax_bar = fig.add_subplot(gs[1, 0:2])
categories = defect_names_cn
confidence_scores = np.array([
    [0.94, 0.03, 0.02, 0.01],
    [0.02, 0.91, 0.04, 0.03],
    [0.01, 0.03, 0.93, 0.03],
    [0.02, 0.02, 0.01, 0.95],
])
x = np.arange(len(categories))
width = 0.18
for i, (name, color) in enumerate(zip(defect_names_cn, colors)):
    bars = ax_bar.bar(x + i * width - 0.27, confidence_scores[i], width, label=f'输入: {name}', color=color, alpha=0.85)
    for bar, val in zip(bars, confidence_scores[i]):
        if val > 0.1:
            ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                       f'{val:.2f}', ha='center', va='bottom', fontsize=8)
ax_bar.set_xticks(x)
ax_bar.set_xticklabels(categories, fontsize=10)
ax_bar.set_ylabel('分类置信度', fontsize=11)
ax_bar.set_title('CNN分类器输出：缺陷类型置信度矩阵', fontsize=13, fontweight='bold')
ax_bar.legend(fontsize=8, loc='upper right')
ax_bar.set_ylim(0, 1.1)
ax_bar.grid(axis='y', alpha=0.3)

# 下排右：模拟训练曲线
ax_train = fig.add_subplot(gs[1, 2:4])
epochs = np.arange(1, 51)
train_acc = 1 - np.exp(-epochs / 8) - 0.02 * np.random.randn(50)
val_acc = 1 - np.exp(-epochs / 12) - 0.05 - 0.03 * np.random.randn(50)
train_loss = np.exp(-epochs / 10) + 0.05 + 0.02 * np.random.randn(50)
val_loss = np.exp(-epochs / 15) + 0.12 + 0.03 * np.random.randn(50)

ax_train2 = ax_train.twinx()
ax_train.plot(epochs, train_acc, color='#2196F3', linewidth=2, label='训练准确率')
ax_train.plot(epochs, val_acc, color='#FF6B6B', linewidth=2, linestyle='--', label='验证准确率')
ax_train2.plot(epochs, train_loss, color='#4CAF50', linewidth=2, alpha=0.7, label='训练损失')
ax_train2.plot(epochs, val_loss, color='#FF9800', linewidth=2, linestyle='--', alpha=0.7, label='验证损失')
ax_train.set_xlabel('训练轮次 (Epoch)', fontsize=11)
ax_train.set_ylabel('准确率', fontsize=11, color='#2196F3')
ax_train2.set_ylabel('损失值 (Loss)', fontsize=11, color='#4CAF50')
ax_train.set_title('晶圆图缺陷分类CNN模型训练曲线', fontsize=13, fontweight='bold')
lines1, labels1 = ax_train.get_legend_handles_labels()
lines2, labels2 = ax_train2.get_legend_handles_labels()
ax_train.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc='center right')
ax_train.grid(alpha=0.2)

fig.suptitle('第6章 Demo：AI驱动的晶圆图缺陷模式识别系统 (PID/YED)', 
             fontsize=16, fontweight='bold', y=0.98)
fig.text(0.5, 0.01, '模拟数据 | CNN架构: ResNet-18 | 输入: 50×50晶圆图 | 输出: 4类缺陷分类', 
         ha='center', fontsize=9, color='gray')

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch6_wafer_defect.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch6 wafer defect demo saved.")
plt.close()
