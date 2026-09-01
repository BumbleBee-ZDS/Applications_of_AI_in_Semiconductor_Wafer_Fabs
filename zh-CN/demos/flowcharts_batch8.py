# -*- coding: utf-8 -*-
"""
batch8: 为第24/25/26章补充流程图
- ch24: Foundry五层架构 / 传统RCA vs Ontology驱动RCA / Ontology三阶段演进
- ch25: 晶圆厂核心本体模型地图 / MES+FDC+SPC+YMS数据融合架构 / 本体实施四阶段路径
- ch26: AMHS天车与AGV智能搬运闭环
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

IMG = r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images'

def draw_flowbox(ax, x, y, w, h, text, color='#2196F3', text_color='white', fontsize=9, alpha=0.9, pad=0.15):
    box = mpatches.FancyBboxPatch((x - w/2, y - h/2), w, h,
                                   boxstyle="round,pad=%f" % pad,
                                   facecolor=color, edgecolor=color, alpha=alpha, linewidth=2)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight='bold', color=text_color, wrap=True)

def draw_arrow(ax, x1, y1, x2, y2, color='#444', label=None, lx=0, ly=0, lw=1.8):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw))
    if label:
        ax.text((x1+x2)/2 + lx, (y1+y2)/2 + ly, label, ha='center', fontsize=8.5, color='#555')

def save(fig, name):
    fig.savefig(r'%s\%s' % (IMG, name), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('Saved', name)

# ============================================================
# 1. Ch24-A: Foundry 五层架构
# ============================================================
fig, ax = plt.subplots(figsize=(13, 8.5))
ax.set_xlim(0, 13); ax.set_ylim(0, 9); ax.axis('off')

layers = [
    (7.6, 10.0, 1.3, '应用层 (Applications)\n仪表盘 / 工作流 / API / LLM Agent', '#2E7D32'),
    (6.3, 10.0, 1.5, '本体层 (Ontology)  ★核心\n对象类型 / 关系 / 动作 / 函数 —— 语义统一层，所有数据的"通用语言"', '#283593'),
    (5.0, 10.0, 1.3, '模型层 (Models)\nML模型 / 统计模型 / 优化模型（绑定到本体对象）', '#1565C0'),
    (3.7, 10.0, 1.3, '数据层 (Data Integration)\nETL管道 / 流式数据 / 联邦查询', '#00838F'),
    (2.4, 10.0, 1.3, '数据源 (Sources)\nMES / FDC / SPC / YMS / ERP / IoT', '#6A1B9A'),
]
for y, w, h, text, color in layers:
    draw_flowbox(ax, 6.5, y, w, h, text, color=color, fontsize=9.5)

notes = [
    (7.6, '所有应用共享同一本体'),
    (6.3, '可执行本体=企业数字孪生'),
    (5.0, '模型作为本体函数调用'),
    (3.7, '支持联邦查询'),
    (2.4, '接入而非取代现有系统'),
]
for y, note in notes:
    ax.text(11.7, y, note, ha='left', va='center', fontsize=8, color='#555')

ax.set_title('第24章: Palantir Foundry 五层架构（本体层为核心）', fontsize=13, fontweight='bold', pad=12)
save(fig, 'flow_ch24_foundry_arch.png')

# ============================================================
# 2. Ch24-B: 传统 RCA vs Ontology 驱动 RCA
# ============================================================
fig, ax = plt.subplots(figsize=(15, 9))
ax.set_xlim(0, 15); ax.set_ylim(0, 9.5); ax.axis('off')

# 左列: 传统方式
draw_flowbox(ax, 3.75, 8.7, 4.8, 0.9, '传统方式: 工程师跨系统人工查询', '#F44336', fontsize=10.5)
steps_old = [
    (7.5, '① YMS 查看晶圆图\n判断缺陷类型'),
    (6.35, '② MES 查工艺路径\n定位异常步骤'),
    (5.2, '③ FDC 查传感器数据\n检查参数异常'),
    (4.05, '④ SPC 查量测数据\n确认参数偏差'),
    (2.9, '⑤ 人工关联信息\n推断根因'),
]
for y, text in steps_old:
    draw_flowbox(ax, 3.75, y, 3.9, 0.95, text, color='#E57373', fontsize=9, pad=0.05)
for i in range(len(steps_old)-1):
    draw_arrow(ax, 3.75, steps_old[i][0]-0.48, 3.75, steps_old[i+1][0]+0.48, color='#C62828')
ax.text(3.75, 1.7, '耗时 4-8 小时 · 高度依赖工程师经验', ha='center', fontsize=10,
        color='#C62828', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#FFEBEE', alpha=0.9))

# 右列: Ontology 方式
draw_flowbox(ax, 11.25, 8.7, 5.2, 0.9, 'Foundry 方式: 本体驱动的自动推理', '#2E7D32', fontsize=10.5)
steps_new = [
    (7.5, '① 输入批次号'),
    (6.35, '② 自动展示完整工艺历史'),
    (5.2, '③ 自动标注异常参数'),
    (4.05, '④ 沿本体关系链搜索关联路径'),
    (2.9, '⑤ 生成根因假设+置信度'),
]
for y, text in steps_new:
    draw_flowbox(ax, 11.25, y, 3.9, 0.85, text, color='#66BB6A', fontsize=9, pad=0.05)
for i in range(len(steps_new)-1):
    draw_arrow(ax, 11.25, steps_new[i][0]-0.43, 11.25, steps_new[i+1][0]+0.43, color='#1B5E20')
ax.text(11.25, 1.7, '缩短到 30-60 分钟 · 不受经验水平限制', ha='center', fontsize=10,
        color='#1B5E20', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#E8F5E9', alpha=0.9))

# 中间对比
ax.annotate('', xy=(8.4, 5.2), xytext=(6.6, 5.2),
            arrowprops=dict(arrowstyle='->', color='#F9A825', lw=3))
ax.text(7.5, 5.75, 'Ontology\n语义统一', ha='center', fontsize=10, color='#F9A825', fontweight='bold')

ax.set_title('第24章: 良率根因分析——传统方式 vs Ontology 驱动', fontsize=13, fontweight='bold', pad=12)
save(fig, 'flow_ch24_rca_comparison.png')

# ============================================================
# 3. Ch24-C: 从个案到范式三阶段演进
# ============================================================
fig, ax = plt.subplots(figsize=(15, 6.5))
ax.set_xlim(0, 15); ax.set_ylim(0, 6.5); ax.axis('off')

stages = [
    (2.6, '第一阶段: 企业内数据融合\n(三星案例)\nMES/FDC/SPC/YMS 统一本体\n2nm良率 30%→55-60%', '#1565C0'),
    (7.5, '第二阶段: 供应链数据共享\n(Athinia案例)\n材料商×设备商×晶圆厂\nCMP预测性制造 + SEMI合作', '#283593'),
    (12.4, '第三阶段: 行业级AI基础设施\n(AIOS-RA / Warp Speed)\n全行业共享数据与AI模型\nOntology成为制造OS', '#6A1B9A'),
]
for x, text, color in stages:
    draw_flowbox(ax, x, 4.3, 4.0, 2.2, text, color=color, fontsize=9)
draw_arrow(ax, 4.7, 4.3, 5.4, 4.3, color='#F9A825', lw=2.5)
draw_arrow(ax, 9.6, 4.3, 10.3, 4.3, color='#F9A825', lw=2.5)

values = [
    (2.6, '价值层1: 数据融合', '让分散数据可关联查询'),
    (7.5, '价值层2: 知识推理', 'AI基于关联做因果推理与RCA'),
    (12.4, '价值层3: 行动执行', '分析结果直接转化为可执行操作'),
]
for x, t, d in values:
    ax.text(x, 2.5, t, ha='center', fontsize=10, fontweight='bold', color='#283593')
    ax.text(x, 1.9, d, ha='center', fontsize=8.5, color='#555')
    draw_arrow(ax, x, 3.1, x, 2.8, color='#999')

ax.text(7.5, 0.9, '从"企业内部"到"企业之间"再到"全行业" —— 数据孤岛不只在企业内部，更在企业之间',
        ha='center', fontsize=10, color='#555', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
ax.set_title('第24章: Palantir 在半导体行业的三阶段演进——从个案到范式', fontsize=13, fontweight='bold', pad=12)
save(fig, 'flow_ch24_evolution.png')

# ============================================================
# 4. Ch25-A: 晶圆厂核心本体模型地图
# ============================================================
fig, ax = plt.subplots(figsize=(15, 9))
ax.set_xlim(0, 15); ax.set_ylim(0, 9.5); ax.axis('off')

draw_flowbox(ax, 3.2, 8.0, 4.4, 1.5, '产品本体\nFabSite / Product / Lot / Wafer / Die', '#1565C0', fontsize=9.5)
draw_flowbox(ax, 11.8, 8.0, 4.4, 1.5, '工艺本体\nRoute / ProcessStep\nModule / Recipe / Parameter', '#283593', fontsize=9.5)
draw_flowbox(ax, 3.2, 4.6, 4.4, 1.5, '缺陷本体\nDefect / DefectType\nDefectPattern / RootCause', '#C62828', fontsize=9.5)
draw_flowbox(ax, 11.8, 4.6, 4.4, 1.5, '设备本体\nToolType / Tool / Chamber\nComponent / ConsumablePart', '#00838F', fontsize=9.5)
draw_flowbox(ax, 7.5, 1.9, 4.4, 1.4, '时间本体\nShift / Day / Week / Month\nPMCycle / RecipeCycle', '#6A1B9A', fontsize=9.5)

draw_arrow(ax, 5.4, 8.0, 9.6, 8.0, color='#999')
ax.text(7.5, 8.3, 'Lot 经 Route 流转', ha='center', fontsize=8, color='#777')
draw_arrow(ax, 3.2, 7.2, 3.2, 5.4, color='#999')
ax.text(2.45, 6.3, 'HAS_DEFECT', ha='center', fontsize=8, color='#777', rotation=90)
draw_arrow(ax, 11.8, 7.2, 11.8, 5.4, color='#999')
ax.text(12.55, 6.3, 'ProcessStep\nuses Tool', ha='center', fontsize=8, color='#777', rotation=90)
draw_arrow(ax, 5.4, 4.6, 9.6, 4.6, color='#999')
ax.text(7.5, 4.9, 'RootCause → RELATED_TO → Tool（因果链路）', ha='center', fontsize=8, color='#777')
draw_arrow(ax, 4.5, 3.9, 6.2, 2.65, color='#999')
ax.text(4.75, 3.05, 'OCCURRED_DURING', ha='center', fontsize=8, color='#777')
draw_arrow(ax, 10.5, 3.9, 8.8, 2.65, color='#999')
ax.text(10.25, 3.05, 'RAN_PM_AT', ha='center', fontsize=8, color='#777')

ax.text(7.5, 0.7, '五大本体 + 显式关系链路 = 跨系统关联查询与因果推理的基础',
        ha='center', fontsize=10.5, color='#555', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
ax.set_title('第25章: 晶圆厂核心本体模型地图（产品/工艺/设备/缺陷/时间）', fontsize=13, fontweight='bold', pad=12)
save(fig, 'flow_ch25_ontology_map.png')

# ============================================================
# 5. Ch25-B: MES+FDC+SPC+YMS 数据融合架构
# ============================================================
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14); ax.set_ylim(0, 8.5); ax.axis('off')

sources = [
    (1.9, 'MES\n(骨架)\nLot追踪/进出时间', '#1565C0'),
    (4.9, 'FDC\n(血肉)\n传感器时序数据', '#00838F'),
    (7.9, 'SPC\n(量尺)\n量测结果/控制图', '#283593'),
    (10.9, 'YMS\n(裁判)\n缺陷/测试良率', '#6A1B9A'),
]
for x, text, color in sources:
    draw_flowbox(ax, x, 6.9, 2.6, 1.5, text, color=color, fontsize=9)
    draw_arrow(ax, x, 6.05, x, 5.35, color='#777')

# 对齐层
draw_flowbox(ax, 6.4, 4.8, 11.4, 1.1, '语义对齐: 概念对齐(步骤等价映射) × 粒度对齐(批次级与秒级) × 时间对齐(UTC统一)',
             color='#F9A825', text_color='#333', fontsize=9)

# 本体层
draw_flowbox(ax, 6.4, 3.3, 11.4, 1.3, '统一本体: Wafer / Lot / Tool / ProcessStep / Measurement / Defect / SensorData',
             color='#283593', fontsize=10)
draw_arrow(ax, 6.4, 4.2, 6.4, 4.0, color='#777')

# 映射说明
maps = ['记录直接映射为对象实例', '时间对齐后映射为SensorData', '映射为Measurement对象', '映射为Defect/测试结果']
for (x, _, _), m in zip(sources, maps):
    ax.text(x, 5.62, m, ha='center', fontsize=7, color='#777')

# 应用层
apps = [
    (3.0, '本体驱动\n根因分析(RCA)', '#2E7D32'),
    (6.4, '本体+LLM\n智能问答', '#2E7D32'),
    (9.8, '本体驱动\n数字孪生', '#2E7D32'),
]
for x, text, color in apps:
    draw_flowbox(ax, x, 1.5, 3.0, 1.2, text, color=color, fontsize=9)
    draw_arrow(ax, x, 2.6, x, 2.15, color='#999')

ax.set_title('第25章: Ontology 驱动的数据融合——MES + FDC + SPC + YMS', fontsize=13, fontweight='bold', pad=12)
save(fig, 'flow_ch25_data_fusion.png')

# ============================================================
# 6. Ch25-C: 本体实施四阶段路径
# ============================================================
fig, ax = plt.subplots(figsize=(16, 5.8))
ax.set_xlim(0, 16); ax.set_ylim(0, 5.8); ax.axis('off')

phases = [
    (2.2, '阶段一: 良率分析本体', 'Wafer/Lot/ProcessStep\nTool/Defect/TestResult\n六类核心实体+基础关系', '#1565C0'),
    (5.9, '阶段二: 设备健康本体', 'Tool/Chamber/Component层级\nSensorData/MaintenanceEvent\nPMCycle → 预测性维护', '#00838F'),
    (9.6, '阶段三: 生产调度本体', 'Route/DispatchingRule\nWIP/Capacity\n→ 智能调度与瓶颈分析', '#283593'),
    (13.3, '阶段四: 全厂集成本体', '跨领域关系整合:\n健康度→工艺质量→良率→产能\n→ 整厂Agent+数字孪生', '#6A1B9A'),
]
for x, title, sub, color in phases:
    draw_flowbox(ax, x, 3.6, 3.2, 2.3, title + '\n' + sub, color=color, fontsize=8.5)
for i in range(len(phases)-1):
    draw_arrow(ax, phases[i][0]+1.6, 3.6, phases[i+1][0]-1.6, 3.6, color='#F9A825', lw=2.2)

ax.text(8.0, 1.5, '增量式构建: 从最高价值场景出发，先建最小本体，再逐步扩展 —— 不追求一步到位',
        ha='center', fontsize=10, color='#555', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
ax.set_title('第25章: 晶圆厂 Ontology 实施四阶段路径', fontsize=13, fontweight='bold', pad=12)
save(fig, 'flow_ch25_build_roadmap.png')

# ============================================================
# 7. Ch26-D: AMHS 天车与 AGV 智能搬运闭环
# ============================================================
fig, ax = plt.subplots(figsize=(15, 6.5))
ax.set_xlim(0, 15); ax.set_ylim(0, 6.8); ax.axis('off')

main = [
    (2.0, '搬运任务下发', '#1565C0'),
    (4.7, '实时感知路况', '#00838F'),
    (7.4, '动态路径规划', '#283593'),
    (10.1, '执行搬运\n(避障/交互)', '#2E7D32'),
    (12.8, 'Load Port\n交付FOUP', '#1565C0'),
]
for x, text, color in main:
    draw_flowbox(ax, x, 4.6, 2.3, 1.3, text, color=color, fontsize=9)
for i in range(len(main)-1):
    draw_arrow(ax, main[i][0]+1.15, 4.6, main[i+1][0]-1.15, 4.6, color='#444')

# 异常处理分支
draw_arrow(ax, 7.4, 3.9, 7.4, 3.1, color='#F44336')
draw_flowbox(ax, 7.4, 2.4, 2.6, 1.2, '遇障碍物/拥堵异常', '#F44336', fontsize=9)
draw_arrow(ax, 8.7, 2.4, 9.0, 2.4, color='#F44336')
draw_flowbox(ax, 10.3, 2.4, 2.4, 1.2, '自主判断:\n重规划/等待/上报', '#F44336', fontsize=8.5)
draw_arrow(ax, 11.5, 2.6, 12.3, 3.4, color='#F44336')
ax.text(12.4, 2.95, '恢复正常', ha='center', fontsize=8, color='#F44336')

# 反馈闭环
draw_arrow(ax, 12.8, 3.9, 12.8, 1.3, color='#999')
draw_arrow(ax, 12.8, 1.3, 4.7, 1.3, color='#999')
draw_arrow(ax, 4.7, 1.3, 4.7, 3.85, color='#999')
ax.text(8.7, 0.85, '交付状态与路况反馈 → 更新调度（闭环）', ha='center', fontsize=9, color='#777')

ax.text(7.5, 6.2, '从"固定轨道+预设路径"走向"动态规划+自主异常处理"', ha='center',
        fontsize=10, color='#555', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
ax.set_title('第26章: AMHS 天车与 AGV 智能搬运闭环', fontsize=13, fontweight='bold', pad=12)
save(fig, 'flow_ch26_amhs_transport.png')
