"""
🔬 Q-Learning 智能派工 / RL-Based Dispatch
对应第16章(行为主义)与第12章智能排程
Chapters 16 (Behaviorism) & 12 (Smart Scheduling)

微型派工环境: 2台设备(快/慢), 批次随机到达, Q-Learning 学习派工策略
Micro dispatch env: 2 tools (fast/slow), random arrivals, Q-learning dispatch policy
"""
import os
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(16)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(OUT, exist_ok=True)

# ---------- 环境: 派工 MDP / environment ----------
N_QUEUE_MAX = 5          # 队列上限 queue cap
TOOL_SPEED = [1.0, 0.4]  # 设备处理速度(批次/时) tool speeds (fast vs slow)
ARRIVAL_P = 0.85         # 每步到达概率 arrival probability per step

def reset():
    return (0, 0)

def step(state, action):
    """执行派工: 批次进队列, 两台设备各处理一批 / dispatch one step"""
    q0, q1 = state
    # 到达批次加入所选设备队列
    if np.random.rand() < ARRIVAL_P:
        if action == 0:
            q0 = min(q0 + 1, N_QUEUE_MAX)
        else:
            q1 = min(q1 + 1, N_QUEUE_MAX)
    # 设备处理(以概率 = 速度)
    done0 = np.random.rand() < TOOL_SPEED[0] and q0 > 0
    done1 = np.random.rand() < TOOL_SPEED[1] and q1 > 0
    q0 = max(q0 - int(done0), 0)
    q1 = max(q1 - int(done1), 0)
    # 奖励: 完成批次 +10, 每在队批次 -1(等待成本)
    reward = 10 * (int(done0) + int(done1)) - (q0 + q1)
    return (q0, q1), reward

# ---------- Q-Learning 训练 / training ----------
def train_q(episodes=2000, alpha=0.1, gamma=0.95, epsilon=0.2):
    Q = np.zeros((N_QUEUE_MAX + 1, N_QUEUE_MAX + 1, 2))
    history = []
    for _ in range(episodes):
        s = reset()
        total = 0.0
        for step_i in range(120):  # 每回合 120 步 / 120 steps per episode
            q0, q1 = s
            if np.random.rand() < epsilon:
                a = np.random.randint(2)
            else:
                a = int(np.argmax(Q[q0, q1]))
            s2, r = step(s, a)
            q0b, q1b = s2
            Q[q0, q1, a] += alpha * (r + gamma * np.max(Q[q0b, q1b]) - Q[q0, q1, a])
            s = s2
            total += r
        history.append(total)
    return Q, history

Q, history = train_q()
# 滑动平均平滑 / moving-average smoothing
window = 50
smooth = np.convolve(history, np.ones(window)/window, mode='valid')

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(history, color='lightblue', lw=0.6, alpha=0.6, label='原始 raw')
ax.plot(smooth, color='#1565C0', lw=2, label=f'滑动平均 moving avg (w={window})')
ax.set_xlabel('回合 episode'); ax.set_ylabel('回合总奖励 total reward')
ax.set_title('Q-Learning 学习曲线 / Learning Curve (奖励随训练提升)')
ax.legend(); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'learning_curve.png'), dpi=140)
plt.close(fig)

# ---------- 策略对比: Q 策略 vs 贪心 / policy comparison ----------
def run_policy(policy, steps=120, seed=1):
    rng = np.random.default_rng(seed)
    q0 = q1 = 0
    events = []  # (t, tool, type)
    total_reward = 0.0
    t = 0
    while t < steps:
        s = (q0, q1)
        a = int(policy(Q, q0, q1)) if callable(policy) else policy(Q, q0, q1)
        # 简化: 记录队列长度变化作为调度效果
        if rng.random() < ARRIVAL_P:
            if a == 0:
                q0 = min(q0 + 1, N_QUEUE_MAX)
            else:
                q1 = min(q1 + 1, N_QUEUE_MAX)
        d0 = rng.random() < TOOL_SPEED[0] and q0 > 0
        d1 = rng.random() < TOOL_SPEED[1] and q1 > 0
        if d0:
            events.append((t, 'tool0(快)', '完成'))
            q0 -= 1
        if d1:
            events.append((t, 'tool1(慢)', '完成'))
            q1 -= 1
        total_reward += 10*(int(d0)+int(d1)) - (q0+q1)
        t += 1
    return events, total_reward

def random_policy(Q, q0, q1):
    """随机基线: 随机选择设备(明显次优, 会把批次塞给慢设备)
    random baseline: pick a tool at random (clearly suboptimal)"""
    return int(np.random.rand() < 0.5)

ev_q, r_q = run_policy(lambda Q, q0, q1: int(np.argmax(Q[q0, q1])))
ev_r, r_r = run_policy(random_policy)

print('=' * 60)
print('[Q-Learning] 训练完成, 末100回合平均奖励: {:.1f}'.format(np.mean(history[-100:])))
print(f'[对比] Q策略总奖励: {r_q:.1f} vs 随机派工: {r_r:.1f}  (提升 {r_q-r_r:.1f})')
print('  结论: Q-Learning 学会按设备负载均衡派工, 明显优于随机派工。')
print('  Takeaway: Q-learning learns load-balancing dispatch, beating random dispatch.')

# 甘特图对比 / Gantt comparison
fig, axes = plt.subplots(2, 1, figsize=(9, 5))
for ax, events, title in [(axes[0], ev_q, 'Q-Learning 派工策略'), (axes[1], ev_r, '随机派工 random')]:
    for (t, tool, typ) in events:
        y = 0 if tool == 'tool0(快)' else 1
        ax.barh(y, 1, left=t, height=0.6, color='#4CAF50' if y == 0 else '#FF9800')
    ax.set_yticks([0, 1]); ax.set_yticklabels(['设备0 快', '设备1 慢'])
    ax.set_xlim(0, 60); ax.set_xlabel('时间步 time step')
    ax.set_title(title)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'gantt.png'), dpi=140)
plt.close(fig)

print('[可视化] 图片输出于 / Figures saved to:', OUT)
