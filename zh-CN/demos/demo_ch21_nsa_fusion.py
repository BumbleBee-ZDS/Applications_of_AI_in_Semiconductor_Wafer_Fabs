"""
第21章 Demo: NSA全融合——感知-认知-行动闭环的具身智能
展示从数字孪生到自主决策的演进路径
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHeI', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

fig = plt.figure(figsize=(20, 16))
gs = GridSpec(4, 3, figure=fig, hspace=0.5, wspace=0.35)

# ========== 左上: NSA闭环架构 ==========
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.set_title('NSA全融合: 感知-认知-行动闭环', fontsize=12, fontweight='bold', color='#9C27B0')

# 三个圆代表三大学派
c_neural = Circle((2, 7), 1.3, facecolor='#2196F3', alpha=0.25, edgecolor='#2196F3', linewidth=2)
c_symbolic = Circle((5, 7), 1.3, facecolor='#4CAF50', alpha=0.25, edgecolor='#4CAF50', linewidth=2)
c_action = Circle((8, 7), 1.3, facecolor='#FF9800', alpha=0.25, edgecolor='#FF9800', linewidth=2)
ax1.add_patch(c_neural)
ax1.add_patch(c_symbolic)
ax1.add_patch(c_action)
ax1.text(2, 7, 'Neural\n(感知)', ha='center', va='center', fontsize=10, fontweight='bold', color='#2196F3')
ax1.text(5, 7, 'Symbolic\n(认知)', ha='center', va='center', fontsize=10, fontweight='bold', color='#4CAF50')
ax1.text(8, 7, 'Action\n(行动)', ha='center', va='center', fontsize=10, fontweight='bold', color='#FF9800')

# 中心: NSA融合
c_center = Circle((5, 4), 1.5, facecolor='#9C27B0', alpha=0.3, edgecolor='#9C27B0', linewidth=3)
ax1.add_patch(c_center)
ax1.text(5, 4, 'NSA\n全融合', ha='center', va='center', fontsize=12, fontweight='bold', color='#9C27B0')

# 箭头连接
for cx, cy in [(2, 7), (5, 7), (8, 7)]:
    ax1.annotate('', xy=(5 + (cx-5)*0.3, 4 + (cy-4)*0.3), xytext=(cx + (5-cx)*0.3, cy + (4-cy)*0.3),
                arrowprops=dict(arrowstyle='->', color='#9C27B0', lw=2, connectionstyle='arc3,rad=0.2'))

# 物理世界
world = FancyBboxPatch((3, 0.5), 4, 1.5, boxstyle='round,pad=0.2',
                         facecolor='#607D8B', alpha=0.2, edgecolor='#607D8B', linewidth=2)
ax1.add_patch(world)
ax1.text(5, 1.2, '物理晶圆厂\n(数字孪生映射)', ha='center', va='center', fontsize=9, fontweight='bold')

# 闭环箭头
ax1.annotate('', xy=(5, 2), xytext=(5, 2.5),
            arrowprops=dict(arrowstyle='->', color='#607D8B', lw=2.5))
ax1.annotate('', xy=(8.5, 5), xytext=(6.5, 1.2),
            arrowprops=dict(arrowstyle='->', color='#FF9800', lw=2,
                          connectionstyle='arc3,rad=-0.3'))
ax1.text(9, 3, '行动\n反馈', ha='center', fontsize=8, color='#FF9800', fontweight='bold')
ax1.annotate('', xy=(1.5, 5.5), xytext=(3.5, 1.2),
            arrowprops=dict(arrowstyle='->', color='#2196F3', lw=2,
                          connectionstyle='arc3,rad=0.3'))
ax1.text(0.5, 3, '感知\n输入', ha='center', fontsize=8, color='#2196F3', fontweight='bold')

ax1.axis('off')

# ========== 中上: 四阶段演进路径 ==========
ax2 = fig.add_subplot(gs[0, 1:])
ax2.set_xlim(0, 20)
ax2.set_ylim(0, 6)
ax2.set_title('NSA全融合: 四阶段演进路径', fontsize=12, fontweight='bold', color='#9C27B0')

stages = [
    (2.5, '阶段1: AI辅助\n(当前)\nAI提供分析建议\n人类做所有决策', '#81C784',
     ['CNN分类', 'KG推理', 'SPC监控']),
    (7.5, '阶段2: AI增强\n(1-2年)\nAI半自主决策\n人类监督确认', '#FFB74D',
     ['RL派工', 'NB根因', 'R2R优化']),
    (12.5, '阶段3: AI自主\n(3-5年)\n限定场景自主\n人类设定目标', '#E57373',
     ['自主调度', '自愈设备', '自动NPI']),
    (17.5, '阶段4: 具身智能\n(5-10年+)\n物理闭环\n人机协作', '#BA68C8',
     ['数字孪生', '维修机器人', '全自动厂']),
]

for x, label, color, features in stages:
    box = FancyBboxPatch((x-1.8, 1), 3.6, 3.5, boxstyle='round,pad=0.15',
                         facecolor=color, alpha=0.2, edgecolor=color, linewidth=2.5)
    ax2.add_patch(box)
    ax2.text(x, 3.8, label.split('\n')[0], ha='center', va='center', fontsize=11, fontweight='bold', color=color)
    for j, line in enumerate(label.split('\n')[1:]):
        ax2.text(x, 3.2 - j*0.4, line, ha='center', va='center', fontsize=8)
    # 特征标签
    for j, feat in enumerate(features):
        ax2.text(x, 1.5 - j*0.3, f'- {feat}', ha='center', va='center', fontsize=7, color=color)

# 阶段间箭头
for i in range(3):
    x_start = stages[i][0] + 1.8
    x_end = stages[i+1][0] - 1.8
    ax2.annotate('', xy=(x_end, 2.5), xytext=(x_start, 2.5),
                arrowprops=dict(arrowstyle='->', color='#666', lw=2.5))

# 成熟度曲线
maturity_x = np.linspace(0.5, 19.5, 100)
maturity_y = 0.2 + 5.5 / (1 + np.exp(-(maturity_x - 10) / 2.5))
ax2.plot(maturity_x, maturity_y, '--', color='#9C27B0', alpha=0.5, linewidth=2)
ax2.text(10, 5.5, '技术成熟度曲线', fontsize=9, color='#9C27B0', alpha=0.7, fontweight='bold')

ax2.axis('off')

# ========== 第二行左: 数字孪生精度 ==========
ax3 = fig.add_subplot(gs[1, 0])
time_sim = np.linspace(0, 100, 500)
real_temp = 200 + 20 * np.sin(time_sim * 0.1) + np.random.randn(500) * 1.5
twin_v1 = 200 + 20 * np.sin(time_sim * 0.1 - 0.3) + np.random.randn(500) * 3  # 低精度
twin_v2 = 200 + 20 * np.sin(time_sim * 0.1 - 0.05) + np.random.randn(500) * 0.8  # 高精度

ax3.plot(time_sim[:200], real_temp[:200], color='#424242', linewidth=2, label='真实设备温度')
ax3.plot(time_sim[:200], twin_v1[:200], color='#FF9800', linewidth=1.5, alpha=0.7, label='数字孪生v1 (RMSE=4.2)')
ax3.plot(time_sim[:200], twin_v2[:200], color='#2196F3', linewidth=1.5, alpha=0.7, label='数字孪生v2 (RMSE=1.1)')
ax3.set_xlabel('时间 (min)', fontsize=9)
ax3.set_ylabel('温度 (C)', fontsize=9)
ax3.set_title('数字孪生精度演进\n(世界模型)', fontsize=11, fontweight='bold')
ax3.legend(fontsize=8)
ax3.grid(alpha=0.3)

# ========== 第二行中: 自主决策准确率 ==========
ax4 = fig.add_subplot(gs[1, 1])
decision_types = ['工艺参数\n调优', '派工\n决策', 'PM调度', '异常\n响应', '良率\n优化', '产能\n分配']
stages_data = {
    'AI辅助': [65, 60, 70, 55, 68, 62],
    'AI增强': [80, 78, 85, 75, 82, 80],
    'AI自主': [92, 90, 95, 88, 93, 91],
}

x = np.arange(len(decision_types))
w = 0.25
for i, (stage, vals) in enumerate(stages_data.items()):
    offset = (i - 1) * w
    bars = ax4.bar(x + offset, vals, w, label=stage, alpha=0.8)
    for j, v in enumerate(vals):
        ax4.text(x[j] + offset, v + 1, f'{v}', ha='center', fontsize=7, fontweight='bold')

ax4.set_xticks(x)
ax4.set_xticklabels(decision_types, fontsize=8)
ax4.set_ylabel('决策准确率 (%)', fontsize=10)
ax4.set_title('不同NSA阶段下的自主决策准确率', fontsize=11, fontweight='bold')
ax4.legend(fontsize=9)
ax4.set_ylim(0, 105)
ax4.grid(axis='y', alpha=0.3)

# ========== 第二行右: 多模态融合 ==========
ax5 = fig.add_subplot(gs[1, 2])
modalities = ['视觉\n(缺陷图)', '时序\n(传感器)', '文本\n(SPEC)', '结构\n(MES)', '知识\n(KG)']
fusion_accuracy = [82, 78, 75, 80, 85]
cumulative = []
current = 0
for acc in fusion_accuracy:
    current = current * 0.3 + acc
    cumulative.append(current)
cumulative[0] = fusion_accuracy[0]
for i in range(1, len(cumulative)):
    cumulative[i] = max(cumulative[i-1], fusion_accuracy[i]) + (fusion_accuracy[i] - 60) * 0.15

ax5.bar(modalities, fusion_accuracy, 0.4, label='单模态准确率', color='#90CAF9', alpha=0.8)
ax5.plot(modalities, cumulative, 'o-', color='#9C27B0', linewidth=2.5, markersize=8, label='累积融合准确率')
for i, (v1, v2) in enumerate(zip(fusion_accuracy, cumulative)):
    ax5.text(i, v1 + 1, f'{v1}%', ha='center', fontsize=8)
    ax5.text(i, v2 + 1, f'{v2:.0f}%', ha='center', fontsize=8, fontweight='bold', color='#9C27B0')

ax5.set_ylabel('准确率 (%)', fontsize=10)
ax5.set_title('多模态融合的累积增益\n(每增加一种模态)', fontsize=11, fontweight='bold')
ax5.legend(fontsize=9)
ax5.set_ylim(0, 110)
ax5.grid(axis='y', alpha=0.3)

# ========== 第三行左: 自愈设备系统 ==========
ax6 = fig.add_subplot(gs[2, 0])
time_heal = np.arange(0, 50)
health_traditional = 100 - 1.2 * time_heal + 3 * np.sin(time_heal * 0.3)
health_traditional = np.clip(health_traditional, 20, 100)
health_sa = 100 - 0.3 * time_heal + 2 * np.sin(time_heal * 0.3)
# NSA自愈: 检测到下降后自动恢复
health_nsa = 100 - 0.5 * time_heal + 2 * np.sin(time_heal * 0.3)
health_nsa[15:] = health_nsa[15:] + np.cumsum(np.exp(-np.abs(time_heal[15:] - 15) * 0.5) * 3)
health_nsa = np.clip(health_nsa, 50, 100)

ax6.plot(time_heal, health_traditional, color='#F44336', linewidth=2, label='传统(定期PM)')
ax6.plot(time_heal, health_sa, color='#FF9800', linewidth=2, label='SA融合(计划维护)')
ax6.plot(time_heal, health_nsa, color='#9C27B0', linewidth=2.5, label='NSA自愈(实时恢复)')
ax6.axhline(y=60, color='gray', linestyle=':', alpha=0.5, label='告警阈值')
ax6.fill_between(time_heal, health_sa, health_nsa, alpha=0.1, color='#9C27B0')
ax6.set_xlabel('运行天数', fontsize=10)
ax6.set_ylabel('设备健康度', fontsize=10)
ax6.set_title('PE/EE: 自愈设备系统\n(NSA: 感知→推理→自动修复)', fontsize=11, fontweight='bold')
ax6.legend(fontsize=8, loc='lower left')
ax6.grid(alpha=0.3)

# ========== 第三行中: 全栈良率智能 ==========
ax7 = fig.add_subplot(gs[2, 1])
yield_stages = ['设计', 'NPI', '试产', '量产\n爬坡', '量产\n稳定', '良率\n衰退']
traditional_yield = [85, 70, 75, 82, 88, 84]
nsa_yield = [92, 85, 90, 94, 96, 95]

x = np.arange(len(yield_stages))
w = 0.35
ax7.bar(x - w/2, traditional_yield, w, label='传统流程', color='#FF6B6B', alpha=0.8)
ax7.bar(x + w/2, nsa_yield, w, label='NSA全栈', color='#9C27B0', alpha=0.8)

for i in range(len(yield_stages)):
    improvement = nsa_yield[i] - traditional_yield[i]
    ax7.text(i, max(traditional_yield[i], nsa_yield[i]) + 1.5, f'+{improvement}pp',
             ha='center', fontsize=9, fontweight='bold', color='#2196F3')

ax7.set_xticks(x)
ax7.set_xticklabels(yield_stages, fontsize=9)
ax7.set_ylabel('良率 (%)', fontsize=10)
ax7.set_title('PID/YED: 全栈良率智能\n(感知→推理→优化→验证→自愈)', fontsize=11, fontweight='bold')
ax7.legend(fontsize=9)
ax7.set_ylim(0, 105)
ax7.grid(axis='y', alpha=0.3)

# ========== 第三行右: 闭环延迟分析 ==========
ax8 = fig.add_subplot(gs[2, 2])
latency_components = ['感知延迟\n(Neural)', '推理延迟\n(Symbolic)', '决策延迟\n(Action)', '执行延迟\n(物理)', '反馈延迟\n(通信)']
latency_ai = [120, 350, 80, 5000, 2000]  # ms
latency_enhanced = [80, 150, 50, 3000, 800]
latency_autonomous = [30, 50, 20, 1500, 200]
latency_embodied = [10, 20, 10, 500, 50]

x = np.arange(len(latency_components))
w = 0.2
ax8.bar(x - 1.5*w, latency_ai, w, label='AI辅助', color='#81C784', alpha=0.8)
ax8.bar(x - 0.5*w, latency_enhanced, w, label='AI增强', color='#FFB74D', alpha=0.8)
ax8.bar(x + 0.5*w, latency_autonomous, w, label='AI自主', color='#E57373', alpha=0.8)
ax8.bar(x + 1.5*w, latency_embodied, w, label='具身智能', color='#BA68C8', alpha=0.8)

ax8.set_xticks(x)
ax8.set_xticklabels(latency_components, fontsize=8)
ax8.set_ylabel('延迟 (ms, 对数刻度)', fontsize=10)
ax8.set_yscale('log')
ax8.set_title('NSA闭环各阶段延迟分析\n(目标: <100ms端到端)', fontsize=11, fontweight='bold')
ax8.legend(fontsize=8, loc='upper right')
ax8.grid(axis='y', alpha=0.3)

# ========== 底部: NSA全融合效果矩阵 ==========
ax9 = fig.add_subplot(gs[3, :])
departments = ['PID/YED\n良率预测', 'PID/YED\n根因分析', 'PID/YED\n工艺优化',
               'MFG\n智能派工', 'MFG\nWIP管理', 'MFG\n异常响应',
               'PE/EE\n预测维护', 'PE/EE\n参数控制', 'PE/EE\n设备自愈']
nb_score = [88, 92, 75, 72, 70, 65, 78, 72, 60]
na_score = [85, 70, 88, 90, 82, 80, 85, 90, 68]
sa_score = [70, 80, 82, 85, 78, 88, 82, 75, 72]
nsa_score = [95, 96, 94, 97, 93, 95, 94, 96, 92]

x = np.arange(len(departments))
w = 0.2
ax9.bar(x - 1.5*w, nb_score, w, label='NB融合', color='#2196F3', alpha=0.7)
ax9.bar(x - 0.5*w, na_score, w, label='NA融合', color='#FF9800', alpha=0.7)
ax9.bar(x + 0.5*w, sa_score, w, label='SA融合', color='#4CAF50', alpha=0.7)
ax9.bar(x + 1.5*w, nsa_score, w, label='NSA全融合', color='#9C27B0', alpha=0.9)

# 标注NSA提升
for i in range(len(departments)):
    best_partial = max(nb_score[i], na_score[i], sa_score[i])
    improvement = nsa_score[i] - best_partial
    ax9.text(x[i] + 1.5*w, nsa_score[i] + 1, f'+{improvement}',
             ha='center', fontsize=8, fontweight='bold', color='#9C27B0')

ax9.set_xticks(x)
ax9.set_xticklabels(departments, fontsize=9)
ax9.set_ylabel('性能评分 (%, 越高越好)', fontsize=11)
ax9.set_title('NB vs NA vs SA vs NSA：晶圆厂三大部门全维度对比', fontsize=13, fontweight='bold')
ax9.legend(fontsize=11, loc='upper left', ncol=4)
ax9.set_ylim(0, 110)
ax9.grid(axis='y', alpha=0.3)

fig.suptitle('第21章 Demo：NSA全融合——感知-认知-行动闭环的具身智能与晶圆厂未来',
             fontsize=16, fontweight='bold', y=0.995)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch21_nsa_fusion.png',
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch21 NSA fusion demo saved.")
plt.close()
