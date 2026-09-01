"""
🔬 预测性维护 RUL - Web 前端 / Predictive Maintenance RUL - Web UI
双语 / Bilingual
运行: Run:  python web_app.py  ->  http://127.0.0.1:5001
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

def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=95, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

def build_figures(exp=1.9, train_ratio=0.8, seed=7):
    np.random.seed(seed)
    N = 300
    t = np.arange(N)
    baseline = 10.0
    drift = 0.0016 * t ** exp
    noise = np.random.normal(0, 0.35, N)
    health = baseline + drift + noise
    threshold = 26.0
    fail_idx = np.argmax(health >= threshold)
    train_n = min(200, int(fail_idx * train_ratio))

    y = health[:train_n] - baseline
    x = t[:train_n].astype(float)
    mask = x >= 1
    logy = np.log(np.clip(y[mask], 1e-3, None))
    b_fit, loga = np.polyfit(np.log(x[mask]), logy, 1)
    a_fit = np.exp(loga)
    pred_health = baseline + a_fit * t ** b_fit
    pred_fail = np.argmax(pred_health >= threshold)
    pred_rul = pred_fail - train_n
    actual_rul = fail_idx - train_n

    imgs = {}
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(t, health, 'b-', lw=1.2, alpha=0.8, label='实际健康特征 actual')
    ax.plot(t, pred_health, 'r--', lw=2, label='拟合外推 fitted')
    ax.axhline(threshold, color='k', ls=':', lw=1.5)
    ax.text(2, threshold+0.6, '失效阈值 {:.0f}'.format(threshold))
    ax.axvline(train_n, color='gray', ls='--')
    ax.text(train_n+1, 14, '预测点 day {}'.format(train_n))
    ax.axvspan(fail_idx, N, color='red', alpha=0.1)
    ax.set_xlabel('运行天数 operating days'); ax.set_ylabel('健康特征 health')
    ax.set_title('退化与 RUL 预测 (预测RUL≈{}天, 实际{}天)'.format(max(pred_rul,0), actual_rul))
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); imgs['deg'] = fig_to_b64(fig)

    # 成本对比 / cost comparison
    planned, failure = 5, 50
    pm_interval = 30
    a_cost = (N // pm_interval) * planned
    b_pm = pred_fail - 5
    b_cost = planned + (failure if b_pm >= fail_idx else 0)
    c_cost = (N // 150) * failure
    fig, ax = plt.subplots(figsize=(6, 4))
    names = ['定期PM\nperiodic', '预测性维护\npredictive', '不维护\nnone']
    costs = [a_cost, b_cost, c_cost]
    bars = ax.bar(names, costs, color=['#2196F3', '#4CAF50', '#F44336'], alpha=0.9)
    for bar, c in zip(bars, costs):
        ax.text(bar.get_x()+bar.get_width()/2, c+0.6, '{}万'.format(c), ha='center', fontweight='bold')
    ax.set_ylabel('维护成本 (万元) cost'); ax.set_title('维护策略成本对比 / Strategy Cost')
    ax.grid(alpha=0.3, axis='y')
    fig.tight_layout(); imgs['cost'] = fig_to_b64(fig)
    return imgs, dict(exp=exp, train_ratio=train_ratio, pred_rul=max(pred_rul,0), actual_rul=actual_rul,
                      fail_day=int(fail_idx), best='预测性维护' if b_cost <= a_cost else '定期PM')

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>预测性维护 RUL / Predictive Maintenance</title>
<style>
 body{font-family:'Microsoft YaHei',sans-serif;max-width:900px;margin:20px auto;padding:0 16px;color:#333}
 h1{color:#1a237e;text-align:center} .en{color:#888;font-size:13px;text-align:center}
 .panel{background:#f5f7ff;border:1px solid #d5dbf5;border-radius:8px;padding:14px;margin:16px 0}
 label{margin-right:8px} input{width:90px;padding:4px;margin-right:14px;border:1px solid #bbb;border-radius:4px}
 button{background:#1a237e;color:#fff;border:none;padding:8px 22px;border-radius:6px;cursor:pointer;font-size:14px}
 img{width:100%;border-radius:6px;margin-top:8px;border:1px solid #eee}
 .row{display:flex;gap:14px;flex-wrap:wrap} .col{flex:1;min-width:320px}
 .result{background:#e8f5e9;border:1px solid #a5d6a7;border-radius:6px;padding:10px;margin:10px 0}
</style></head>
<body>
<h1>🔧 预测性维护 RUL 实验 / Predictive Maintenance RUL</h1>
<p class="en">《AI在半导体晶圆厂的应用》第12章配套实验 · Chapter 12 companion experiment</p>
<form method="get">
 <div class="panel">
  <label>退化指数 exponent:</label><input name="exp" value="{{exp}}" step="0.1">
  <label>训练比例 train ratio:</label><input name="ratio" value="{{train_ratio}}" step="0.05">
  <button type="submit">运行 / Run</button>
 </div>
</form>
<div class="result">
 <b>RUL 预测:</b> 第 {{train_ratio*100|int}}% 生命周期处预测剩余寿命 ≈ <b>{{pred_rul}}</b> 天 (实际 {{actual_rul}} 天, 失效日 day {{fail_day}})<br>
 <b>最优维护策略 / best strategy:</b> <b>{{best}}</b>
</div>
<div class="row">
 <div class="col"><img src="data:image/png;base64,{{deg}}"><p class="en">① 退化曲线与 RUL 预测 Degradation &amp; RUL</p></div>
 <div class="col"><img src="data:image/png;base64,{{cost}}"><p class="en">② 维护策略成本对比 Strategy cost</p></div>
</div>
<p class="en" style="text-align:center">运行: python web_app.py (端口5001) · 命令行版: python predictive_maintenance_rul.py</p>
</body></html>"""

@app.route('/')
def index():
    try:
        exp = min(max(float(request.args.get('exp', 1.9)), 1.2), 3.0)
        ratio = min(max(float(request.args.get('ratio', 0.8)), 0.5), 0.95)
    except ValueError:
        exp, ratio = 1.9, 0.8
    imgs, meta = build_figures(exp, ratio)
    return render_template_string(HTML, **imgs, **meta)

if __name__ == '__main__':
    print('预测性维护 RUL Web 界面 / RUL Web UI: http://127.0.0.1:5001')
    app.run(debug=True, port=5001)
