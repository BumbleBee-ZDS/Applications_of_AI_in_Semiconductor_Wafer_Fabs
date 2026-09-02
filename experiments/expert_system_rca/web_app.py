"""
🔬 专家系统缺陷诊断 - Web 前端 / Expert-System RCA - Web UI
双语 / Bilingual
运行: Run:  python web_app.py  ->  http://127.0.0.1:5005
"""
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, request, render_template_string

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expert_system_rca import RULES, forward_chain, diagnose

app = Flask(__name__)

ALL_FACTS = ['边缘环形缺陷', '中心圆形缺陷', '簇状缺陷', '划痕缺陷',
             '随机颗粒缺陷', '图案变形', '缺陷类型=颗粒', '缺陷密度高',
             '簇中心对应腔体', '曝光剂量偏低', '缺陷类型=桥接']

def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=95, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

def chain_img(facts, fired):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis('off')
    nf = len(facts)
    fx = [1.0 + i * (8.0 / max(nf, 1)) for i in range(nf)]
    for x, f in zip(fx, facts):
        ax.add_patch(plt.Rectangle((x-0.95, 3.1), 1.9, 0.7, facecolor='#E3F2FD', edgecolor='#1976D2', lw=1.5))
        ax.text(x, 3.45, f[:8], ha='center', fontsize=9)
    ax.text(5, 3.9, '观察事实 Facts', ha='center', fontsize=10, color='#0D47A1', fontweight='bold')
    nr = len(fired)
    rx = [1.0 + i * (8.0 / max(nr, 1)) for i in range(nr)]
    for x, r in zip(rx, fired):
        ax.add_patch(plt.Rectangle((x-0.95, 1.6), 1.9, 0.8, facecolor='#FFF9C4', edgecolor='#F9A825', lw=1.5))
        ax.text(x, 2.15, r.id, ha='center', fontsize=10, fontweight='bold', color='#795548')
        ax.text(x, 1.85, f'置信度 {r.confidence:.2f}', ha='center', fontsize=8)
        for fxp in fx:
            ax.annotate('', xy=(x, 2.45), xytext=(fxp, 3.1),
                        arrowprops=dict(arrowstyle='->', color='#B0BEC5', lw=0.8))
    ax.text(5, 2.6, '规则匹配 Rules (前向推理)', ha='center', fontsize=10, color='#E65100', fontweight='bold')
    if fired:
        top = fired[0]
        ax.add_patch(plt.Rectangle((2.6, 0.2), 4.8, 0.9, facecolor='#E8F5E9', edgecolor='#2E7D32', lw=2))
        ax.text(5, 0.75, f'诊断: {top.conclusion}', ha='center', fontsize=11, fontweight='bold', color='#1B5E20')
        ax.text(5, 0.4, f'置信度 {top.confidence:.2f} | 建议: {top.advice}', ha='center', fontsize=8, color='#2E7D32')
        for x in rx:
            ax.annotate('', xy=(5, 1.15), xytext=(x, 1.6), arrowprops=dict(arrowstyle='->', color='#4CAF50', lw=1.2))
    fig.tight_layout()
    return fig_to_b64(fig)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>专家系统缺陷诊断 / Expert-System RCA</title>
<style>
 body{font-family:'Microsoft YaHei',sans-serif;max-width:900px;margin:20px auto;padding:0 16px;color:#333}
 h1{color:#1a237e;text-align:center} .en{color:#888;font-size:13px;text-align:center}
 .panel{background:#f5f7ff;border:1px solid #d5dbf5;border-radius:8px;padding:14px;margin:14px 0}
 label{display:inline-block;width:48%;margin:3px 0;font-size:13px}
 button{background:#1a237e;color:#fff;border:none;padding:8px 20px;border-radius:6px;cursor:pointer;font-size:14px;margin-top:8px}
 img{width:100%;border-radius:6px;margin-top:8px;border:1px solid #eee}
 .result{background:#e8f5e9;border:1px solid #a5d6a7;border-radius:6px;padding:12px;margin:12px 0;font-size:14px}
 .rules{background:#fafafa;border:1px solid #eee;border-radius:6px;padding:10px;font-size:12px}
</style></head>
<body>
<h1>🧩 专家系统缺陷诊断 / Expert-System RCA</h1>
<p class="en">《AI在半导体晶圆厂的应用》第14章配套实验 · 前向推理 IF-THEN 规则引擎</p>
<form method="post">
 <div class="panel">
  <b>选择观察事实 / observed facts:</b><br>
  {% for f in facts %}
  <label><input type="checkbox" name="fact" value="{{f}}" {% if f in checked %}checked{% endif %}> {{f}}</label>
  {% endfor %}
  <br><button type="submit">推理诊断 / Diagnose</button>
 </div>
</form>
{% if diag %}
<div class="result">
 <b>诊断 / diagnosis:</b> {{diag}} &nbsp;|&nbsp; <b>置信度 / confidence:</b> {{conf}}<br>
 <b>建议 / advice:</b> {{advice}}
</div>
{% endif %}
{% if img %}<img src="data:image/png;base64,{{img}}"><p class="en">推理链 Inference chain</p>{% endif %}
<div class="panel rules"><b>规则库 / Rule base:</b><br>
{% for r in rules %}[{{r.id}}] IF {{r.premises|join(' AND ')}} THEN {{r.conclusion}} ({{r.confidence}})<br>{% endfor %}
</div>
<p class="en" style="text-align:center">运行: python web_app.py (端口5005) · 命令行版: python expert_system_rca.py</p>
</body></html>"""

@app.route('/', methods=['GET', 'POST'])
def index():
    checked = []
    diag = conf = advice = img = None
    if request.method == 'POST':
        checked = request.form.getlist('fact')
        top, err = diagnose(checked)
        if top:
            diag = top.conclusion
            conf = f'{top.confidence:.2f}'
            advice = top.advice
            fired = forward_chain(checked)
            img = chain_img(checked, fired)
        else:
            diag = err
            conf = '—'
            advice = '—'
    return render_template_string(HTML, facts=ALL_FACTS, rules=RULES, checked=checked,
                                  diag=diag, conf=conf, advice=advice, img=img)

if __name__ == '__main__':
    print('专家系统缺陷诊断 Web 界面 / Expert-System RCA Web UI: http://127.0.0.1:5005')
    app.run(debug=True, port=5005)
