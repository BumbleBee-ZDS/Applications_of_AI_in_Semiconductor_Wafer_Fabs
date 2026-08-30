"""
第2章 Demo: AI三大学派对比可视化
展示符号主义、连接主义、行为主义的技术特征与应用对比
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

fig = plt.figure(figsize=(18, 12))
gs = GridSpec(3, 3, figure=fig, hspace=0.4, wspace=0.3)

# 上排：三大学派雷达图
schools = ['符号主义', '连接主义', '行为主义']
colors = ['#2196F3', '#4CAF50', '#FF9800']
metrics = ['知识表示', '学习能力', '感知能力', '推理能力', '决策优化', '可解释性']
data = {
    '符号主义': [0.9, 0.2, 0.3, 0.85, 0.5, 0.95],
    '连接主义': [0.4, 0.9, 0.95, 0.3, 0.4, 0.2],
    '行为主义': [0.3, 0.7, 0.6, 0.4, 0.9, 0.5],
}

for i, (school, color) in enumerate(zip(schools, colors)):
    ax = fig.add_subplot(gs[0, i], polar=True)
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    values = data[school]
    values_plot = values + values[:1]
    angles_plot = angles + angles[:1]
    ax.fill(angles_plot, values_plot, color=color, alpha=0.25)
    ax.plot(angles_plot, values_plot, color=color, linewidth=2.5)
    ax.set_xticks(angles)
    ax.set_xticklabels(metrics, fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_title(school, fontsize=13, fontweight='bold', color=color, pad=15)

# 中排左：三大学派发展历程（关键里程碑）
ax4 = fig.add_subplot(gs[1, 0])
timeline_data = [
    (1956, '符号', 'Dartmouth', '#2196F3'),
    (1958, '连接', '感知机', '#4CAF50'),
    (1969, '连接', 'XOR批判', '#F44336'),
    (1986, '连接', '反向传播', '#4CAF50'),
    (1989, '行为', 'Q-Learning', '#FF9800'),
    (2012, '连接', 'AlexNet', '#4CAF50'),
    (2016, '行为', 'AlphaGo', '#FF9800'),
    (2020, '连接', 'GPT-3', '#4CAF50'),
    (2022, '行为', 'RLHF', '#FF9800'),
]
years = [d[0] for d in timeline_data]
ax4.barh(range(len(timeline_data)), [1]*len(timeline_data),
         color=[d[3] for d in timeline_data], alpha=0.7)
for i, (year, school, event, color) in enumerate(timeline_data):
    ax4.text(0.5, i, f'{year} [{school}] {event}', ha='center', va='center',
             fontsize=8, fontweight='bold', color='white')
ax4.set_yticks([])
ax4.set_title('关键里程碑时间线', fontsize=12, fontweight='bold')
ax4.axis('off')

# 中排中：三大学派在晶圆厂应用成熟度
ax5 = fig.add_subplot(gs[1, 1])
applications = ['缺陷检测', '良率预测', '根因分析', '智能调度', 'R2R控制', '预测性维护']
symbolism_maturity = [0.6, 0.3, 0.85, 0.5, 0.3, 0.4]
connectionism_maturity = [0.95, 0.85, 0.5, 0.4, 0.6, 0.8]
behaviorism_maturity = [0.3, 0.5, 0.2, 0.7, 0.75, 0.6]

x = np.arange(len(applications))
w = 0.25
ax5.bar(x - w, symbolism_maturity, w, label='符号主义', color='#2196F3', alpha=0.8)
ax5.bar(x, connectionism_maturity, w, label='连接主义', color='#4CAF50', alpha=0.8)
ax5.bar(x + w, behaviorism_maturity, w, label='行为主义', color='#FF9800', alpha=0.8)
ax5.set_xticks(x)
ax5.set_xticklabels(applications, fontsize=8, rotation=15)
ax5.set_ylabel('应用成熟度')
ax5.set_title('三大学派在晶圆厂的应用成熟度', fontsize=12, fontweight='bold')
ax5.legend(fontsize=9)
ax5.grid(axis='y', alpha=0.3)

# 中排右：优劣势对比热力图
ax6 = fig.add_subplot(gs[1, 2])
aspects = ['可解释性', '学习能力', '泛化能力', '实时性', '知识获取', '鲁棒性']
matrix = np.array([
    [0.95, 0.2, 0.3, 0.6, 0.2, 0.7],   # 符号主义
    [0.2, 0.9, 0.95, 0.7, 0.8, 0.5],   # 连接主义
    [0.5, 0.7, 0.6, 0.5, 0.6, 0.8],    # 行为主义
])
im = ax6.imshow(matrix, cmap='RdYlGn', vmin=0, vmax=1, aspect='auto')
ax6.set_xticks(range(len(aspects)))
ax6.set_xticklabels(aspects, fontsize=9, rotation=30)
ax6.set_yticks(range(3))
ax6.set_yticklabels(schools, fontsize=10)
for i in range(3):
    for j in range(len(aspects)):
        ax6.text(j, i, f'{matrix[i,j]:.1f}', ha='center', va='center',
                 color='white' if matrix[i,j] > 0.5 else 'black', fontsize=9, fontweight='bold')
plt.colorbar(im, ax=ax6, fraction=0.046)
ax6.set_title('优劣势对比矩阵', fontsize=12, fontweight='bold')

# 底排：融合趋势
ax7 = fig.add_subplot(gs[2, :])
years_trend = np.arange(2010, 2027)
symbolism_trend = np.maximum(0.3, 0.6 - 0.02*(years_trend-2010)) + np.random.randn(len(years_trend))*0.02
connectionism_trend = 0.3 + 0.04*(years_trend-2010) + np.random.randn(len(years_trend))*0.02
behaviorism_trend = 0.1 + 0.03*(years_trend-2010) + np.random.randn(len(years_trend))*0.02
fusion_trend = np.maximum(0, 0.05 + 0.06*(years_trend-2015)) + np.random.randn(len(years_trend))*0.02
fusion_trend[years_trend < 2015] = 0.02

ax7.fill_between(years_trend, 0, symbolism_trend, alpha=0.3, color='#2196F3', label='符号主义')
ax7.fill_between(years_trend, symbolism_trend, symbolism_trend+connectionism_trend,
                 alpha=0.3, color='#4CAF50', label='连接主义')
ax7.fill_between(years_trend, symbolism_trend+connectionism_trend,
                 symbolism_trend+connectionism_trend+behaviorism_trend,
                 alpha=0.3, color='#FF9800', label='行为主义')
ax7.plot(years_trend, fusion_trend, color='#9C27B0', linewidth=3, label='融合方向 (NB/NA/SA/NSA)')
ax7.axvline(x=2020, color='gray', linestyle='--', alpha=0.5)
ax7.text(2020.3, 0.8, '融合加速期', fontsize=10, color='#9C27B0', fontweight='bold')
ax7.set_xlabel('年份', fontsize=11)
ax7.set_ylabel('相对影响力', fontsize=11)
ax7.set_title('AI三大学派发展趋势：从分立到融合', fontsize=13, fontweight='bold')
ax7.legend(fontsize=9, loc='upper left')
ax7.grid(alpha=0.3)

fig.suptitle('第2章 Demo：AI三大学派对比——技术特征、应用成熟度与融合趋势', 
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch2_three_schools.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch2 three schools demo saved.")
plt.close()
