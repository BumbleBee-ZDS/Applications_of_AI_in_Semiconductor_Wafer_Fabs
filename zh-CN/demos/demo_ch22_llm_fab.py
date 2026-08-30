"""
第22章 Demo: LLM在晶圆厂的应用——SPEC检索、良率分析报告生成与RAG架构
展示大语言模型在工艺文档管理和良率分析中的实际效果
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHeI', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)

fig = plt.figure(figsize=(20, 14))
gs = GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# ========== 左上: RAG架构流程 ==========
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.set_title('RAG架构: LLM + 领域知识检索', fontsize=12, fontweight='bold', color='#2196F3')

steps = [
    (5, 9, '用户提问: "Step23光刻套刻精度超标原因?"', '#E3F2FD', '#2196F3'),
    (2, 7, '查询向量化\n(Embedding)', '#FFF3E0', '#FF9800'),
    (5, 7, '知识库检索\n(SPEC + 历史\n缺陷库 + KG)', '#E8F5E9', '#4CAF50'),
    (8, 7, 'Top-K相关\n文档片段', '#F3E5F5', '#9C27B0'),
    (5, 5, 'Prompt组装\n(问题 + 检索上下文)', '#FFFDE7', '#FBC02D'),
    (5, 3, 'LLM生成\n(基于上下文回答)', '#E3F2FD', '#2196F3'),
    (5, 1, '回答 + 引用来源\n(可追溯)', '#E8F5E9', '#4CAF50'),
]
for x, y, label, face, edge in steps:
    box = FancyBboxPatch((x-1.8, y-0.5), 3.6, 1, boxstyle='round,pad=0.1',
                         facecolor=face, edgecolor=edge, linewidth=1.5)
    ax1.add_patch(box)
    ax1.text(x, y, label, ha='center', va='center', fontsize=7.5, fontweight='bold')

arrows = [(5, 8.5, 5, 7.5), (2, 6.5, 4, 6.5), (8, 6.5, 6, 6.5),
          (5, 6.5, 5, 5.5), (5, 4.5, 5, 3.5), (5, 2.5, 5, 1.5)]
for x1, y1, x2, y2 in arrows:
    ax1.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

ax1.axis('off')

# ========== 中上: 检索准确率对比 ==========
ax2 = fig.add_subplot(gs[0, 1])
query_types = ['SPEC条款\n检索', '设备手册\n问答', '工艺参数\n查询', '异常报告\n生成', '跨文档\n推理']
keyword_search = [65, 60, 58, 45, 30]
vector_search = [78, 75, 72, 65, 55]
rag_search = [94, 91, 93, 88, 85]

x = np.arange(len(query_types))
w = 0.25
ax2.bar(x - w, keyword_search, w, label='关键词搜索', color='#FF6B6B', alpha=0.8)
ax2.bar(x, vector_search, w, label='向量检索', color='#FF9800', alpha=0.8)
ax2.bar(x + w, rag_search, w, label='RAG (LLM+检索)', color='#2196F3', alpha=0.9)

for i in range(len(query_types)):
    ax2.text(i + w, rag_search[i] + 1, f'{rag_search[i]}%', ha='center', fontsize=8, fontweight='bold')

ax2.set_xticks(x)
ax2.set_xticklabels(query_types, fontsize=9)
ax2.set_ylabel('准确率 (%)', fontsize=10)
ax2.set_title('RAG vs 关键词 vs 向量检索\n(SPEC/手册/工艺查询)', fontsize=11, fontweight='bold')
ax2.legend(fontsize=9)
ax2.set_ylim(0, 110)
ax2.grid(axis='y', alpha=0.3)

# ========== 右上: 幻觉率对比 ==========
ax3 = fig.add_subplot(gs[0, 2])
methods = ['纯LLM\n(无RAG)', 'LLM+\n简单检索', 'LLM+KG+\nRAG', 'LLM+KG+RAG\n+自验证']
hallucination_rate = [22, 12, 4, 0.8]
answer_latency = [2.1, 3.5, 5.2, 8.8]

x = np.arange(len(methods))
ax3_twin = ax3.twinx()

bars1 = ax3.bar(x - 0.15, hallucination_rate, 0.3, label='幻觉率(%)', color='#F44336', alpha=0.8)
bars2 = ax3_twin.bar(x + 0.15, answer_latency, 0.3, label='延迟(s)', color='#2196F3', alpha=0.8)

for i in range(len(methods)):
    ax3.text(x[i] - 0.15, hallucination_rate[i] + 0.5, f'{hallucination_rate[i]}%',
             ha='center', fontsize=9, fontweight='bold')
    ax3_twin.text(x[i] + 0.15, answer_latency[i] + 0.2, f'{answer_latency[i]}s',
                  ha='center', fontsize=9, fontweight='bold')

ax3.set_xticks(x)
ax3.set_xticklabels(methods, fontsize=9)
ax3.set_ylabel('幻觉率 (%)', fontsize=10, color='#F44336')
ax3_twin.set_ylabel('响应延迟 (s)', fontsize=10, color='#2196F3')
ax3.set_title('幻觉抑制 vs 响应延迟\n(准确率-延迟权衡)', fontsize=11, fontweight='bold')
ax3.legend(loc='upper left', fontsize=9)
ax3_twin.legend(loc='upper right', fontsize=9)
ax3.grid(axis='y', alpha=0.3)

# ========== 左中: 良率报告自动生成 ==========
ax4 = fig.add_subplot(gs[1, 0])
report_sections = ['数据汇总\n与预处理', '统计分析\n与趋势', '异常检测\n与分类', '根因推理\n与验证',
                   '改善建议\n生成', '报告排版\n与输出']
manual_time = [45, 60, 40, 90, 30, 25]  # minutes
llm_time = [3, 5, 2, 8, 3, 1]

x = np.arange(len(report_sections))
w = 0.35
ax4.barh(x - w/2, manual_time, w, label='人工撰写', color='#FF6B6B', alpha=0.8)
ax4.barh(x + w/2, llm_time, w, label='LLM生成', color='#2196F3', alpha=0.9)

for i in range(len(report_sections)):
    speedup = manual_time[i] / llm_time[i]
    ax4.text(max(manual_time[i], llm_time[i]) + 2, x[i], f'{speedup:.0f}x',
             va='center', fontsize=9, fontweight='bold', color='#2196F3')

ax4.set_yticks(x)
ax4.set_yticklabels(report_sections, fontsize=9)
ax4.set_xlabel('耗时 (分钟)', fontsize=10)
ax4.set_title('良率分析报告生成: 人工 vs LLM\n(加速15-30倍)', fontsize=11, fontweight='bold')
ax4.legend(fontsize=9)
ax4.grid(axis='x', alpha=0.3)

# ========== 中中: LLM自然语言交互示例 ==========
ax5 = fig.add_subplot(gs[1, 1])
ax5.set_xlim(0, 10)
ax5.set_ylim(0, 10)
ax5.set_title('LLM自然语言数据交互', fontsize=12, fontweight='bold', color='#2196F3')

# 用户问题
q_box = FancyBboxPatch((0.3, 7.5), 5, 1.5, boxstyle='round,pad=0.15',
                       facecolor='#E3F2FD', edgecolor='#2196F3', linewidth=1.5)
ax5.add_patch(q_box)
ax5.text(0.5, 8.6, '[用户]', fontsize=8, fontweight='bold', color='#2196F3')
ax5.text(0.5, 8.0, '"最近一周Tool-A03的\nStep23良率趋势如何?"', fontsize=9, va='center')

# LLM处理
proc_box = FancyBboxPatch((0.3, 5), 9.4, 2, boxstyle='round,pad=0.15',
                           facecolor='#FFF3E0', edgecolor='#FF9800', linewidth=1.5)
ax5.add_patch(proc_box)
ax5.text(0.5, 6.6, '[LLM解析]', fontsize=8, fontweight='bold', color='#FF9800')
ax5.text(0.5, 6.1, '1. 识别实体: Tool=A03, Step=23, 时间=最近7天', fontsize=8.5)
ax5.text(0.5, 5.7, '2. 生成SQL: SELECT yield FROM lot_data', fontsize=8.5)
ax5.text(0.5, 5.3, '   WHERE tool_id="A03" AND step=23 AND date >= NOW()-7', fontsize=8)

# LLM回答
a_box = FancyBboxPatch((0.3, 1), 9.4, 3.5, boxstyle='round,pad=0.15',
                        facecolor='#E8F5E9', edgecolor='#4CAF50', linewidth=1.5)
ax5.add_patch(a_box)
ax5.text(0.5, 4.1, '[LLM回答]', fontsize=8, fontweight='bold', color='#4CAF50')
answer_lines = [
    'Tool-A03在最近7天的Step23良率:',
    '- 整体均值: 91.3% (目标: 92%)',
    '- 趋势: 前5天稳定(91-93%), 第6天降至87%',
    '- 异常: 第6天检测到SPC超标 (2.8sigma)',
    '- 关联: 同期Tool-A03对准系统温度偏高+2.3C',
    '- 建议: 检查冷却系统, 参考SPEC-23-SEC04',
]
for i, line in enumerate(answer_lines):
    ax5.text(0.5, 3.7 - i * 0.4, line, fontsize=8.5)

# 箭头
ax5.annotate('', xy=(0.5, 7), xytext=(0.5, 7.5),
            arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
ax5.annotate('', xy=(0.5, 4.5), xytext=(0.5, 5),
            arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

ax5.axis('off')

# ========== 右中: 跨系统数据问答 ==========
ax6 = fig.add_subplot(gs[1, 2])
systems = ['MES\n生产数据', 'FDC\n设备数据', 'SPC\n质控数据', 'SPEC\n工艺规范', 'KG\n知识图谱', 'CP/FT\n测试数据']
access_traditional = [100, 85, 90, 70, 30, 80]  # 人工查询覆盖率
access_llm = [100, 100, 100, 95, 90, 100]

x = np.arange(len(systems))
w = 0.35
ax6.bar(x - w/2, access_traditional, w, label='人工查询(覆盖率)', color='#FF6B6B', alpha=0.8)
ax6.bar(x + w/2, access_llm, w, label='LLM统一访问(覆盖率)', color='#2196F3', alpha=0.9)

ax6.set_xticks(x)
ax6.set_xticklabels(systems, fontsize=8)
ax6.set_ylabel('数据覆盖率 (%)', fontsize=10)
ax6.set_title('LLM跨系统统一数据访问\n(消除数据孤岛)', fontsize=11, fontweight='bold')
ax6.legend(fontsize=9)
ax6.set_ylim(0, 115)
ax6.grid(axis='y', alpha=0.3)

# ========== 底部: LLM应用效果汇总 ==========
ax7 = fig.add_subplot(gs[2, :])
applications = ['SPEC智能\n检索', '设备手册\n问答', '异常报告\n自动生成', '良率报告\n自动撰写',
                '跨系统\n数据问答', '工单\n智能管理', '生产报表\n自动化', '工艺变更\n评估']
manual_time_all = [30, 25, 60, 120, 90, 45, 60, 180]  # 分钟
llm_time_all = [2, 3, 5, 8, 5, 3, 4, 15]
accuracy = [94, 91, 92, 95, 88, 90, 93, 87]

x = np.arange(len(applications))
w = 0.3
ax7_twin = ax7.twinx()

bars1 = ax7.bar(x - w/2, manual_time_all, w, label='人工耗时(分钟)', color='#FF6B6B', alpha=0.7)
bars2 = ax7.bar(x + w/2, llm_time_all, w, label='LLM耗时(分钟)', color='#2196F3', alpha=0.9)
line1 = ax7_twin.plot(x, accuracy, 'o-', color='#4CAF50', linewidth=2.5, markersize=8, label='LLM准确率(%)')

for i in range(len(applications)):
    speedup = manual_time_all[i] / llm_time_all[i] if llm_time_all[i] > 0 else 0
    ax7.text(i, max(manual_time_all[i], llm_time_all[i]) + 3, f'{speedup:.0f}x',
             ha='center', fontsize=8, fontweight='bold', color='#9C27B0')
    ax7_twin.text(i, accuracy[i] + 1, f'{accuracy[i]}%', ha='center', fontsize=8,
                  fontweight='bold', color='#4CAF50')

ax7.set_xticks(x)
ax7.set_xticklabels(applications, fontsize=9)
ax7.set_ylabel('耗时 (分钟)', fontsize=11)
ax7_twin.set_ylabel('准确率 (%)', fontsize=11, color='#4CAF50')
ax7.set_title('LLM在晶圆厂八大应用场景: 效率与准确率对比', fontsize=13, fontweight='bold')
ax7.legend(loc='upper left', fontsize=10)
ax7_twin.legend(loc='upper right', fontsize=10)
ax7.set_ylim(0, 200)
ax7_twin.set_ylim(0, 110)
ax7.grid(axis='y', alpha=0.3)

fig.suptitle('第22章 Demo：LLM在晶圆厂的应用——从SPEC检索到智能报告生成',
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch22_llm_fab.png',
            dpi=150, bbox_inches='tight', facecolor='white')
print("Ch22 LLM demo saved.")
plt.close()
