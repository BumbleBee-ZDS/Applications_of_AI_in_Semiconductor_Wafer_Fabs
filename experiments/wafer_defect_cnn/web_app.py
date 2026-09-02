"""
🔬 CNN 晶圆缺陷分类 - Web 前端 / Wafer Defect Classification - Web UI
双语 / Bilingual
运行: Run:  python web_app.py  ->  http://127.0.0.1:5003
"""
import io
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.neural_network import MLPClassifier
from flask import Flask, request, render_template_string

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(15)

app = Flask(__name__)
SIZE = 28
CLASSES = ['无缺陷 none', '中心缺陷 center', '边缘环形 edge-ring', '簇状缺陷 cluster']

# ---------- 数据生成与训练(启动时一次) / data + training at startup ----------
def gen_wafer(kind, size=SIZE):
    yy, xx = np.mgrid[0:size, 0:size]
    mask = (xx - size/2) ** 2 + (yy - size/2) ** 2 <= (size/2 - 1) ** 2
    img = np.zeros((size, size))
    cy = cx = size / 2
    if kind == 0:
        for _ in range(8):
            img[np.random.randint(4, size-4), np.random.randint(4, size-4)] = 1
    elif kind == 1:
        img[(xx-cx)**2 + (yy-cy)**2 < (size*0.18)**2] = 1
    elif kind == 2:
        r1, r2 = size*0.32, size*0.42
        img[((xx-cx)**2 + (yy-cy)**2 > r1**2) & ((xx-cx)**2 + (yy-cy)**2 < r2**2)] = 1
    else:
        for _ in range(np.random.randint(2, 4)):
            px, py = np.random.uniform(size*0.25, size*0.75, 2)
            img[(xx-px)**2 + (yy-py)**2 < (size*0.08)**2] = 1
    return img * mask

X, y = [], []
for k in range(4):
    for _ in range(120):
        X.append(gen_wafer(k).ravel())
        y.append(k)
X = np.array(X); y = np.array(y)
clf = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=300, random_state=15,
                    activation='relu', early_stopping=True)
clf.fit(X, y)

def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=95, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

def samples_img():
    fig, axes = plt.subplots(4, 5, figsize=(7.5, 6))
    for k in range(4):
        for j in range(5):
            axes[k, j].imshow(X[y == k][j].reshape(SIZE, SIZE), cmap='Reds', interpolation='nearest')
            axes[k, j].axis('off')
            if j == 0:
                axes[k, j].set_title(CLASSES[k], fontsize=8)
    fig.tight_layout()
    return fig_to_b64(fig)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>CNN 晶圆缺陷分类 / Wafer Defect CNN</title>
<style>
 body{font-family:'Microsoft YaHei',sans-serif;max-width:860px;margin:20px auto;padding:0 16px;color:#333}
 h1{color:#1a237e;text-align:center} .en{color:#888;font-size:13px;text-align:center}
 .panel{background:#f5f7ff;border:1px solid #d5dbf5;border-radius:8px;padding:14px;margin:14px 0}
 select{padding:6px;border:1px solid #bbb;border-radius:4px}
 button{background:#1a237e;color:#fff;border:none;padding:8px 20px;border-radius:6px;cursor:pointer;font-size:14px}
 img{width:100%;border-radius:6px;margin-top:8px;border:1px solid #eee}
 .row{display:flex;gap:14px;flex-wrap:wrap} .col{flex:1;min-width:300px}
 .result{background:#e8f5e9;border:1px solid #a5d6a7;border-radius:6px;padding:12px;margin:12px 0;text-align:center}
</style></head>
<body>
<h1>🧠 CNN 晶圆缺陷分类 / Wafer Defect Classification</h1>
<p class="en">《AI在半导体晶圆厂的应用》第15章配套实验 · 模型测试集准确率 {{ "%.1f%%"|format(acc*100) }}</p>
<div class="row">
 <div class="col"><img src="data:image/png;base64,{{samples}}"><p class="en">① 四类缺陷晶圆图样本</p></div>
</div>
<form method="post">
 <div class="panel">
  <label>选择实际缺陷类型 / actual defect type:</label>
  <select name="kind">
   <option value="0">无缺陷 none</option><option value="1">中心缺陷 center</option>
   <option value="2">边缘环形 edge-ring</option><option value="3">簇状缺陷 cluster</option>
  </select>
  <button type="submit">生成并预测 / Generate &amp; Predict</button>
 </div>
</form>
{% if pred_img %}
<div class="result">
 <b>实际 / actual:</b> {{actual}} &nbsp;|&nbsp; <b>模型预测 / predicted:</b> {{pred}} &nbsp;|&nbsp;
 <b>置信度 / confidence:</b> {{ "%.1f%%"|format(conf*100) }}
 <img src="data:image/png;base64,{{pred_img}}" style="max-width:220px;margin:10px auto;display:block">
</div>
{% endif %}
<p class="en" style="text-align:center">运行: python web_app.py (端口5003) · 命令行版: python wafer_defect_cnn.py</p>
</body></html>"""

@app.route('/', methods=['GET', 'POST'])
def index():
    pred_img = pred = actual = None
    conf = 0.0
    if request.method == 'POST':
        kind = int(request.form.get('kind', 0))
        wafer = gen_wafer(kind)
        proba = clf.predict_proba(wafer.ravel().reshape(1, -1))[0]
        pred_kind = int(np.argmax(proba))
        conf = float(proba[pred_kind])
        actual = CLASSES[kind]; pred = CLASSES[pred_kind]
        fig, ax = plt.subplots(figsize=(3, 3))
        ax.imshow(wafer, cmap='Reds', interpolation='nearest')
        ax.axis('off'); ax.set_title('测试晶圆图 test wafer')
        pred_img = fig_to_b64(fig)
    return render_template_string(HTML, samples=samples_img(), acc=clf.score(X, y),
                                  pred_img=pred_img, pred=pred, actual=actual, conf=conf)

if __name__ == '__main__':
    print('CNN 晶圆缺陷分类 Web 界面 / Wafer Defect CNN Web UI: http://127.0.0.1:5003')
    app.run(debug=True, port=5003)
