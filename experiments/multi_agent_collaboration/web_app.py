"""
🔬 多 Agent 协作诊断 - Web 前端 / Multi-Agent Collaboration - Web UI
双语 / Bilingual
运行: Run:  python web_app.py  ->  http://127.0.0.1:5009
"""
import os
from flask import Flask, request, render_template_string

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multi_agent_collaboration import AGENTS, run_collaboration, get_api_key

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
<head><meta charset="utf-8"><title>多 Agent 协作诊断 / Multi-Agent Collaboration</title>
<style>
 body{font-family:'Microsoft YaHei',sans-serif;max-width:860px;margin:20px auto;padding:0 16px;color:#333}
 h1{color:#1a237e;text-align:center} .en{color:#888;font-size:13px;text-align:center}
 .panel{background:#f5f7ff;border:1px solid #d5dbf5;border-radius:8px;padding:14px;margin:14px 0}
 input[type=text]{width:70%;padding:8px;border:1px solid #bbb;border-radius:4px;font-size:14px}
 button{background:#1a237e;color:#fff;border:none;padding:8px 20px;border-radius:6px;cursor:pointer;font-size:14px}
 .agent{background:#fff;border-left:4px solid #1976D2;border-radius:6px;padding:10px 12px;margin:8px 0;font-size:14px}
 .agent b{color:#0D47A1}
 .final{background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;padding:14px;margin:12px 0;font-size:14px}
</style></head>
<body>
<h1>🤝 多 Agent 协作诊断 / Multi-Agent Collaboration</h1>
<p class="en">《AI在半导体晶圆厂的应用》第23章配套实验 · 主持人编排四个专业Agent · Mode: <b>{{mode}}</b></p>
<form method="post">
 <div class="panel">
  <input type="text" name="question" placeholder="问题: 光刻层良率下降, 晶圆图显示边缘环形缺陷" value="{{question}}" required>
  <button type="submit">协作诊断 / Collaborate</button>
 </div>
</form>
{% if opinions %}
{% for key, op in opinions.items() %}
<div class="agent"><b>{{AGENTS[key].name}}</b> ({{AGENTS[key].role}}):<br>{{op}}</div>
{% endfor %}
<div class="final"><b>主持人决策 / Coordinator decision:</b><br>{{summary}}</div>
{% endif %}
<p class="en" style="text-align:center">运行: python web_app.py (端口5009) · 命令行版: python multi_agent_collaboration.py</p>
</body></html>"""

@app.route('/', methods=['GET', 'POST'])
def index():
    question, opinions, summary = '', None, ''
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if question:
            opinions, summary = run_collaboration(question)
    mode = 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)'
    return render_template_string(HTML, AGENTS=AGENTS, mode=mode, question=question,
                                  opinions=opinions, summary=summary)

if __name__ == '__main__':
    print('多 Agent 协作 Web 界面 / Multi-Agent Web UI: http://127.0.0.1:5009')
    app.run(debug=True, port=5009)
