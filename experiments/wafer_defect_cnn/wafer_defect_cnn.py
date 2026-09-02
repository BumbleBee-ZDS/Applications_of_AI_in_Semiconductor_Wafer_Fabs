"""
🔬 CNN 晶圆缺陷分类 / Wafer Defect Classification
对应第15章(连接主义) / Chapter 15 (Connectionism)

用 MLP 模拟 CNN 分类思想: 生成4类模拟晶圆图 -> 训练 -> 评估 -> 可视化
MLP stands in for a CNN (GPU-free): 4 wafer-map classes -> train -> evaluate -> visualize
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(15)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(OUT, exist_ok=True)

SIZE = 28
CLASSES = ['无缺陷\nnone', '中心缺陷\ncenter', '边缘环形\nedge-ring', '簇状缺陷\ncluster']

# ---------- 生成模拟晶圆图 / generate synthetic wafer maps ----------
def gen_wafer(kind, size=SIZE):
    """生成一种缺陷模式的晶圆图(圆形晶圆内) / generate one wafer map"""
    yy, xx = np.mgrid[0:size, 0:size]
    mask = (xx - size/2) ** 2 + (yy - size/2) ** 2 <= (size/2 - 1) ** 2  # 晶圆圆形区域
    img = np.zeros((size, size))
    cy = cx = size / 2
    if kind == 0:      # 无缺陷 none: 少量随机点
        for _ in range(8):
            img[np.random.randint(4, size-4), np.random.randint(4, size-4)] = 1
    elif kind == 1:    # 中心缺陷 center: 中心圆斑
        r = size * 0.18
        img[(xx-cx)**2 + (yy-cy)**2 < r**2] = 1
    elif kind == 2:    # 边缘环形 edge-ring: 环形
        r1, r2 = size*0.32, size*0.42
        ring = ((xx-cx)**2 + (yy-cy)**2 > r1**2) & ((xx-cx)**2 + (yy-cy)**2 < r2**2)
        img[ring] = 1
    else:              # 簇状缺陷 cluster: 2-3 个缺陷簇
        for _ in range(np.random.randint(2, 4)):
            px, py = np.random.uniform(size*0.25, size*0.75, 2)
            r = size * 0.08
            img[(xx-px)**2 + (yy-py)**2 < r**2] = 1
    return img * mask

N_PER_CLASS = 120
X, y = [], []
for kind in range(4):
    for _ in range(N_PER_CLASS):
        X.append(gen_wafer(kind).ravel())
        y.append(kind)
X = np.array(X) / 255.0 if X[0].max() > 1 else np.array(X)   # 归一化
y = np.array(y)

# 训练/测试划分 / train-test split
idx = np.random.permutation(len(X))
split = int(len(X) * 0.8)
X_train, X_test = X[idx[:split]], X[idx[split:]]
y_train, y_test = y[idx[:split]], y[idx[split:]]

print('=' * 60)
print('[数据] 生成晶圆图 / Wafer maps:', X.shape, ' 训练/测试:', len(X_train), '/', len(X_test))

# ---------- 训练 MLP(模拟CNN) / train MLP ----------
clf = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=300, random_state=15,
                    activation='relu', early_stopping=True)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f'[训练] 测试集准确率 / test accuracy = {acc:.3f}')

# ---------- 可视化1: 晶圆图样本 / wafer samples ----------
fig, axes = plt.subplots(4, 6, figsize=(9, 6))
for k in range(4):
    samples = X[y == k][:6]
    for j in range(6):
        axes[k, j].imshow(samples[j].reshape(SIZE, SIZE), cmap='Reds', interpolation='nearest')
        axes[k, j].axis('off')
        if j == 0:
            axes[k, j].set_title(CLASSES[k], fontsize=9)
fig.suptitle('晶圆图缺陷样本 / Wafer Defect Samples', fontsize=13, fontweight='bold')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'wafer_samples.png'), dpi=140)
plt.close(fig)

# ---------- 可视化2: 混淆矩阵 / confusion matrix ----------
cm = confusion_matrix(y_test, y_pred)
fig, ax = plt.subplots(figsize=(6.5, 5.5))
im = ax.imshow(cm, cmap='Blues')
ax.set_xticks(range(4)); ax.set_xticklabels(['none', 'center', 'edge', 'cluster'])
ax.set_yticks(range(4)); ax.set_yticklabels(['none', 'center', 'edge', 'cluster'])
ax.set_xlabel('预测 / predicted'); ax.set_ylabel('实际 / actual')
for i in range(4):
    for j in range(4):
        ax.text(j, i, cm[i, j], ha='center', va='center',
                color='white' if cm[i, j] > cm.max()/2 else 'black')
ax.set_title(f'混淆矩阵 Confusion Matrix (准确率 accuracy={acc:.3f})')
fig.colorbar(im)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'confusion_matrix.png'), dpi=140)
plt.close(fig)

print('[可视化] 图片输出于 / Figures saved to:', OUT)
print('[结论] 神经网络自动识别缺陷模式, 支撑 ADC 自动缺陷分类。')
print('  Takeaway: a neural net auto-classifies defect patterns, powering ADC.')
