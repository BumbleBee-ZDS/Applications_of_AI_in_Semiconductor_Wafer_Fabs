"""
🔬 反思型 Agent - Web 前端 / Reflexion Agent - Web UI
双语 / Bilingual
运行: Run:  python web_app.py  ->  http://127.0.0.1:5011
"""
import io
import base64
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template_string

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reflexion_agent import reflexion_run, get_api_key

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

app = Flask(__name__)

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        for line in open(env_path, encoding='utf-8'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()

def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=95, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

def curve_img(history):
    rounds = [h['round'] for h in history]
    makespans = [h['makespan'] for h in history]
    balances = [h['balance'] for h in history]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))
    axes[0].plot(rounds, makespans, 'o-', color='#1976D2', lw=2)
    axes[0].set_xlabel('轮次 round'); axes[0].set_ylabel('最大完工时间 makespan')
    axes[0].set_title('完工时间下降 / Makespan'); axes[0].grid(alpha=0.3)
    axes[1].plot(rounds, balances, 'o-', color='#2E7D32', lw=2)
    axes[1].set_xlabel('轮次 round'); axes[1].set_ylabel('负载差异 balance gap')
    axes[1].set_title('负载均衡提升 / Balance'); axes[1].grid(alpha=0.3)
    fig.tight_layout()
    return fig_to_b64(fig)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>反思型 Agent / Reflexion Agent</title>
<style>
 body{font-family:'Microsoft YaHei',sans-serif;max-width:860px;margin:20px auto;padding:0 16px;color:#333}
 h1{color:#1a237e;text-align:center} .en{color:#888;font-size:13px;text-align:center}
 img{width:100%;border-radius:6px;margin-top:8px;border:1px solid #eee}
 .round{background:#fff;border-left:4px solid #1976D2;border-radius:6px;padding:8px 12px;margin:6px 0;font-size:13px}
 .final{background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;padding:12px;margin:12px 0}
</style></head>
<body>
<h1>🔄 反思型 Agent / Reflexion Agent</h1>
<p class="en">《AI在半导体晶圆厂的应用》第23章配套实验 · 尝试→评估→反思→重试 · Mode: <b>{{mode}}</b></p>
<div class="panel" style="background:#f5f7ff;border:1px solid #d5dbf5;border-radius:8px;padding:12px;font-size:13px">
 任务: 把 8 批任务分配给 3 台设备(速度 2.0/1.0/0.5), 使负载均衡 —— Agent 每轮反思并改进方案
</div>
{% if rounds %}
<div class="panel"><b>迭代过程 Iterations:</b>
 {% for h in rounds %}
 <div class="round">轮 {{h.round}}: 方案 {{h.plan}} | 最大完工 {{'%.2f'|format(h.makespan)}} |
  负载差异 {{'%.2f'|format(h.balance)}} {{h.note if h.note else ''}}</div>
 {% endfor %}
</div>
<div class="final"><b>最佳方案 Best:</b> 轮{{best.round}} 方案{{best.plan}}, 最大完工时间 {{'%.2f'|format(best.makespan)}}</div>
<img src="data:image/png;base64,{{curve}}">
{% endif %}
<p class="en" style="text-align:center">运行: python web_app.py (端口5011) · 命令行版: python reflexion_agent.py</p>
</body></html>"""

@app.route('/')
def index():
    history = reflexion_run()
    best = min(history, key=lambda h: h['makespan'])
    mode = 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)'
    return render_template_string(HTML, rounds=history, best=best, curve=curve_img(history), mode=mode)

if __name__ == '__main__':
    print('反思型 Agent Web 界面 / Reflexion Web UI: http://127.0.0.1:5011')
    app.run(debug=True, port=5011)
