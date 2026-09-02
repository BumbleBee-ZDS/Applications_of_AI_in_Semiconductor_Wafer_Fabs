"""
🔬 良率模型与爬坡模拟 - Web 前端 / Yield Modeling & Ramp Simulation - Web UI
双语 / Bilingual
运行: Run:  python web_app.py  ->  http://127.0.0.1:5000
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

app = Flask(__name__)

# ---------- 计算函数 / computation functions ----------
def poisson_yield(D0, A):
    return np.exp(-D0 * A)

def negative_binomial_yield(D0, A, alpha):
    return (1 + D0 * A / alpha) ** (-alpha)

def murphy_yield(D0, A):
    x = D0 * A
    return (1 - np.exp(-x)) / x

def ramp_curve(t, y_start, y_max, k, t0):
    return y_start + (y_max - y_start) / (1 + np.exp(-k * (t - t0)))

def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=95, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

# ---------- 生成 3 张图 / build the three figures ----------
def build_figures(D0_max=2.0, A=1.0, k=0.38, target=85.0):
    imgs = {}
    # 图1: 良率模型对比 / yield models
    D0 = np.linspace(0.05, D0_max, 100)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(D0, poisson_yield(D0, A), 'k-', lw=2, label='Poisson (随机 random)')
    ax.plot(D0, negative_binomial_yield(D0, A, 2), 'r--', lw=2, label='负二项式 NB α=2 (聚集)')
    ax.plot(D0, negative_binomial_yield(D0, A, 20), 'g--', lw=2, label='负二项式 NB α=20')
    ax.plot(D0, murphy_yield(D0, A), 'b:', lw=2, label='Murphy (波动修正)')
    ax.set_xlabel('缺陷密度 D0 / defect density')
    ax.set_ylabel('良率 Yield')
    ax.set_title('良率模型对比 Yield Models (A={:.1f})'.format(A))
    ax.legend(fontsize=7); ax.grid(alpha=0.3)
    fig.tight_layout(); imgs['models'] = fig_to_b64(fig)

    # 图2: S形爬坡曲线 / ramp curves
    months = np.linspace(0, 24, 300)
    y_fast = ramp_curve(months, 30, 93, k, 8.5)
    y_slow = ramp_curve(months, 30, 82, k * 0.55, 9.0)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(months, y_fast, 'b-', lw=2.2, label='快学习率 k={:.2f}'.format(k))
    ax.plot(months, y_slow, 'r--', lw=2.2, label='慢学习率 k={:.2f}'.format(k*0.55))
    ax.axhline(target, color='g', ls=':', lw=1.5)
    ax.text(0.3, target+1.5, '量产目标 {:.0f}%'.format(target), color='g')
    ax.axvspan(0, 9, color='orange', alpha=0.12)
    ax.text(1.5, 34, '"死亡之谷"', color='#E65100', fontweight='bold')
    ax.set_xlabel('投产月份 months'); ax.set_ylabel('良率 Yield (%)')
    ax.set_title('良率爬坡 S 曲线 / Yield Ramp S-Curve')
    ax.legend(loc='lower right', fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); imgs['ramp'] = fig_to_b64(fig)

    # 图3: 虚拟量测 / virtual metrology
    np.random.seed(42)
    n = 200
    temp = np.random.uniform(380, 420, n)
    rf = np.random.uniform(800, 1200, n)
    thick_true = 180 + 0.25*(temp-400) - 0.08*(rf-1000) + np.random.normal(0, 1.5, n)
    Xb = np.column_stack([np.ones(n), temp, rf])
    beta, *_ = np.linalg.lstsq(Xb, thick_true, rcond=None)
    thick_pred = Xb @ beta
    err = np.abs(thick_pred - thick_true)
    skip = (err < 3.0).mean()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(thick_true, thick_pred, s=10, alpha=0.6)
    lim = [thick_true.min(), thick_true.max()]
    ax.plot(lim, lim, 'r--', lw=1.5)
    ax.set_xlabel('实际 actual (nm)'); ax.set_ylabel('预测 predicted (nm)')
    ax.set_title('虚拟量测 VM (免检率 skip rate={:.0%})'.format(skip))
    ax.grid(alpha=0.3)
    fig.tight_layout(); imgs['vm'] = fig_to_b64(fig)
    return imgs

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>良率模型与爬坡模拟 / Yield Modeling</title>
<style>
 body{font-family:'Microsoft YaHei',sans-serif;max-width:960px;margin:20px auto;padding:0 16px;color:#333}
 h1{color:#1a237e;text-align:center} .en{color:#888;font-size:13px;text-align:center}
 .panel{background:#f5f7ff;border:1px solid #d5dbf5;border-radius:8px;padding:14px;margin:16px 0}
 label{margin-right:8px} input{width:90px;padding:4px;margin-right:14px;border:1px solid #bbb;border-radius:4px}
 button{background:#1a237e;color:#fff;border:none;padding:8px 22px;border-radius:6px;cursor:pointer;font-size:14px}
 img{width:100%;border-radius:6px;margin-top:8px;border:1px solid #eee}
 .row{display:flex;gap:14px;flex-wrap:wrap} .col{flex:1;min-width:300px}
</style></head>
<body>
<h1>🔬 良率模型与爬坡模拟 / Yield Modeling &amp; Ramp</h1>
<p class="en">Interactive: adjust parameters and re-run · 《AI在半导体晶圆厂的应用》第9/11章配套实验</p>
<form method="get">
 <div class="panel">
  <label>缺陷密度上限 D0<sub>max</sub>:</label><input name="d0" value="{{d0}}">
  <label>芯片面积 A:</label><input name="a" value="{{a}}">
  <label>学习率 k:</label><input name="k" value="{{k}}" step="0.01">
  <label>量产目标 %:</label><input name="target" value="{{target}}">
  <button type="submit">运行 / Run</button>
 </div>
</form>
<div class="row">
 <div class="col"><img src="data:image/png;base64,{{models}}"><p class="en">① 良率模型对比 Yield models</p></div>
 <div class="col"><img src="data:image/png;base64,{{ramp}}"><p class="en">② S形爬坡曲线 Ramp curve</p></div>
 <div class="col"><img src="data:image/png;base64,{{vm}}"><p class="en">③ 虚拟量测 Virtual metrology</p></div>
</div>
<p class="en" style="text-align:center">运行: python web_app.py · 命令行版: python yield_modeling_ramp.py</p>
</body></html>"""

@app.route('/')
def index():
    try:
        d0 = float(request.args.get('d0', 2.0))
        a = float(request.args.get('a', 1.0))
        k = float(request.args.get('k', 0.38))
        target = float(request.args.get('target', 85.0))
        d0 = min(max(d0, 0.2), 10.0)      # 参数钳制 / clamp params
        a = min(max(a, 0.1), 10.0)
        k = min(max(k, 0.05), 1.0)
        target = min(max(target, 50.0), 99.0)
    except ValueError:
        d0, a, k, target = 2.0, 1.0, 0.38, 85.0
    imgs = build_figures(d0, a, k, target)
    return render_template_string(HTML, d0=d0, a=a, k=k, target=target, **imgs)

if __name__ == '__main__':
    print('良率模型实验 Web 界面 / Yield Modeling Web UI: http://127.0.0.1:5000')
    app.run(debug=True, port=5000)
