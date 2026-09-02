"""
🔬 Agent 任务分解与执行 - Web 前端 / Task Decomposition - Web UI
双语 / Bilingual
运行: Run:  python web_app.py  ->  http://127.0.0.1:5010
"""
import os
from flask import Flask, request, render_template_string

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent_task_decomposition import execute, get_api_key

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

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>Agent 任务分解与执行 / Task Decomposition</title>
<style>
 body{font-family:'Microsoft YaHei',sans-serif;max-width:860px;margin:20px auto;padding:0 16px;color:#333}
 h1{color:#1a237e;text-align:center} .en{color:#888;font-size:13px;text-align:center}
 .panel{background:#f5f7ff;border:1px solid #d5dbf5;border-radius:8px;padding:14px;margin:14px 0}
 input[type=text]{width:70%;padding:8px;border:1px solid #bbb;border-radius:4px;font-size:14px}
 button{background:#1a237e;color:#fff;border:none;padding:8px 20px;border-radius:6px;cursor:pointer;font-size:14px}
 .task{background:#fff;border-left:4px solid #1976D2;border-radius:6px;padding:8px 12px;margin:6px 0;font-size:13px}
 .report{background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;padding:14px;margin:12px 0;font-size:14px;white-space:pre-wrap}
</style></head>
<body>
<h1>🗂️ Agent 任务分解与执行 / Task Decomposition & Execution</h1>
<p class="en">《AI在半导体晶圆厂的应用》第17章(SA融合)配套实验 · 规划→执行→汇总 · Mode: <b>{{mode}}</b></p>
<form method="post">
 <div class="panel">
  <input type="text" name="goal" placeholder="目标: 提升光刻层良率, 找出根因并给出优化方案" value="{{goal}}" required>
  <button type="submit">分解并执行 / Decompose & Run</button>
 </div>
</form>
{% if results %}
<div class="panel"><b>任务分解与执行 Subtasks:</b>
 {% for r in results %}
 <div class="task"><b>{{r.task}}</b> → 工具 {{r.tool}}<br><span style="color:#555">{{r.result[:110]}}</span></div>
 {% endfor %}
</div>
<div class="report"><b>完成报告 Report:</b><br>{{report}}</div>
{% endif %}
<p class="en" style="text-align:center">运行: python web_app.py (端口5010) · 命令行版: python agent_task_decomposition.py</p>
</body></html>"""

@app.route('/', methods=['GET', 'POST'])
def index():
    goal, results, report = '', None, ''
    if request.method == 'POST':
        goal = request.form.get('goal', '').strip()
        if goal:
            plan, results, report = execute(goal)
    mode = 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)'
    return render_template_string(HTML, goal=goal, results=results, report=report, mode=mode)

if __name__ == '__main__':
    print('Agent 任务分解 Web 界面 / Task Decomposition Web UI: http://127.0.0.1:5010')
    app.run(debug=True, port=5010)
