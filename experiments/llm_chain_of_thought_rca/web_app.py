"""
🔬 思维链良率根因分析 - Web 前端 / CoT RCA - Web UI
双语 / Bilingual
运行: Run:  python web_app.py  ->  http://127.0.0.1:5007
"""
import os
from flask import Flask, request, render_template_string

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_chain_of_thought_rca import run_cot, rule_check, get_api_key

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
<head><meta charset="utf-8"><title>思维链良率根因分析 / CoT RCA</title>
<style>
 body{font-family:'Microsoft YaHei',sans-serif;max-width:860px;margin:20px auto;padding:0 16px;color:#333}
 h1{color:#1a237e;text-align:center} .en{color:#888;font-size:13px;text-align:center}
 .panel{background:#f5f7ff;border:1px solid #d5dbf5;border-radius:8px;padding:14px;margin:14px 0}
 input[type=text]{width:70%;padding:8px;border:1px solid #bbb;border-radius:4px;font-size:14px}
 button{background:#1a237e;color:#fff;border:none;padding:8px 20px;border-radius:6px;cursor:pointer;font-size:14px}
 .step{background:#fff;border-left:4px solid #7B1FA2;border-radius:4px;padding:10px 12px;margin:6px 0;font-size:14px;white-space:pre-wrap}
 .check{background:#fff3e0;border:1px solid #ffcc80;border-radius:6px;padding:10px;margin:10px 0;font-size:13px}
 .examples{font-size:12px;color:#555}
</style></head>
<body>
<h1>🧠 思维链良率根因分析 / Chain-of-Thought RCA</h1>
<p class="en">《AI在半导体晶圆厂的应用》第18章配套实验 · 观察→假设→验证→结论 · Mode: <b>{{mode}}</b></p>
<div class="panel examples">
 示例: 晶圆图显示边缘环形缺陷, 缺陷类型为颗粒, 曝光剂量偏低 · 晶圆图显示簇状缺陷, 簇中心对应某腔体位置
</div>
<form method="post">
 <div class="panel">
  <input type="text" name="facts" placeholder="输入缺陷观察事实 facts" value="{{facts}}" required>
  <button type="submit">推理根因 / Reason</button>
 </div>
</form>
{% if steps %}
<div class="panel"><b>CoT 推理步骤 / reasoning steps:</b>
 {% for s in steps %}<div class="step">{{s}}</div>{% endfor %}
</div>
<div class="check"><b>符号规则校验 / symbolic check:</b> {{check}}</div>
{% endif %}
<p class="en" style="text-align:center">运行: python web_app.py (端口5007) · 命令行版: python llm_chain_of_thought_rca.py</p>
</body></html>"""

@app.route('/', methods=['GET', 'POST'])
def index():
    facts, steps, check = '', None, ''
    if request.method == 'POST':
        facts = request.form.get('facts', '').strip()
        if facts:
            raw, conclusion = run_cot(facts)
            steps = [ln for ln in raw.split('\n') if ln.strip()][:4]
            check = rule_check(facts, conclusion)
    mode = 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)'
    return render_template_string(HTML, facts=facts, steps=steps, check=check, mode=mode)

if __name__ == '__main__':
    print('CoT 根因分析 Web 界面 / CoT RCA Web UI: http://127.0.0.1:5007')
    app.run(debug=True, port=5007)
