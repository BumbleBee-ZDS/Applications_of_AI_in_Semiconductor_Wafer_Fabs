"""
🔬 LLM 良率周报自动生成 - Web 前端 / Yield Report Automation - Web UI
双语 / Bilingual
运行: Run:  python web_app.py  ->  http://127.0.0.1:5008
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
from llm_report_automation import DATA, generate_report, get_api_key

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

def charts():
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    ax = axes[0]
    ax.plot(DATA['weeks'], DATA['yield_trend'], 'o-', color='#1976D2', lw=2.2)
    ax.set_xlabel('周 week'); ax.set_ylabel('综合良率 %')
    ax.set_title('良率周趋势 / Weekly Yield Trend'); ax.grid(alpha=0.3)
    ax = axes[1]
    tops = DATA['defect_top3']
    ax.barh([t['type'] for t in tops][::-1], [t['loss'] for t in tops][::-1],
            color=['#F44336', '#FF9800', '#FFC107'])
    ax.set_xlabel('良率损失 % / yield loss')
    ax.set_title('缺陷 TOP3 / Defect TOP3'); ax.grid(alpha=0.3, axis='x')
    fig.tight_layout()
    return fig_to_b64(fig)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>LLM 良率周报自动生成 / Yield Report</title>
<style>
 body{font-family:'Microsoft YaHei',sans-serif;max-width:860px;margin:20px auto;padding:0 16px;color:#333}
 h1{color:#1a237e;text-align:center} .en{color:#888;font-size:13px;text-align:center}
 img{width:100%;border-radius:6px;margin-top:8px;border:1px solid #eee}
 .report{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin:14px 0;line-height:1.7;white-space:pre-wrap}
 .badge{display:inline-block;background:#1a237e;color:#fff;border-radius:4px;padding:2px 10px;font-size:12px}
</style></head>
<body>
<h1>📊 LLM 良率周报自动生成 / LLM Yield Report Automation</h1>
<p class="en">《AI在半导体晶圆厂的应用》第22章配套实验 · 数据→文本 · Mode: <b>{{mode}}</b></p>
<img src="data:image/png;base64,{{charts}}">
<div class="report"><b>📄 {{DATA.week}}周良率周报(自动生成):</b>
{{report}}</div>
<p class="en" style="text-align:center">运行: python web_app.py (端口5008) · 命令行版: python llm_report_automation.py</p>
</body></html>"""

@app.route('/')
def index():
    report = generate_report()
    mode = 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)'
    return render_template_string(HTML, report=report, charts=charts(), DATA=DATA, mode=mode)

if __name__ == '__main__':
    print('LLM 良率周报 Web 界面 / Yield Report Web UI: http://127.0.0.1:5008')
    app.run(debug=True, port=5008)
