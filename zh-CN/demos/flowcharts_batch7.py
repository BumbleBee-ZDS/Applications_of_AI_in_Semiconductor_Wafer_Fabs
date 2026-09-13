"""
第28章 晶圆厂数据体系 配图生成脚本(第一部分)
Part 1: 数据源全景 / 时间粒度对比 / 七层加工链路 / 语义层架构
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

IMG = r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images'

def draw_flowbox(ax, x, y, w, h, text, color='#2196F3', text_color='white', fontsize=9):
    box = mpatches.FancyBboxPatch((x - w/2, y - h/2), w, h,
                                   boxstyle="round,pad=0.15",
                                   facecolor=color, edgecolor=color, alpha=0.9, linewidth=2)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight='bold', color=text_color, wrap=True)
    return (x, y, w, h)

def draw_arrow(ax, x1, y1, x2, y2, color='#666', lw=1.8):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw))

# ============================================================
# 1. 图28-1: 数据源全景四层图 (28.1.1)
# ============================================================
fig, ax = plt.subplots(figsize=(13, 6.5))
ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')

# 四层(自下而上)
layers = [
    ('设备层 Equipment Layer', 0.8, '#E8EAF6', [
        ('刻蚀机 Etcher', 'ETCH-03'), ('光刻机 Scanner', 'LITHO-02'),
        ('薄膜设备 Deposition', 'DEPO-01'), ('量测设备 Metrology', 'MET-05')], '#5C6BC0'),
    ('控制层 Control Layer', 2.9, '#E3F2FD', [
        ('EAP 设备自动化', '工艺参数采集'), ('FDC/EDA 数据采集', 'SECS/GEM 通信')], '#42A5F5'),
    ('执行层 Execution Layer', 5.0, '#E8F5E9', [
        ('MES 制造执行', '批次/工单'), ('SPC 统计过程控制', '管制图'),
        ('YMS 良率管理', '晶圆图/良率')], '#66BB6A'),
    ('计划层 Planning Layer', 7.1, '#FFF3E0', [
        ('ERP 企业资源规划', '物料/成本'), ('分析平台 Analytics', 'BI/数据仓库')], '#FFA726'),
]
for name, y, bg, items, edge in layers:
    ax.add_patch(plt.Rectangle((0.8, y-0.55), 10.4, 1.2, facecolor=bg,
                               edgecolor=edge, lw=1.5, zorder=1))
    ax.text(1.0, y+0.28, name, fontsize=10, fontweight='bold', color=edge, zorder=2)
    n = len(items)
    for i, (t, sub) in enumerate(items):
        x = 3.4 + i * (9.0 / n)
        draw_flowbox(ax, x, y-0.05, 2.6/n*3, 0.7, f'{t}\n{sub}', color=edge,
                     fontsize=8)
# 层间数据流向箭头
for y1, y2 in [(1.35, 2.35), (3.45, 4.45), (5.55, 6.55)]:
    draw_arrow(ax, 1.0, y1, 1.0, y2, color='#B0BEC5')
    ax.text(1.12, (y1+y2)/2, '数据流 data flow', fontsize=8, color='#78909C', rotation=90)
# 右侧标注
ax.text(11.5, 4.0, '数据流自下而上:\n设备→控制→执行→计划\n(数据流向 Data flows upward)',
        ha='center', fontsize=9, color='#455A64',
        bbox=dict(boxstyle='round', facecolor='white', edgecolor='#B0BEC5'))
ax.set_title('图28-1 晶圆厂数据源全景图 / Fab Data-Source Landscape (IT/OT 四层架构)',
             fontsize=13, fontweight='bold', pad=10)
fig.tight_layout()
fig.savefig(f'{IMG}\\flow_ch28_data_sources.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('图28-1 数据源全景 saved')

# ============================================================
# 2. 图28-2: 数据时间粒度对比图 (28.1.2)
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5.5))
# 横轴: 时间粒度(对数), 纵轴: 单日数据量(对数)
data = [
    ('FDC/EDA', 1e-1, 1e7, '#E53935'),      # 毫秒级, 千万级记录
    ('SECS/GEM日志', 5e0, 1e5, '#FB8C00'),   # 秒~分钟级, 十万级
    ('MES', 3e2, 1e5, '#1E88E5'),            # 分钟~小时级, 十万级
    ('检测/量测', 3e3, 1e4, '#8E24AA'),      # 片/批次级
    ('SPC', 1e4, 1e4, '#00897B'),            # 批次级
    ('YMS', 1e5, 1e3, '#43A047'),            # 批次/日级
    ('ERP', 1e5, 1e3, '#F4511E'),            # 天级
]
for name, gran, vol, color in data:
    ax.scatter(gran, vol, s=vol/100, color=color, alpha=0.85, zorder=3, edgecolor='white', lw=1)
    ax.annotate(name, (gran, vol), textcoords='offset points', xytext=(6, 6),
                fontsize=9, fontweight='bold', color=color)
# 区域标注
ax.axvspan(1e-2, 1e1, color='#FFEBEE', alpha=0.5)
ax.text(3e-1, 3e6, '高频时序流\n(设备过程参数)', fontsize=9, color='#C62828', fontweight='bold')
ax.axvspan(1e1, 1e3, color='#E3F2FD', alpha=0.5)
ax.text(4e1, 3e5, '事件流\n(生产执行)', fontsize=9, color='#1565C0', fontweight='bold')
ax.axvspan(1e3, 1e6, color='#E8F5E9', alpha=0.5)
ax.text(1.5e4, 1e4, '业务汇总\n(质量/良率/经营)', fontsize=9, color='#2E7D32', fontweight='bold')
ax.set_xscale('log'); ax.set_yscale('log')
from matplotlib.ticker import FuncFormatter
def fmt_log(x, pos):
    """log 刻度标签: 显示为 10^n(用 ASCII, 避免 U+2212)"""
    e = int(round(np.log10(x)))
    return f'10^{e}' if x != 1.0 else '1'
ax.xaxis.set_major_formatter(FuncFormatter(fmt_log))
ax.yaxis.set_major_formatter(FuncFormatter(fmt_log))
ax.set_xlabel('时间粒度 (秒) / time granularity (s, log)', fontsize=11)
ax.set_ylabel('单日数据量 (条/天) / daily volume (records/day, log)', fontsize=11)
ax.set_title('图28-2 各数据源时间粒度与量级对比 / Data Time-Granularity & Volume Comparison',
             fontsize=12, fontweight='bold')
ax.grid(alpha=0.3, which='both')
fig.tight_layout()
fig.savefig(f'{IMG}\\demo_ch28_time_granularity.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('图28-2 时间粒度对比 saved')

# ============================================================
# 3. 图28-3: 七层加工链路图 (28.2.1)
# ============================================================
fig, ax = plt.subplots(figsize=(14, 3.6))
ax.set_xlim(0, 14); ax.set_ylim(0, 3); ax.axis('off')
stages = [
    ('源表\nYMS.WAFER_TEST_RESULT', '#B71C1C'),
    ('Oracle存储过程\nPKG_YIELD.CALC_WEEKLY', '#D32F2F'),
    ('PL/SQL业务逻辑\n过滤返工/折算', '#E64A19'),
    ('ETL作业\n每日增量入仓', '#F57C00'),
    ('数仓视图\nV_YIELD_WEEKLY', '#F9A825'),
    ('BI报表\n周良率KPI', '#FBC02D'),
]
for i, (txt, c) in enumerate(stages):
    x = 1.1 + i * 2.2
    draw_flowbox(ax, x, 2.0, 2.0, 1.1, txt, color=c, fontsize=8.5)
    if i < len(stages)-1:
        draw_arrow(ax, x+1.0, 2.0, x+1.2, 2.0, color='#666')
# 语义丢失风险标注
for i in range(len(stages)):
    x = 1.1 + i * 2.2
    ax.text(x, 0.8, '语义丢失风险\nsemantics loss', fontsize=7.5, color='#C62828',
            ha='center', bbox=dict(boxstyle='round', facecolor='#FFEBEE', alpha=0.8))
ax.set_title('图28-3 良率字段的七层加工链路 / The Seven-Layer Processing Chain of a Yield Field',
             fontsize=12, fontweight='bold', pad=10)
fig.tight_layout()
fig.savefig(f'{IMG}\\flow_ch28_lineage_chain.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('图28-3 七层加工链路 saved')

# ============================================================
# 4. 图28-4: 工业语义层三层架构图 (28.4.2)
# ============================================================
fig, ax = plt.subplots(figsize=(13, 6.5))
ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')

# 三层(自下而上)
# 底层: 物理数据层
ax.add_patch(plt.Rectangle((0.8, 0.7), 10.4, 1.4, facecolor='#ECEFF1', edgecolor='#78909C', lw=1.5))
ax.text(1.0, 1.7, '物理数据层 Physical Data Layer', fontsize=10, fontweight='bold', color='#455A64')
physical = ['MES数据库', 'YMS数据库', 'FDC时序库', '检测图像存储']
for i, t in enumerate(physical):
    draw_flowbox(ax, 2.6 + i*2.2, 1.1, 2.0, 0.75, t, color='#78909C', fontsize=8.5)

# 中层: 工业语义层
ax.add_patch(plt.Rectangle((0.8, 3.2), 10.4, 1.9, facecolor='#E3F2FD', edgecolor='#1976D2', lw=2))
ax.text(1.0, 4.65, '工业语义层 Industrial Semantic Layer', fontsize=10, fontweight='bold', color='#0D47A1')
draw_flowbox(ax, 3.0, 4.1, 3.6, 1.0, '本体模型 Ontology\n(业务对象与关系)', color='#1976D2', fontsize=8.5)
draw_flowbox(ax, 7.6, 4.1, 3.6, 1.0, '语义服务 Semantic Services\n(对象查询/关系遍历/口径计算)', color='#42A5F5', fontsize=8.5)
# 权限控制点
ax.text(11.0, 2.4, '[权限控制点]\npermission control', fontsize=8, color='#C62828',
        ha='center', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#FFEBEE', edgecolor='#EF5350'))
draw_arrow(ax, 7.6, 2.1, 7.6, 3.2, color='#EF5350', lw=2)

# 顶层: AI应用层
ax.add_patch(plt.Rectangle((0.8, 6.2), 10.4, 1.4, facecolor='#E8F5E9', edgecolor='#2E7D32', lw=1.5))
ax.text(1.0, 7.2, 'AI应用层 AI Application Layer', fontsize=10, fontweight='bold', color='#1B5E20')
apps = ['良率分析', '虚拟量测', '根因分析RCA', 'LLM/Agent应用']
for i, t in enumerate(apps):
    draw_flowbox(ax, 2.6 + i*2.2, 6.55, 2.0, 0.75, t, color='#2E7D32', fontsize=8.5)

# 数据流箭头(上下)
draw_arrow(ax, 4.8, 2.1, 4.8, 3.2, color='#1976D2', lw=2)
draw_arrow(ax, 4.8, 5.1, 4.8, 6.2, color='#1976D2', lw=2)
ax.text(5.0, 2.7, '翻译为物理查询\n(translate)', fontsize=8, color='#1976D2')
ax.text(5.0, 5.6, '业务对象级结果\n(business objects)', fontsize=8, color='#2E7D32')

ax.set_title('图28-4 工业语义层定位 / Positioning of the Industrial Semantic Layer (三层结构)',
             fontsize=13, fontweight='bold', pad=10)
fig.tight_layout()
fig.savefig(f'{IMG}\\flow_ch28_semantic_layer.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('图28-4 语义层架构 saved')
print('Part 1 done.')

# ============================================================
# 5. 图28-5: 六大核心实体本体模型图 (28.4.3)
# ============================================================
fig, ax = plt.subplots(figsize=(12, 7))
ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')

# 六实体布点
entities = {
    'Lot':        (2.2, 6.0, '#1A237E', '批次\n加工管理单元'),
    'Wafer':      (6.0, 6.0, '#283593', '晶圆\n物理加工对象'),
    'Equipment':  (9.8, 6.0, '#1565C0', '设备(含Chamber)\n物理资源'),
    'ProcessStep':(2.2, 2.2, '#00838F', '工艺步骤\nRecipe执行'),
    'Defect':     (6.0, 2.2, '#E65100', '缺陷\n观测对象'),
    'Parameter':  (9.8, 2.2, '#558B2F', '工艺参数\n量测/FDC'),
}
for name, (x, y, c, desc) in entities.items():
    draw_flowbox(ax, x, y, 2.6, 1.2, f'{name}\n{desc}', color=c, fontsize=9)

# 关系边(标注在边上)
rels = [
    (2.2, 6.0, 6.0, 6.0, 'BELONGS_TO\n(属于)'),
    (6.0, 6.0, 9.8, 6.0, 'PROCESSED_ON\n(在设备上加工)'),
    (9.8, 6.0, 9.8, 2.2, 'EXECUTES\n(执行步骤)'),
    (2.2, 2.2, 6.0, 2.2, 'HAS_PARAMETER\n(有参数)'),
    (6.0, 2.2, 6.0, 6.0, 'OBSERVED_ON\n(缺陷在晶圆上)'),
    (2.2, 6.0, 2.2, 2.2, 'HAS_TEST_RESULT\n(有测试结果)'),
    (9.8, 6.0, 9.8, 2.2, ''),
]
# 重画: ProcessStep -> Equipment 是 Equipment EXECUTES ProcessStep, 用 Equipment 指向 ProcessStep? 修正为双向理解
# 简单起见: 实体间连线(带关系标签)
def edge(ax, x1, y1, x2, y2, label, color='#90A4AE'):
    ax.plot([x1, x2], [y1, y2], color=color, lw=1.5, alpha=0.9)
    mx, my = (x1+x2)/2, (y1+y2)/2
    ax.text(mx, my, label, fontsize=7, color='#455A64', ha='center',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white', alpha=0.85))

edge(ax, 3.5, 6.0, 4.7, 6.0, 'BELONGS_TO 属于')
edge(ax, 7.3, 6.0, 8.5, 6.0, 'PROCESSED_ON 加工')
edge(ax, 9.8, 5.4, 9.8, 2.8, 'EXECUTES 执行')
edge(ax, 3.5, 2.2, 4.7, 2.2, 'HAS_PARAMETER 参数')
edge(ax, 6.0, 5.4, 6.0, 2.8, 'OBSERVED_ON 观测')
edge(ax, 2.2, 5.4, 2.2, 2.8, 'HAS_TEST_RESULT 测试')

ax.text(6, 7.4, '六大核心实体与关系 / Six Core Entities & Relationships', fontsize=12,
        fontweight='bold', color='#1A237E')
ax.set_title('图28-5 半导体领域本体模型 / Semiconductor Domain Ontology (Lot-Wafer-Equipment-ProcessStep-Defect-Parameter)',
             fontsize=12, fontweight='bold', pad=8)
fig.tight_layout()
fig.savefig(f'{IMG}\\flow_ch28_ontology_model.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('图28-5 本体模型 saved')

# ============================================================
# 6. 图28-6: 知识图谱三层架构图 (28.4.4)
# ============================================================
fig, ax = plt.subplots(figsize=(13, 7))
ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')

# L1 血缘图谱(底层)
ax.add_patch(plt.Rectangle((0.8, 0.8), 10.4, 1.7, facecolor='#ECEFF1', edgecolor='#78909C', lw=1.5))
ax.text(1.0, 2.25, 'L1 数据血缘图谱 Data Lineage Graph\n(回答: 数据从哪来)', fontsize=9.5,
        fontweight='bold', color='#455A64')
l1 = ['表 Tables', '字段 Columns', '存储过程 SP', 'ETL作业', '报表 Reports']
for i, t in enumerate(l1):
    draw_flowbox(ax, 2.4 + i*2.0, 1.4, 1.8, 0.7, t, color='#78909C', fontsize=8)

# L2 业务知识图谱(中层)
ax.add_patch(plt.Rectangle((0.8, 3.4), 10.4, 1.7, facecolor='#E3F2FD', edgecolor='#1976D2', lw=1.5))
ax.text(1.0, 4.85, 'L2 业务知识图谱 Business Knowledge Graph\n(回答: 业务怎么运转)', fontsize=9.5,
        fontweight='bold', color='#0D47A1')
l2 = ['Lot', 'Wafer', 'Equipment', 'Defect', 'Rule/SOP', 'Case']
for i, t in enumerate(l2):
    draw_flowbox(ax, 1.8 + i*1.8, 4.0, 1.6, 0.7, t, color='#1976D2', fontsize=8)

# L3 可操作本体(顶层)
ax.add_patch(plt.Rectangle((0.8, 6.0), 10.4, 1.7, facecolor='#E8F5E9', edgecolor='#2E7D32', lw=2))
ax.text(1.0, 7.45, 'L3 可操作本体 Operational Ontology\n(回答: AI能做什么 · Agent只与L3交互)', fontsize=9.5,
        fontweight='bold', color='#1B5E20')
l3 = ['hold_lot\n冻结批次', 'create_workorder\n生成工单', 'release_lot\n放行', '本体对象\n查询/遍历']
for i, t in enumerate(l3):
    draw_flowbox(ax, 2.0 + i*2.4, 6.7, 2.1, 0.85, t, color='#2E7D32', fontsize=8)

# 层间箭头
for y1, y2 in [(2.5, 3.4), (5.1, 6.0)]:
    draw_arrow(ax, 6.0, y1, 6.0, y2, color='#90A4AE', lw=2)
ax.text(6.2, 2.95, '依赖 depends', fontsize=8, color='#78909C')
ax.text(6.2, 5.55, '依赖 depends', fontsize=8, color='#78909C')
# Agent 标注
ax.text(11.3, 6.7, 'Agent', fontsize=11, fontweight='bold', color='#2E7D32', ha='center',
        bbox=dict(boxstyle='round', facecolor='#C8E6C9', edgecolor='#2E7D32'))
draw_arrow(ax, 11.3, 6.2, 11.3, 5.1, color='#2E7D32', lw=2)
ax.text(11.4, 5.6, '经由L3消费\nconsume via L3', fontsize=7.5, color='#2E7D32')

ax.set_title('图28-6 知识图谱三层架构 / Three-Layer Knowledge-Graph Architecture (L1血缘→L2业务知识→L3可操作本体)',
             fontsize=12, fontweight='bold', pad=8)
fig.tight_layout()
fig.savefig(f'{IMG}\\flow_ch28_knowledge_layers.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('图28-6 知识图谱三层 saved')

# ============================================================
# 7. 图28-7: 多Agent协作流程图 (28.5.2)
# ============================================================
fig, ax = plt.subplots(figsize=(13, 4.5))
ax.set_xlim(0, 13); ax.set_ylim(0, 4); ax.axis('off')

stages = [
    ('感知Agent\nPerception\n(SPC/FDC信号→事件)', '#D32F2F'),
    ('诊断Agent\nDiagnosis\n(GraphRAG沿本体推理)', '#E64A19'),
    ('知识问答Agent\nKnowledge QA\n(向量RAG检索SOP/案例)', '#F57C00'),
    ('执行Agent\nExecution\n(建议动作)', '#2E7D32'),
    ('人工审批\nHuman Approval\n(工程师确认/驳回)', '#1565C0'),
]
for i, (txt, c) in enumerate(stages):
    x = 1.2 + i * 2.35
    draw_flowbox(ax, x, 2.6, 2.2, 1.4, txt, color=c, fontsize=8.5)
    if i < len(stages)-1:
        draw_arrow(ax, x+1.1, 2.6, x+1.25, 2.6, color='#666', lw=2)
# 执行动作 + 审计
draw_arrow(ax, 10.95, 2.6, 12.1, 2.6, color='#2E7D32', lw=2)
draw_flowbox(ax, 12.3, 2.6, 1.3, 1.4, '执行动作\nhold批次\n生成工单', color='#00838F', fontsize=8)
# 审计回环
draw_arrow(ax, 12.3, 1.8, 1.2, 1.8, color='#B0BEC5', lw=1.2)
draw_arrow(ax, 1.2, 1.8, 1.2, 1.9, color='#B0BEC5', lw=1.2)
ax.text(6.7, 1.5, '全链路审计日志 / full-pipeline audit log', fontsize=8.5, color='#607D8B',
        ha='center', bbox=dict(boxstyle='round', facecolor='white', edgecolor='#B0BEC5'))
ax.set_title('图28-7 多Agent协作架构 / Multi-Agent Collaboration Architecture (人在环路 Human-in-the-Loop)',
             fontsize=12, fontweight='bold', pad=10)
fig.tight_layout()
fig.savefig(f'{IMG}\\flow_ch28_agent_flow.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('图28-7 多Agent协作 saved')
print('Part 2 done.')

