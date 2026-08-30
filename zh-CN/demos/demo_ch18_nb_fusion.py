"""
第18章 Demo: NB融合——LLM+知识图谱的良率根因分析
展示神经符号融合的推理过程
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHeI', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

fig = plt.figure(figsize=(18, 12))
gs = GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# 左上：LLM假设生成
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)
hypotheses = [
    ('假设1: 光刻对准问题', 0.65, '#FF6B6B'),
    ('假设2: 刻蚀均匀性问题', 0.55, '#FF9800'),
    ('假设3: CMP过度抛光', 0.30, '#FFC107'),
    ('假设4: 沉积层厚度异常', 0.15, '#FFD54F'),
]
for i, (h, score, color) in enumerate(hypotheses):
    y = 0.85 - i * 0.22
    ax1.barh(y, score, height=0.12, color=color, alpha=0.8)
    ax1.text(score + 0.02, y, f'{score:.0%}', va='center', fontsize=9, fontweight='bold')
    ax1.text(0.01, y, h, va='center', fontsize=9)
ax1.set_xlim(0, 0.9)
ax1.set_title('步骤1: LLM生成假设\n(Neural — 直觉感知)', fontsize=11, fontweight='bold', color='#2196F3')
ax1.set_xlabel('LLM置信度', fontsize=9)
ax1.grid(axis='x', alpha=0.3)

# 中上：KG验证
ax2 = fig.add_subplot(gs[0, 1])
kg_data = {
    'Step 23 光刻': {'SPC': '3.2σ', 'status': '超标', 'color': '#F44336'},
    'Step 47 刻蚀': {'SPC': '1.1σ', 'status': '正常', 'color': '#4CAF50'},
    'Step 89 CMP': {'SPC': '0.8σ', 'status': '正常', 'color': '#4CAF50'},
    'Step 12 沉积': {'SPC': '1.5σ', 'status': '正常', 'color': '#4CAF50'},
}
for i, (step, data) in enumerate(kg_data.items()):
    y = 0.85 - i * 0.22
    ax2.barh(y, 1, height=0.12, color=data['color'], alpha=0.7)
    ax2.text(0.5, y, f"{step}\nSPC: {data['SPC']} → {data['status']}", 
             ha='center', va='center', fontsize=8, fontweight='bold', color='white')
ax2.set_xlim(0, 1)
ax2.set_title('步骤2: KG验证事实\n(Symbolic — 知识检索)', fontsize=11, fontweight='bold', color='#4CAF50')
ax2.axis('off')

# 右上：推理结果
ax3 = fig.add_subplot(gs[0, 2])
results = [
    ('光刻对准问题', 0.94, '#F44336', '已确认'),
    ('刻蚀均匀性', 0.12, '#4CAF50', '已排除'),
    ('CMP过度抛光', 0.05, '#4CAF50', '已排除'),
    ('沉积层异常', 0.03, '#4CAF50', '已排除'),
]
for i, (cause, prob, color, status) in enumerate(results):
    y = 0.85 - i * 0.22
    ax3.barh(y, prob, height=0.12, color=color, alpha=0.8)
    ax3.text(prob + 0.02, y, f'{prob:.0%} - {status}', va='center', fontsize=9, fontweight='bold')
    ax3.text(0.01, y, cause, va='center', fontsize=9)
ax3.set_xlim(0, 1.15)
ax3.set_title('步骤3: LLM+KG推理\n(NB融合 — 可验证)', fontsize=11, fontweight='bold', color='#9C27B0')
ax3.set_xlabel('验证后概率', fontsize=9)
ax3.grid(axis='x', alpha=0.3)

# 左中：推理链可视化
ax4 = fig.add_subplot(gs[1, 0])
chain = [
    ('CNN识别\n边缘环形缺陷\n(置信度94%)', '#2196F3'),
    ('KG检索\n边缘环形→{光刻,刻蚀,CMP}', '#4CAF50'),
    ('规则引擎\nSPC检查: Step23=3.2σ超标', '#FF9800'),
    ('LLM推理\n光刻对准问题\n置信度94%', '#9C27B0'),
    ('验证\n推理链完整\n无幻觉风险', '#4CAF50'),
]
for i, (text, color) in enumerate(chain):
    y = 4 - i
    ax4.barh(y, 1, height=0.7, color=color, alpha=0.7, edgecolor='white')
    ax4.text(0.5, y, text, ha='center', va='center', fontsize=8, fontweight='bold', color='white')
    if i < len(chain) - 1:
        ax4.annotate('', xy=(0.5, y - 0.35), xytext=(0.5, y - 0.5),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=2))
ax4.set_xlim(0, 1)
ax4.set_ylim(-0.5, 4.5)
ax4.set_title('NB融合推理链', fontsize=11, fontweight='bold')
ax4.axis('off')

# 中中+右中：LLM生成的分析报告
ax5 = fig.add_subplot(gs[1, 1:])
report_text = (
    "[良率分析报告 - 自动生成]\n"
    "========================================\n"
    "批次: B12345 | 产品: Product-X (3nm)\n"
    "良率: 85% (目标: 92%, 下降7pp)\n"
    "========================================\n"
    "[根因分析]\n"
    "  - CNN识别: 边缘环形缺陷 (置信度94%)\n"
    "  - KG检索: 关联3个边缘相关工艺步骤\n"
    "  - SPC验证: Step 23光刻套刻精度3.2sigma\n"
    "    -> 超出2sigma控制限 (Tool-A03)\n"
    "  - 其他步骤参数均在控制限内\n"
    "========================================\n"
    "[结论] 首要根因 = Tool-A03光刻套刻精度超标\n"
    "[推理链] 5步, 全部可追溯\n"
    "[幻觉风险] 无 (每步有KG数据支撑)\n"
    "[建议] 检查Tool-A03对准系统校准\n"
    "========================================\n"
    "生成时间: 3.8秒 | 验证: 通过"
)
ax5.text(0.05, 0.95, report_text, transform=ax5.transAxes, fontsize=10,
         verticalalignment='top',
         fontfamily='SimHei',
         bbox=dict(boxstyle='round', facecolor='#F5F5F5', edgecolor='#2196F3', alpha=0.9))
ax5.set_title('LLM自动生成的良率分析报告（经KG验证）', fontsize=11, fontweight='bold', color='#9C27B0')
ax5.axis('off')

# 底部：传统方法 vs NB融合对比
ax6 = fig.add_subplot(gs[2, :])
metrics = ['分析时间\n(分钟)', '准确率\n(%)', '可追溯性\n(1-10)', '幻觉风险\n(1-10)', '工程师\n接受度(%)']
traditional = [120, 75, 3, 8, 60]
nb_fusion = [3.8, 94, 10, 1, 88]

x = np.arange(len(metrics))
w = 0.35
ax6.bar(x - w/2, traditional, w, label='传统人工分析', color='#FF6B6B', alpha=0.8)
ax6.bar(x + w/2, nb_fusion, w, label='NB融合分析', color='#9C27B0', alpha=0.8)
for i in range(len(metrics)):
    t_val = traditional[i]
    n_val = nb_fusion[i]
    improvement = ((n_val - t_val) / t_val * 100) if t_val > 0 else 0
    if i in [0, 3]:  # 越低越好
        improvement = -improvement
    ax6.text(i, max(t_val, n_val) + 3, f'{improvement:+.0f}%', ha='center', 
             fontsize=9, fontweight='bold', color='#2196F3')
ax6.set_xticks(x)
ax6.set_xticklabels(metrics, fontsize=10)
ax6.set_title('传统人工分析 vs NB融合分析：关键指标对比', fontsize=13, fontweight='bold')
ax6.legend(fontsize=10)
ax6.grid(axis='y', alpha=0.3)

fig.suptitle('第18章 Demo：NB融合（LLM+知识图谱）驱动的可验证良率根因分析', 
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch18_nb_fusion.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch18 NB fusion demo saved.")
plt.close()
