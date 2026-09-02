"""
🔬 LLM Agent 工具调用 - Web 前端 / LLM Agent Tool Use - Web UI
双语 / Bilingual
运行: Run:  python web_app.py  ->  http://127.0.0.1:5006
"""
import os
from flask import Flask, request, render_template_string

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_agent_tool_use import TOOLS, agent_run, get_api_key

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
<head><meta charset="utf-8"><title>LLM Agent 工具调用 / Agent Tool Use</title>
<style>
 body{font-family:'Microsoft YaHei',sans-serif;max-width:860px;margin:20px auto;padding:0 16px;color:#333}
 h1{color:#1a237e;text-align:center} .en{color:#888;font-size:13px;text-align:center}
 .panel{background:#f5f7ff;border:1px solid #d5dbf5;border-radius:8px;padding:14px;margin:14px 0}
 input[type=text]{width:70%;padding:8px;border:1px solid #bbb;border-radius:4px;font-size:14px}
 button{background:#1a237e;color:#fff;border:none;padding:8px 20px;border-radius:6px;cursor:pointer;font-size:14px}
 .step{background:#fff;border-left:4px solid #1976D2;border-radius:4px;padding:8px 12px;margin:6px 0;font-size:13px}
 .final{background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;padding:12px;margin:12px 0}
 .tool{display:inline-block;background:#E3F2FD;border:1px solid #90CAF9;border-radius:4px;padding:2px 8px;font-size:12px;margin:2px}
</style></head>
<body>
<h1>🤖 LLM Agent 工具调用 / LLM Agent with Tool Use</h1>
<p class="en">《AI在半导体晶圆厂的应用》第23章配套实验 · ReAct 循环 · Mode: <b>{{mode}}</b></p>
<div class="panel">
 <b>工具集 Tools:</b>
 {% for k, v in tools.items() %}<span class="tool">{{k}}: {{v.desc}}</span>{% endfor %}
</div>
<form method="post">
 <div class="panel">
  <input type="text" name="question" placeholder="提问: EUV-01 的利用率是多少?" value="{{question}}" required>
  <button type="submit">运行 Agent / Run</button>
 </div>
</form>
{% if trace %}
<div class="panel">
 <b>调用轨迹 Tool-call trace:</b>
 {% for t in trace %}
  <div class="step">
   步骤 {{t.step}}:
   {% if 'tool' in t %}<b>调用 {{t.tool}}({{t.arg}})</b> → {{t.result[:80]}}
   {% elif 'final' in t %}<b>最终回答</b>: {{t.final[:80]}}
   {% elif 'error' in t %}<b>错误</b>: {{t.error}}
   {% else %}{{t.raw}}{% endif %}
  </div>
 {% endfor %}
</div>
<div class="final"><b>最终答案 / Final:</b> {{final}}</div>
{% endif %}
<p class="en" style="text-align:center">运行: python web_app.py (端口5006) · 命令行版: python llm_agent_tool_use.py</p>
</body></html>"""

@app.route('/', methods=['GET', 'POST'])
def index():
    question, trace, final = '', None, ''
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if question:
            trace, final = agent_run(question)
    mode = 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)'
    return render_template_string(HTML, tools=TOOLS, mode=mode,
                                  question=question, trace=trace, final=final)

if __name__ == '__main__':
    print('LLM Agent 工具调用 Web 界面 / Agent Tool Use Web UI: http://127.0.0.1:5006')
    app.run(debug=True, port=5006)
