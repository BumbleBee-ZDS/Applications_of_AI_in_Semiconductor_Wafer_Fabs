"""
第26章 Demo: 晶圆厂具身智能应用场景
AMHS智能搬运 + EFEM视觉抓取 + 移动巡检机器人
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(26)

fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))

# ============ 左: AMHS 天车动态路径规划 ============
ax = axes[0]
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
# 轨道网格
for i in range(0, 11, 2):
    ax.plot([i, i], [0, 10], color='#E0E0E0', lw=1)
    ax.plot([0, 10], [i, i], color='#E0E0E0', lw=1)
# 设备(障碍)
for (x, y) in [(2, 3), (2, 7), (6, 2), (6, 8), (8, 5)]:
    ax.add_patch(plt.Rectangle((x-0.4, y-0.4), 0.8, 0.8, facecolor='#B0BEC5', edgecolor='#78909C'))
    ax.text(x, y, '设备', ha='center', va='center', fontsize=7, color='#37474F')
# 路径: 起点(0,1) → 终点(10,1), 绕开拥堵区
path1_x = [0.5, 3.0, 4.5, 6.0, 8.0, 9.5]
path1_y = [1.0, 1.0, 3.5, 5.5, 7.0, 9.0]
ax.plot(path1_x, path1_y, color='#4CAF50', lw=2.5, marker='o', ms=4, label='智能动态路径(绕开拥堵)')
# 拥堵区
ax.add_patch(plt.Circle((3, 1.2), 0.9, color='#FFCDD2', alpha=0.7))
ax.text(3, 1.2, '拥堵', ha='center', fontsize=8, color='#C62828', fontweight='bold')
ax.annotate('', xy=(0.5, 1.0), xytext=(0.3, 0.3),
            arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
ax.text(0.5, 0.2, '起点', fontsize=8, color='#333')
ax.annotate('', xy=(9.5, 9.0), xytext=(9.7, 9.6),
            arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
ax.text(9.0, 9.7, '终点', fontsize=8, color='#333')
ax.set_title('AMHS天车/AGV智能搬运\n(动态路径规划+避障)', fontsize=11, fontweight='bold')

# ============ 中: EFEM 视觉引导抓取 ============
ax = axes[1]
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
# 机械臂示意
ax.plot([2, 4.5, 6.5], [8.5, 5.5, 3.5], color='#455A64', lw=5)
ax.plot([4.5], [5.5], marker='o', ms=10, color='#37474F')
ax.text(2.2, 8.9, '机械臂', fontsize=9, color='#37474F', fontweight='bold')
# FOUP 晶圆盒
ax.add_patch(plt.Rectangle((6.2, 0.8), 1.8, 1.4, facecolor='#FFF9C4', edgecolor='#F9A825', lw=2))
ax.text(7.1, 1.5, 'FOUP\n晶圆盒', ha='center', fontsize=8, color='#795548', fontweight='bold')
# 视觉检测框
ax.add_patch(plt.Rectangle((5.6, 0.4), 3.0, 2.2, fill=False, edgecolor='#4CAF50', lw=1.5, ls='--'))
ax.text(8.9, 2.8, '视觉引导抓取\n(识别姿态/位置)', fontsize=8, color='#2E7D32', ha='right')
# EFEM
ax.add_patch(plt.Rectangle((0.3, 2.8), 2.4, 2.2, facecolor='#E3F2FD', edgecolor='#1976D2', lw=2))
ax.text(1.5, 3.9, 'EFEM\n设备前端模块', ha='center', fontsize=8, color='#0D47A1', fontweight='bold')
ax.annotate('', xy=(2.0, 4.5), xytext=(3.4, 5.2),
            arrowprops=dict(arrowstyle='->', color='#1976D2', lw=1.5))
ax.set_title('洁净室机械臂/EFEM自动上下料\n(视觉引导+异常识别)', fontsize=11, fontweight='bold')

# ============ 右: 移动巡检机器人 ============
ax = axes[2]
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
# 机器人本体
ax.add_patch(plt.Circle((3, 2.5), 1.2, facecolor='#BBDEFB', edgecolor='#1565C0', lw=2))
ax.add_patch(plt.Circle((3, 3.4), 0.55, facecolor='#E3F2FD', edgecolor='#1565C0', lw=1.5))
ax.text(3, 3.4, '相机', ha='center', fontsize=7, color='#0D47A1')
ax.text(3, 1.0, '移动巡检机器人', ha='center', fontsize=8, color='#0D47A1', fontweight='bold')
# 设备(被巡检)
for (x, y, label) in [(7, 6, '设备A\n状态正常'), (8.5, 2, '设备B\n报警!')]:
    ax.add_patch(plt.Rectangle((x-1, y-0.7), 2, 1.4, facecolor='#C8E6C9', edgecolor='#388E3C', lw=1.5))
    ax.text(x, y, label, ha='center', fontsize=8)
# 巡检路径
ax.plot([3.5, 7, 8.5, 5, 3.5], [2.5, 5.5, 2, 1, 2.5], color='#FF9800', lw=2, ls='--')
ax.text(6.2, 4.2, '巡检路径', fontsize=8, color='#E65100', rotation=-25)
# 视觉识别结果
ax.annotate('识别到红灯: 设备B异常', xy=(8.5, 2.6), xytext=(5.5, 6.2),
            fontsize=8, color='#C62828', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#C62828', lw=1.2))
ax.set_title('移动操作机器人巡检维护\n(视觉识别+异常上报)', fontsize=11, fontweight='bold')

plt.suptitle('第26章 Demo: 晶圆厂具身智能应用场景——搬运 / 上下料 / 巡检', fontsize=13, fontweight='bold', y=1.0)
plt.tight_layout()
plt.savefig(r'h:\code\traework\AI在半导体晶圆厂的应用\zh-CN\images\demo_ch26_embodied_ai.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Demo Ch26 Embodied AI saved.')
