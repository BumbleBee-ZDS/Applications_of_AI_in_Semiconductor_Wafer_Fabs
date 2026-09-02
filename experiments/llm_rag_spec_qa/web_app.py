"""
🔬 LLM RAG 工艺文档问答 - Web 前端 / LLM RAG Process-Spec QA - Web UI
双语 / Bilingual
运行: Run:  python web_app.py  ->  http://127.0.0.1:5002
说明: 读取 .env 中的 DEEPSEEK_API_KEY; 无 Key 时自动使用 Mock LLM
Note: reads DEEPSEEK_API_KEY from .env; falls back to Mock LLM without a key.
"""
import os
import base64
from flask import Flask, request, render_template_string

# 复用主程序(import 无副作用, 主入口有 __main__ 保护)
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_rag_spec_qa import DOCS, retrieve, ask, get_api_key

app = Flask(__name__)

def load_env():
    """读取同目录 .env(如有) / load .env if present"""
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
<head><meta charset="utf-8"><title>LLM RAG 工艺文档问答 / SPEC QA</title>
<style>
 body{font-family:'Microsoft YaHei',sans-serif;max-width:860px;margin:20px auto;padding:0 16px;color:#333}
 h1{color:#1a237e;text-align:center} .en{color:#888;font-size:13px;text-align:center}
 .panel{background:#f5f7ff;border:1px solid #d5dbf5;border-radius:8px;padding:14px;margin:14px 0}
 input[type=text]{width:70%;padding:8px;border:1px solid #bbb;border-radius:4px;font-size:14px}
 button{background:#1a237e;color:#fff;border:none;padding:8px 20px;border-radius:6px;cursor:pointer;font-size:14px}
 .qa{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:12px;margin:10px 0}
 .q{font-weight:bold} .a{color:#1a237e;margin-top:6px}
 .hits{color:#888;font-size:12px;margin-top:4px}
 .docs{background:#fafafa;border:1px solid #eee;border-radius:6px;padding:10px;font-size:13px}
 .badge{display:inline-block;background:#1a237e;color:#fff;border-radius:4px;padding:2px 8px;font-size:12px}
</style></head>
<body>
<h1>🤖 LLM RAG 工艺文档问答 / Process-Spec QA</h1>
<p class="en">《AI在半导体晶圆厂的应用》第22章配套实验 · Mode: <b>{{mode}}</b></p>
<form method="post">
 <div class="panel">
  <input type="text" name="question" placeholder="提问: 刻蚀机的腔体压力规格是多少?" value="{{question}}" required>
  <button type="submit">提问 / Ask</button>
 </div>
</form>

{% if answer %}
<div class="qa">
 <div class="q">问 / Q: {{question}}</div>
 <div class="a">答 / A: {{answer}}</div>
 <div class="hits">检索命中 / retrieval hits: {{hits}}</div>
</div>
{% endif %}

<div class="panel">
 <b>文档库 / Doc Library:</b>
 <div class="docs">
 {% for d in docs %}<div><span class="badge">{{d.id}}</span> {{d.title}}</div>{% endfor %}
 </div>
</div>
<p class="en" style="text-align:center">RAG = 检索 Retrieval + 增强 Augmentation + 生成 Generation · 运行: python web_app.py (端口5002)</p>
</body></html>"""

@app.route('/', methods=['GET', 'POST'])
def index():
    question = ''
    answer = ''
    hits = ''
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if question:
            found = retrieve(question)
            hits = ', '.join(d['id'] for d in found) or '(无命中 no hit)'
            answer = ask(question)
    mode = 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)'
    return render_template_string(HTML, question=question, answer=answer, hits=hits,
                                  docs=DOCS, mode=mode)

if __name__ == '__main__':
    print('LLM RAG 问答 Web 界面 / RAG QA Web UI: http://127.0.0.1:5002')
    app.run(debug=True, port=5002)
