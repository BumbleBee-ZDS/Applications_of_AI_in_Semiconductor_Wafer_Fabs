"""
第13章 Demo: 代工服务转型期三大任务
NPI协同 + 数据安全 + 供应链透明化
"""
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(13)

fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))

# ============ 左: NPI协同——多客户并行甘特图 ============
ax = axes[0]
clients = ['客户A (AI芯片)', '客户B (汽车MCU)', '客户C (服务器SoC)', '客户D (电源IC)']
starts = [0, 2, 4, 7]
durs = [6, 5, 5, 4]
colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0']
for i, (c, s, d, col) in enumerate(zip(clients, starts, durs, colors)):
    ax.barh(i, d, left=s, color=col, alpha=0.85, height=0.55)
    ax.text(s+d/2, i, f'试产 {d}周', ha='center', va='center', color='white', fontsize=9, fontweight='bold')
ax.set_yticks(range(len(clients)))
ax.set_yticklabels(clients, fontsize=9)
ax.set_xlabel('NPI 周期 (周)', fontsize=10)
ax.set_title('NPI协同: 多客户并行试产排程\n(动态分配试产线/实验晶圆)', fontsize=11, fontweight='bold')
ax.grid(alpha=0.3, axis='x')

# ============ 中: 数据安全——租户隔离示意 ============
ax = axes[1]
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
ax.add_patch(plt.Rectangle((0.5, 0.5), 4, 9, facecolor='#E3F2FD', edgecolor='#2196F3', lw=1.5))
ax.add_patch(plt.Rectangle((5.5, 0.5), 4, 9, facecolor='#E8F5E9', edgecolor='#4CAF50', lw=1.5))
ax.text(2.5, 8.6, '客户A 数据域', ha='center', fontsize=10, fontweight='bold', color='#0D47A1')
ax.text(7.5, 8.6, '客户B 数据域', ha='center', fontsize=10, fontweight='bold', color='#1B5E20')
for i, txt in enumerate(['版图(GDS)', '工艺参数', '良率数据']):
    ax.text(2.5, 6.5-i*1.4, '· ' + txt, ha='center', fontsize=9, color='#333')
    ax.text(7.5, 6.5-i*1.4, '· ' + txt, ha='center', fontsize=9, color='#333')
ax.text(5.0, 4.2, '隔离墙', ha='center', fontsize=9, color='#F44336', fontweight='bold')
ax.plot([5, 5], [1.2, 9.2], color='#F44336', lw=3, ls='--')
ax.text(5.0, 1.6, '租户隔离 + 访问控制 + 审计', ha='center', fontsize=9, color='#555')
ax.set_title('数据安全: 多客户租户隔离\n(数据防泄漏=代工生命线)', fontsize=11, fontweight='bold')

# ============ 右: 供应链透明化——端到端可见 ============
ax = axes[2]
nodes = ['原材料', '设备/备件', '在制品WIP', '晶圆产出', '封测', '客户交付']
pos_x = np.arange(len(nodes))
ax.plot(pos_x, np.full(len(nodes), 5), color='#B0BEC5', lw=2)
for i, node in enumerate(nodes):
    ax.add_patch(plt.Circle((i, 5), 0.35, color='#4FC3F7', zorder=3))
    ax.text(i, 5.55, node, ha='center', fontsize=9, fontweight='bold')
    ax.text(i, 4.5, '可见', ha='center', fontsize=8, color='#2E7D32')
ax.text(2.5, 6.6, '供应链端到端可视化', ha='center', fontsize=11, fontweight='bold', color='#283593')
ax.text(2.5, 0.9, '风险预警: 关键材料单一供应商依赖\nClear-to-Build: 交付承诺实时确认', ha='center',
        fontsize=9, color='#555',
        bbox=dict(boxstyle='round', facecolor='#FFF9C4', alpha=0.9))
ax.set_xlim(-0.5, len(nodes)-0.5); ax.set_ylim(0.5, 7.2); ax.axis('off')

plt.suptitle('第13章 Demo: 代工服务转型期三大任务——NPI协同 / 数据安全 / 供应链透明化', fontsize=13, fontweight='bold', y=1.0)
plt.tight_layout()
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch13_foundry_service.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Demo Ch13 Foundry Service saved.')
