"""
流程图批次2: Ch14-12 学派应用 + 融合概论
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def box(ax, x, y, w, h, text, color='#2196F3', fs=9):
    b = mpatches.FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.12",
        facecolor=color, edgecolor=color, alpha=0.9, linewidth=2)
    ax.add_patch(b)
    ax.text(x, y, text, ha='center', va='center', fontsize=fs, fontweight='bold', color='white')

def arrow(ax, x1, y1, x2, y2, color='#666'):
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
        arrowprops=dict(arrowstyle='->', color=color, lw=1.8))


# === Ch14: 缺陷根因分析专家系统流程 ===
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis('off')
box(ax, 3, 7, 3, 0.7, '缺陷数据输入\n(ADI/AEI检测)', '#2196F3')
box(ax, 3, 5.5, 3, 0.7, '知识图谱检索\n缺陷-工艺-设备关联', '#4CAF50')
arrow(ax, 3, 6.65, 3, 5.85, '#2196F3')
box(ax, 3, 4, 3, 0.7, '规则引擎推理\nIF-THEN规则链', '#FF9800')
arrow(ax, 3, 5.15, 3, 4.35, '#4CAF50')
box(ax, 3, 2.5, 3, 0.7, '根因候选列表\n(排序+置信度)', '#9C27B0')
arrow(ax, 3, 3.65, 3, 2.85, '#FF9800')
box(ax, 7.5, 5.5, 3, 0.7, 'SPC数据验证\n检查参数控制限', '#00BCD4')
arrow(ax, 4.5, 4, 6, 5.3, '#9C27B0')
box(ax, 7.5, 3.5, 3, 0.7, '设备历史检索\nFDC/MES记录', '#795548')
arrow(ax, 4.5, 2.5, 6, 3.3, '#9C27B0')
box(ax, 11.5, 4.5, 3, 1.0, '根因报告\n\n- 首要根因\n- 置信度\n- 推理链', '#4CAF50')
arrow(ax, 9, 5.3, 10, 4.7, '#00BCD4')
arrow(ax, 9, 3.7, 10, 4.3, '#795548')
box(ax, 7.5, 1, 4, 0.6, '知识库持续更新：新案例写入KG', '#9C27B0', 8)
arrow(ax, 11.5, 4, 9.5, 1.3, '#9C27B0')
ax.set_title('第14章：基于知识图谱的缺陷根因分析专家系统流程', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch14_expert_system.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch14 saved.")

# === Ch15: 深度学习训练pipeline ===
fig, ax = plt.subplots(figsize=(16, 5))
ax.set_xlim(0, 16); ax.set_ylim(0, 5); ax.axis('off')
stages = [
    (1.5, '数据采集\n晶圆图/FDC\nMES/YMS', '#1565C0'),
    (4, '数据预处理\n清洗/标注\n增强/分割', '#1976D2'),
    (6.5, '模型构建\nCNN/LSTM\nTransformer', '#1E88E5'),
    (9, '模型训练\nGPU训练\n超参调优', '#42A5F5'),
    (11.5, '模型评估\n准确率/F1\n过拟合检查', '#64B5F6'),
    (14, '部署推理\n在线预测\nAPI服务', '#90CAF9'),
]
for x, text, color in stages:
    box(ax, x, 3, 2, 1.2, text, color=color, fs=8)
for i in range(len(stages)-1):
    arrow(ax, stages[i][0]+1, 3, stages[i+1][0]-1, 3, '#666')
# 反馈
arrow(ax, 11.5, 2.4, 11.5, 1.5, '#F44336')
arrow(ax, 11.5, 1.5, 6.5, 1.5, '#F44336')
arrow(ax, 6.5, 1.5, 6.5, 2.4, '#F44336')
ax.text(9, 1.1, '评估不达标 → 调整超参/模型结构 → 重新训练', ha='center', fontsize=9, color='#F44336',
    bbox=dict(boxstyle='round', facecolor='#FFEBEE', alpha=0.8))
ax.set_title('第15章：深度学习模型训练Pipeline（从数据到部署）', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch15_training_pipeline.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch15 saved.")

# === Ch16: RL MDP决策循环 ===
fig, ax = plt.subplots(figsize=(10, 8))
ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis('off')
box(ax, 5, 7, 3, 0.8, 'Agent (RL策略 pi)', '#FF5722', 11)
box(ax, 5, 4, 3, 0.8, '环境 (晶圆厂)', '#795548', 11)
# State
arrow(ax, 3.5, 4.4, 3.5, 6.6, '#2196F3')
ax.text(2.5, 5.5, '状态 s_t\n(设备/WIP/良率)', fontsize=9, color='#2196F3', fontweight='bold',
    bbox=dict(boxstyle='round', facecolor='#E3F2FD', alpha=0.9))
# Action
arrow(ax, 6.5, 6.6, 6.5, 4.4, '#4CAF50')
ax.text(7.5, 5.5, '行动 a_t\n(派工/调参)', fontsize=9, color='#4CAF50', fontweight='bold',
    bbox=dict(boxstyle='round', facecolor='#E8F5E9', alpha=0.9))
# Reward
arrow(ax, 8, 4, 8, 2.5, '#FF9800')
arrow(ax, 8, 2.5, 2, 2.5, '#FF9800')
arrow(ax, 2, 2.5, 2, 6.6, '#FF9800')
ax.text(5, 2, '奖励 r_t = f(良率, 交期, 利用率)', ha='center', fontsize=10, color='#FF9800', fontweight='bold',
    bbox=dict(boxstyle='round', facecolor='#FFF3E0', alpha=0.9))
# 中心循环标注
ax.text(5, 5.5, 'MDP循环\npi(a|s) -> max E[sum r_t]', ha='center', fontsize=9, color='#9C27B0',
    bbox=dict(boxstyle='round', facecolor='#F3E5F5', alpha=0.9))
ax.set_title('第16章：强化学习MDP决策循环——Agent与晶圆厂环境的交互', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch16_mdp_loop.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch16 saved.")

# === Ch17: 三大融合方向映射图 ===
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis('off')
# 三个圆
from matplotlib.patches import Circle
c1 = Circle((3, 6), 1.5, facecolor='#2196F3', alpha=0.3, edgecolor='#2196F3', linewidth=2)
c2 = Circle((7, 6), 1.5, facecolor='#4CAF50', alpha=0.3, edgecolor='#4CAF50', linewidth=2)
c3 = Circle((11, 6), 1.5, facecolor='#FF9800', alpha=0.3, edgecolor='#FF9800', linewidth=2)
ax.add_patch(c1); ax.add_patch(c2); ax.add_patch(c3)
ax.text(3, 6, 'Neural\n连接主义', ha='center', va='center', fontsize=11, fontweight='bold', color='#1565C0')
ax.text(7, 6, 'Symbolic\n符号主义', ha='center', va='center', fontsize=11, fontweight='bold', color='#2E7D32')
ax.text(11, 6, 'Action\n行为主义', ha='center', va='center', fontsize=11, fontweight='bold', color='#E65100')
# 交集区域标注
ax.text(5, 6.8, 'NB', ha='center', fontsize=10, fontweight='bold', color='#9C27B0',
    bbox=dict(boxstyle='round', facecolor='#F3E5F5', alpha=0.9))
ax.text(9, 6.8, 'SA', ha='center', fontsize=10, fontweight='bold', color='#9C27B0',
    bbox=dict(boxstyle='round', facecolor='#F3E5F5', alpha=0.9))
ax.text(7, 4.8, 'NA', ha='center', fontsize=10, fontweight='bold', color='#9C27B0',
    bbox=dict(boxstyle='round', facecolor='#F3E5F5', alpha=0.9))
# NSA中心
nsa = Circle((7, 5.5), 0.6, facecolor='#9C27B0', alpha=0.5, edgecolor='#9C27B0', linewidth=2)
ax.add_patch(nsa)
ax.text(7, 5.5, 'NSA', ha='center', va='center', fontsize=8, fontweight='bold', color='white')
# 应用映射
apps = [
    (3, 2.5, 'PID/YED: 良率分析\nMFG: 数据问答\nPE/EE: 故障诊断', '#2196F3'),
    (7, 2.5, 'PID/YED: 参数优化\nMFG: 智能派工\nPE/EE: 设备控制', '#4CAF50'),
    (11, 2.5, 'PID/YED: NPI管理\nMFG: 异常响应\nPE/EE: PM计划', '#FF9800'),
]
for x, y, text, color in apps:
    box(ax, x, y, 3, 1.0, text, color=color, fs=8)
ax.set_title('第17章：三大主义交叉融合方向——NB/NA/SA/NSA映射', fontsize=14, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch17_fusion_map.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch17 saved.")

print("\n=== Batch 2 flowcharts done ===")
