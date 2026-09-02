"""
🔬 Q-Learning 智能派工 - Web 前端 / RL Dispatch - Web UI
双语 / Bilingual
运行: Run:  python web_app.py  ->  http://127.0.0.1:5004
"""
import io
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, request, render_template_string

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(16)

app = Flask(__name__)
N_QUEUE_MAX = 5
TOOL_SPEED = [1.0, 0.4]
ARRIVAL_P = 0.85

# ---------- 环境与训练(启动时一次) ----------
def reset():
    return (0, 0)

def step(state, action):
    q0, q1 = state
    if np.random.rand() < ARRIVAL_P:
        if action == 0:
            q0 = min(q0 + 1, N_QUEUE_MAX)
        else:
            q1 = min(q1 + 1, N_QUEUE_MAX)
    d0 = np.random.rand() < TOOL_SPEED[0] and q0 > 0
    d1 = np.random.rand() < TOOL_SPEED[1] and q1 > 0
    q0 = max(q0 - int(d0), 0)
    q1 = max(q1 - int(d1), 0)
    reward = 10 * (int(d0) + int(d1)) - (q0 + q1)
    return (q0, q1), reward

def train_q(episodes=2000, alpha=0.1, gamma=0.95, epsilon=0.2):
    Q = np.zeros((N_QUEUE_MAX + 1, N_QUEUE_MAX + 1, 2))
    history = []
    for _ in range(episodes):
        s = reset()
        total = 0.0
        for _ in range(120):
            q0, q1 = s
            a = np.random.randint(2) if np.random.rand() < epsilon else int(np.argmax(Q[q0, q1]))
            s2, r = step(s, a)
            q0b, q1b = s2
            Q[q0, q1, a] += alpha * (r + gamma * np.max(Q[q0b, q1b]) - Q[q0, q1, a])
            s = s2
            total += r
        history.append(total)
    return Q, history

Q, history = train_q()

def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=95, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

def learning_curve_img():
    window = 50
    smooth = np.convolve(history, np.ones(window)/window, mode='valid')
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(history, color='lightblue', lw=0.6, alpha=0.6, label='原始 raw')
    ax.plot(smooth, color='#1565C0', lw=2, label='滑动平均 moving avg')
    ax.set_xlabel('回合 episode'); ax.set_ylabel('回合总奖励 total reward')
    ax.set_title('Q-Learning 学习曲线 / Learning Curve')
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig_to_b64(fig)

def run_policy(policy, steps=120, seed=1):
    rng = np.random.default_rng(seed)
    q0 = q1 = 0
    events = []
    total = 0.0
    for t in range(steps):
        a = int(policy(Q, q0, q1))
        if rng.random() < ARRIVAL_P:
            if a == 0:
                q0 = min(q0 + 1, N_QUEUE_MAX)
            else:
                q1 = min(q1 + 1, N_QUEUE_MAX)
        d0 = rng.random() < TOOL_SPEED[0] and q0 > 0
        d1 = rng.random() < TOOL_SPEED[1] and q1 > 0
        if d0:
            events.append((t, 0)); q0 -= 1
        if d1:
            events.append((t, 1)); q1 -= 1
        total += 10*(int(d0)+int(d1)) - (q0+q1)
    return events, total

def gantt_img():
    ev_q, r_q = run_policy(lambda Q, q0, q1: int(np.argmax(Q[q0, q1])))
    ev_r, r_r = run_policy(lambda Q, q0, q1: int(np.random.rand() < 0.5))
    fig, axes = plt.subplots(2, 1, figsize=(8, 4.5))
    for ax, events, title in [(axes[0], ev_q, f'Q-Learning (奖励 {r_q:.0f})'), (axes[1], ev_r, f'随机派工 (奖励 {r_r:.0f})')]:
        for (t, tool) in events:
            ax.barh(tool, 1, left=t, height=0.6, color='#4CAF50' if tool == 0 else '#FF9800')
        ax.set_yticks([0, 1]); ax.set_yticklabels(['设备0 快', '设备1 慢'])
        ax.set_xlim(0, 120); ax.set_title(title, fontsize=10)
    fig.tight_layout()
    return fig_to_b64(fig)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>Q-Learning 智能派工 / RL Dispatch</title>
<style>
 body{font-family:'Microsoft YaHei',sans-serif;max-width:880px;margin:20px auto;padding:0 16px;color:#333}
 h1{color:#1a237e;text-align:center} .en{color:#888;font-size:13px;text-align:center}
 img{width:100%;border-radius:6px;margin-top:8px;border:1px solid #eee}
 .row{display:flex;gap:14px;flex-wrap:wrap} .col{flex:1;min-width:320px}
 .panel{background:#f5f7ff;border:1px solid #d5dbf5;border-radius:8px;padding:12px;margin:12px 0;font-size:14px}
</style></head>
<body>
<h1>🎯 Q-Learning 智能派工 / RL-Based Dispatch</h1>
<p class="en">《AI在半导体晶圆厂的应用》第16章配套实验 · 2台设备(快/慢) 随机到达批次</p>
<div class="panel">
 状态 state = (设备0队列, 设备1队列) &nbsp;|&nbsp; 动作 action = 派给哪台设备 &nbsp;|&nbsp;
 奖励 reward = 完成×10 − 排队等待
</div>
<div class="row">
 <div class="col"><img src="data:image/png;base64,{{lc}}"><p class="en">① 学习曲线: 奖励随训练提升</p></div>
 <div class="col"><img src="data:image/png;base64,{{gt}}"><p class="en">② Q策略 vs 随机派工甘特图</p></div>
</div>
<p class="en" style="text-align:center">运行: python web_app.py (端口5004) · 命令行版: python rl_dispatch_basic.py</p>
</body></html>"""

@app.route('/')
def index():
    return render_template_string(HTML, lc=learning_curve_img(), gt=gantt_img())

if __name__ == '__main__':
    print('Q-Learning 智能派工 Web 界面 / RL Dispatch Web UI: http://127.0.0.1:5004')
    app.run(debug=True, port=5004)
