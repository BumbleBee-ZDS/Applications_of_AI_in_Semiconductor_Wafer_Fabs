"""
part3c/d/e 流程图生成脚本
第11章 建设期业务流 + 第12章 成熟期任务联动 + 第13章 转型期信任闭环
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def draw_flowbox(ax, x, y, w, h, text, color='#2196F3', text_color='white', fontsize=9):
    box = mpatches.FancyBboxPatch((x - w/2, y - h/2), w, h,
                                   boxstyle="round,pad=0.15",
                                   facecolor=color, edgecolor=color, alpha=0.9, linewidth=2)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight='bold', color=text_color, wrap=True)
    return (x, y, w, h)

def draw_arrow(ax, x1, y1, x2, y2, color='#666'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.8))

# ============================================================
# 1. Ch11: 建设期业务主线
# ============================================================
fig, ax = plt.subplots(figsize=(16, 4.5))
ax.set_xlim(0, 16); ax.set_ylim(0, 4.5); ax.axis('off')

stages = [
    (1.6, 2.5, '设备通线\n(安装/验收/匹配)', '#2196F3'),
    (4.6, 2.5, '良率分析\n(晶圆图/RCA/模型)', '#FF9800'),
    (7.6, 2.5, '缺陷检测\n(扫描/ADC/新类发现)', '#F44336'),
    (10.6, 2.5, '虚拟量测\n(FDC预测/免检决策)', '#4CAF50'),
    (13.6, 2.5, '爬坡迭代\n(良率/产能双爬坡)', '#9C27B0'),
]
for x, y, text, color in stages:
    draw_flowbox(ax, x, y, 2.4, 1.6, text, color=color, fontsize=9)
for i in range(len(stages)-1):
    draw_arrow(ax, stages[i][0]+1.2, 2.5, stages[i+1][0]-1.2, 2.5)
draw_arrow(ax, 14.8, 1.5, 1.6, 1.5, color='#999')
draw_arrow(ax, 1.6, 1.5, 1.6, 1.68, color='#999')
ax.text(8.2, 0.9, '建设期数据闭环: 缺陷检测发现问题 → 良率分析定位根因 → 虚拟量测放大学习样本', ha='center',
        fontsize=10, color='#555', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
ax.set_title('第11章: 建设期与爬坡期业务主线', fontsize=14, fontweight='bold', pad=12)
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch11_construction_flow.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Flow Ch11 Construction saved.')

# ============================================================
# 2. Ch12: 成熟期三任务联动
# ============================================================
fig, ax = plt.subplots(figsize=(14, 6))
ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis('off')

# 三个任务框
draw_flowbox(ax, 3, 4.2, 4.2, 1.6, '智能排程\n(资源分配/动态派工)', '#2196F3', fontsize=10)
draw_flowbox(ax, 9, 4.2, 4.2, 1.6, '预测性维护\n(设备可用率/减少停机)', '#FF9800', fontsize=10)
draw_flowbox(ax, 6, 2.0, 4.6, 1.6, '能源管理\n(能耗成本/绿色制造)', '#4CAF50', fontsize=10)

# 联动箭头
draw_arrow(ax, 5.2, 4.2, 6.8, 4.2, color='#333')
ax.text(6.0, 4.55, '排程避开\n维护停机', ha='center', fontsize=8.5, color='#333')
draw_arrow(ax, 7.9, 3.3, 7.2, 2.9, color='#333')
ax.text(8.3, 3.05, '维护时机\n与排程联动', ha='center', fontsize=8.5, color='#333')
draw_arrow(ax, 5.0, 2.9, 4.1, 3.3, color='#333')
ax.text(4.1, 2.75, '能耗成本\n纳入排程目标', ha='center', fontsize=8.5, color='#333')

ax.text(6, 5.6, '成熟量产期: 效率×韧性 三角', ha='center', fontsize=13, fontweight='bold', color='#283593')
ax.text(6, 0.55, '共同目标: 成本更低 · 产出更多 · 运营更稳(ROI导向)', ha='center',
        fontsize=10, color='#555', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch12_mature_ops_flow.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Flow Ch12 Mature Ops saved.')

# ============================================================
# 3. Ch13: 转型期信任闭环
# ============================================================
fig, ax = plt.subplots(figsize=(14, 6))
ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis('off')

draw_flowbox(ax, 1.8, 3.0, 3.0, 1.7, '客户\n(设计/IP)', '#F44336', fontsize=10)
draw_flowbox(ax, 6.0, 4.4, 3.4, 1.7, 'NPI协同\n(联合开发)', '#FF9800', fontsize=10)
draw_flowbox(ax, 10.2, 3.0, 3.0, 1.7, '制造交付\n(晶圆产出)', '#2196F3', fontsize=10)
draw_flowbox(ax, 6.0, 1.6, 4.6, 1.7, '数据安全\n(租户隔离/全流程保障)', '#4CAF50', fontsize=10)

draw_arrow(ax, 3.3, 3.4, 4.4, 4.1, color='#333')
ax.text(3.6, 4.2, '设计', ha='center', fontsize=9)
draw_arrow(ax, 7.7, 4.1, 8.8, 3.4, color='#333')
ax.text(8.6, 4.15, '试产反馈', ha='center', fontsize=9)
draw_arrow(ax, 8.8, 2.6, 7.7, 2.2, color='#333')
ax.text(8.7, 2.35, '交付', ha='center', fontsize=9)
# 数据安全包围
draw_arrow(ax, 3.3, 2.6, 1.8, 2.0, color='#999', )
ax.text(1.0, 1.15, '供应链透明化\n(端到端可见/Clear-to-Build)', fontsize=9, color='#0D47A1', fontweight='bold')
draw_arrow(ax, 10.2, 2.0, 10.2, 2.15, color='#999')
ax.text(6.0, 5.75, '代工服务转型期: 信任闭环(数据安全贯穿全流程)', ha='center',
        fontsize=13, fontweight='bold', color='#283593')
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\flow_ch13_foundry_service_flow.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Flow Ch13 Foundry Service saved.')
