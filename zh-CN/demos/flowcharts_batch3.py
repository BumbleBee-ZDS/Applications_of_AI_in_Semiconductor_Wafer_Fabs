"""
流程图批次3: Ch19-19 融合章节 + LLM/Agent/Ontology
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


# === Ch19: RLHF训练流程 ===
fig, ax = plt.subplots(figsize=(14, 6))
ax.set_xlim(0, 14); ax.set_ylim(0, 6); ax.axis('off')
box(ax, 2, 5, 2.5, 0.7, 'SFT阶段\n监督微调\n(工程师决策数据)', '#2196F3', 8)
box(ax, 5.5, 5, 2.5, 0.7, 'RM阶段\n奖励模型训练\n(偏好标注)', '#4CAF50', 8)
box(ax, 9, 5, 2.5, 0.7, 'PPO阶段\n强化学习优化\n(策略最大化奖励)', '#FF9800', 8)
box(ax, 12.5, 5, 2, 0.7, '部署\nRLHF策略', '#9C27B0', 8)
arrow(ax, 3.25, 5, 4.25, 5, '#2196F3')
arrow(ax, 6.75, 5, 7.75, 5, '#4CAF50')
arrow(ax, 10.25, 5, 11.5, 5, '#FF9800')
# 细节
box(ax, 2, 3, 2.5, 0.6, '输入: 产线状态\n输出: 工程师决策', '#64B5F6', 8)
box(ax, 5.5, 3, 2.5, 0.6, '两方案对比\n工程师选择更优', '#81C784', 8)
box(ax, 9, 3, 2.5, 0.6, 'PPO优化策略\nKL散度约束', '#FFB74D', 8)
arrow(ax, 2, 4.65, 2, 3.3, '#2196F3')
arrow(ax, 5.5, 4.65, 5.5, 3.3, '#4CAF50')
arrow(ax, 9, 4.65, 9, 3.3, '#FF9800')
# 反馈
arrow(ax, 10.25, 4.8, 10.25, 2, '#F44336')
arrow(ax, 10.25, 2, 5.5, 2, '#F44336')
arrow(ax, 5.5, 2, 5.5, 4.65, '#F44336')
ax.text(8, 1.5, 'RLHF反馈循环: 策略输出→奖励评分→策略更新', ha='center', fontsize=9, color='#F44336',
    bbox=dict(boxstyle='round', facecolor='#FFEBEE', alpha=0.8))
ax.set_title('第19章：NA融合——RLHF训练流程（从人类偏好到RL策略）', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch19_rlhf.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch19 RLHF saved.")

# === Ch20: 多智能体符号-行为架构 ===
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis('off')
# 符号层
box(ax, 7, 7.5, 6, 0.6, '符号层: 全局任务分解 + 部门间约束定义', '#2196F3', 10)
# 三个Agent
agents = [
    (2.5, 5.5, 'PID Agent\n工艺开发\nRL自适应执行', '#1976D2'),
    (7, 5.5, 'MFG Agent\n排产调度\nRL动态派工', '#43A047'),
    (11.5, 5.5, 'PE Agent\nRecipe优化\nRL参数搜索', '#FB8C00'),
]
for x, y, text, color in agents:
    box(ax, x, y, 3, 1.0, text, color=color, fs=8)
    arrow(ax, x, 7.2, x, 6, '#2196F3')
# 通信
arrow(ax, 4, 5.5, 5.5, 5.5, '#9C27B0')
arrow(ax, 8.5, 5.5, 10, 5.5, '#9C27B0')
ax.text(4.75, 5.8, '通知:\n工艺变更', fontsize=7, color='#9C27B0', ha='center',
    bbox=dict(boxstyle='round', facecolor='#F3E5F5', alpha=0.9))
ax.text(9.25, 5.8, '通知:\n设备调整', fontsize=7, color='#9C27B0', ha='center',
    bbox=dict(boxstyle='round', facecolor='#F3E5F5', alpha=0.9))
# 行为执行
box(ax, 7, 3.5, 8, 0.6, '行为层: 各Agent在执行中自适应处理不确定性', '#FF5722', 10)
for x, _, _, _ in agents:
    arrow(ax, x, 5, 7, 3.8, '#FF5722')
# 验证
box(ax, 7, 2, 6, 0.6, '符号层验证: 全局一致性检查 + 冲突协调', '#9C27B0', 10)
arrow(ax, 7, 3.2, 7, 2.3, '#9C27B0')
# 反馈
arrow(ax, 4, 2, 2.5, 2, '#795548')
arrow(ax, 2.5, 2, 2.5, 5, '#795548')
ax.text(1.5, 3.5, '反馈\n更新', fontsize=8, color='#795548', rotation=90,
    bbox=dict(boxstyle='round', facecolor='#EFEBE9', alpha=0.9))
ax.set_title('第20章：SA融合——多智能体符号-行为协同架构', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch20_multiagent.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch20 multiagent saved.")

# === Ch21: NSA四阶段演进 ===
fig, ax = plt.subplots(figsize=(16, 6))
ax.set_xlim(0, 16); ax.set_ylim(0, 6); ax.axis('off')
stages = [
    (2, '阶段1: AI辅助\n(当前)\nAI提供分析建议\n人类做所有决策', '#81C784', 'CNN分类\nKG推理'),
    (5.5, '阶段2: AI增强\n(1-2年)\nAI半自主决策\n人类监督确认', '#FFB74D', 'RL派工\nNB根因分析'),
    (9, '阶段3: AI自主\n(3-5年)\nAI限定场景自主\n人类设定目标', '#E57373', '自主调度\n自愈设备'),
    (12.5, '阶段4: 具身智能\n(5-10年+)\n物理闭环\n人机协作', '#BA68C8', '维修机器人\n全自动工厂'),
]
for x, text, color, tech in stages:
    box(ax, x, 4, 2.8, 1.5, text, color=color, fs=8)
    ax.text(x, 2.2, f'关键技术:\n{tech}', ha='center', fontsize=8, color='#666',
        bbox=dict(boxstyle='round', facecolor='#F5F5F5', alpha=0.8))
for i in range(len(stages)-1):
    arrow(ax, stages[i][0]+1.4, 4, stages[i+1][0]-1.4, 4, '#666')
# 底部能力矩阵
caps = ['感知', '认知', '行动', '物理闭环']
stage_caps = [
    [1, 0, 0, 0],
    [1, 1, 0.5, 0],
    [1, 1, 1, 0],
    [1, 1, 1, 1],
]
for i, (x, _, color, _) in enumerate(stages):
    for j, cap in enumerate(caps):
        filled = stage_caps[i][j]
        c = color if filled == 1 else ('#E0E0E0' if filled == 0 else '#BDBDBD')
        alpha = 0.9 if filled == 1 else 0.3
        ax.add_patch(mpatches.FancyBboxPatch((x-1.2+j*0.65, 0.5), 0.55, 0.4,
            boxstyle="round,pad=0.05", facecolor=c, alpha=alpha, edgecolor='white'))
        ax.text(x-0.93+j*0.65, 0.7, cap, fontsize=6, ha='center', color='white' if filled==1 else '#999')
ax.set_title('第21章：NSA全融合——从AI辅助到具身智能的四阶段演进', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch21_evolution.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch21 evolution saved.")

# === Ch22: RAG架构流程 ===
fig, ax = plt.subplots(figsize=(14, 6))
ax.set_xlim(0, 14); ax.set_ylim(0, 6); ax.axis('off')
box(ax, 2, 5, 2.5, 0.7, '用户提问\n(自然语言)', '#2196F3', 9)
box(ax, 5.5, 5, 2.5, 0.7, 'LLM理解意图\n生成检索query', '#4CAF50', 9)
box(ax, 9, 5, 2.5, 0.7, '向量数据库检索\n(工艺知识/SPEC)', '#FF9800', 9)
box(ax, 12.5, 5, 2, 0.7, '返回相关文档', '#9C27B0', 9)
arrow(ax, 3.25, 5, 4.25, 5)
arrow(ax, 6.75, 5, 7.75, 5)
arrow(ax, 10.25, 5, 11.5, 5)
box(ax, 12.5, 3, 2, 0.7, 'LLM+检索结果\n生成回答', '#00BCD4', 9)
arrow(ax, 12.5, 4.65, 12.5, 3.35, '#9C27B0')
box(ax, 7, 3, 3, 0.7, '引用来源标注\n(可追溯)', '#795548', 9)
arrow(ax, 11.5, 3, 8.5, 3, '#00BCD4')
box(ax, 2, 3, 2.5, 0.7, '输出回答\n(带引用)', '#4CAF50', 9)
arrow(ax, 5.5, 3, 3.25, 3, '#795548')
# 幻觉防护
box(ax, 7, 1, 4, 0.5, '幻觉防护: 回答必须基于检索到的文档', '#F44336', 8)
arrow(ax, 7, 2.65, 7, 1.25, '#F44336')
ax.set_title('第22章：RAG架构——LLM+检索增强生成在晶圆厂的应用流程', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch22_rag.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch22 RAG saved.")

# === Ch23: Agent核心架构 ===
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')
# 中心
box(ax, 6, 4, 3, 1, 'Agent核心\nLLM大脑', '#9C27B0', 11)
# 四个模块
modules = [
    (2, 7, '感知模块\n- FDC信号\n- 晶圆图\n- MES数据', '#2196F3'),
    (10, 7, '规划模块\n- 任务分解\n- 优先级排序\n- 资源分配', '#4CAF50'),
    (2, 1, '记忆模块\n- 短期记忆\n- 长期记忆\n- 经验库', '#FF9800'),
    (10, 1, '行动模块\n- API调用\n- 设备控制\n- 通知发送', '#F44336'),
]
for x, y, text, color in modules:
    box(ax, x, y, 3, 1.2, text, color=color, fs=8)
    dx = 6 - x
    dy = 4 - y
    dist = (dx**2 + dy**2)**0.5
    arrow(ax, x + dx/dist*1.5, y + dy/dist*0.6, 6 - dx/dist*1.5, 4 - dy/dist*0.5, color)
# 环境
box(ax, 6, 7.5, 3, 0.5, '晶圆厂环境', '#795548', 9)
arrow(ax, 2, 6.4, 5, 7.2, '#2196F3')
arrow(ax, 7, 7.2, 9, 6.4, '#4CAF50')
ax.set_title('第23章：Agent核心架构——感知/规划/记忆/行动', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch23_agent.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch23 agent saved.")

# === Ch24: Ontology驱动数据融合 ===
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis('off')
# 数据源
sources = [
    (2, 7, 'MES\n批次/工单', '#1565C0'),
    (2, 5.5, 'FDC\n设备参数', '#1976D2'),
    (2, 4, 'YMS\n良率/缺陷', '#1E88E5'),
    (2, 2.5, 'SPC\n控制图', '#42A5F5'),
]
for x, y, text, color in sources:
    box(ax, x, y, 2, 0.6, text, color=color, fs=8)
# Ontology层
box(ax, 6, 5, 3, 2.5, 'Ontology\n本体模型\n\n统一语义\n实体关系\n推理规则', '#9C27B0', 10)
for _, y, _, _ in sources:
    arrow(ax, 3, y, 4.5, 5, '#666')
# 输出
outputs = [
    (10, 7, '根因分析\n(推理)', '#4CAF50'),
    (10, 5, '智能问答\n(LLM+Ontology)', '#FF9800'),
    (10, 3, '数字孪生\n(仿真)', '#00BCD4'),
    (10, 1, '决策支持\n(Action)', '#F44336'),
]
for x, y, text, color in outputs:
    box(ax, x, y, 3, 0.6, text, color=color, fs=8)
    arrow(ax, 7.5, 5, 8.5, y, '#9C27B0')
ax.set_title('第24章：Ontology驱动的晶圆厂数据融合架构', fontsize=13, fontweight='bold', pad=15)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch24_ontology.png',
    dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Flow Ch24 ontology saved.")

print("\n=== Batch 3 flowcharts done ===")
