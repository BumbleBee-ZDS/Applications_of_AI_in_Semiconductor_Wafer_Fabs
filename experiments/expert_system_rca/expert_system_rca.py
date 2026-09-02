"""
🔬 专家系统缺陷诊断 / Expert-System Root Cause Analysis
对应第14章(符号主义) / Chapter 14 (Symbolism)

前向推理专家系统: 规则库 -> 事实输入 -> 推理链 -> 诊断结论
Forward-chaining expert system: rule base -> facts -> inference chain -> diagnosis
"""
import os
from dataclasses import dataclass, field
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(OUT, exist_ok=True)

# ---------- 规则库 / Rule base ----------
@dataclass
class Rule:
    id: str
    premises: list      # 前提条件(全部满足才触发)
    conclusion: str     # 结论(根因)
    confidence: float   # 置信度
    advice: str         # 建议措施

RULES = [
    Rule('R001', ['边缘环形缺陷', '缺陷类型=颗粒'], '光刻焦点偏移', 0.80, '检查光刻机焦距与FEM窗口'),
    Rule('R002', ['中心圆形缺陷', '缺陷密度高'], '光刻镜头污染', 0.70, '检查光刻机镜头3 的洁净度'),
    Rule('R003', ['簇状缺陷', '簇中心对应腔体'], '腔体微粒脱落', 0.90, '检查对应腔体消耗件状态'),
    Rule('R004', ['划痕缺陷'], '机械搬运问题', 0.75, '检查AMHS/机械手搬运路径与末端'),
    Rule('R005', ['随机颗粒缺陷'], '洁净室污染', 0.60, '检查洁净室粒子计数与过滤器'),
    Rule('R006', ['边缘环形缺陷', '缺陷类型=颗粒', '曝光剂量偏低'], '边缘清洗不良', 0.80, '检查边缘清洗工艺'),
    Rule('R007', ['图案变形', '缺陷类型=桥接'], '刻蚀负载效应', 0.85, '检查刻蚀速率均匀性/图案密度'),
]

# ---------- 前向推理引擎 / forward-chaining engine ----------
def forward_chain(facts):
    """给定事实集, 前向推理出所有可触发规则, 按置信度排序
    given facts, fire all applicable rules, sort by confidence"""
    fired = []
    facts = set(facts)
    for rule in RULES:
        if all(p in facts for p in rule.premises):
            fired.append(rule)
    fired.sort(key=lambda r: -r.confidence)
    return fired

def diagnose(facts):
    fired = forward_chain(facts)
    if not fired:
        return None, '未匹配到规则 / no rule matched —— 建议补充量测/复查'
    top = fired[0]
    return top, None

# ---------- 推理链可视化 / inference chain visualization ----------
def plot_chain(facts, fired):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis('off')

    # 事实框 / fact boxes
    nf = len(facts)
    fx = [1.0 + i * (8.0 / max(nf, 1)) for i in range(nf)]
    for x, f in zip(fx, facts):
        ax.add_patch(plt.Rectangle((x-0.95, 3.1), 1.9, 0.7, facecolor='#E3F2FD',
                                   edgecolor='#1976D2', lw=1.5))
        ax.text(x, 3.45, f[:8], ha='center', fontsize=9)
    ax.text(5, 3.9, '观察事实 Facts', ha='center', fontsize=10, color='#0D47A1', fontweight='bold')

    # 规则框 / rule boxes
    nr = len(fired)
    rx = [1.0 + i * (8.0 / max(nr, 1)) for i in range(nr)]
    for x, r in zip(rx, fired):
        ax.add_patch(plt.Rectangle((x-0.95, 1.6), 1.9, 0.8, facecolor='#FFF9C4',
                                   edgecolor='#F9A825', lw=1.5))
        ax.text(x, 2.15, r.id, ha='center', fontsize=10, fontweight='bold', color='#795548')
        ax.text(x, 1.85, f'置信度 {r.confidence:.2f}', ha='center', fontsize=8)
        for fxp in fx:
            ax.annotate('', xy=(x, 2.45), xytext=(fxp, 3.1),
                        arrowprops=dict(arrowstyle='->', color='#B0BEC5', lw=0.8))
    ax.text(5, 2.6, '规则匹配 Rules (前向推理)', ha='center', fontsize=10, color='#E65100', fontweight='bold')

    # 结论框 / conclusion box
    top = fired[0] if fired else None
    cx = 5.0
    ax.add_patch(plt.Rectangle((cx-2.4, 0.2), 4.8, 0.9, facecolor='#E8F5E9',
                               edgecolor='#2E7D32', lw=2))
    if top:
        ax.text(cx, 0.75, f'诊断: {top.conclusion}', ha='center', fontsize=11, fontweight='bold', color='#1B5E20')
        ax.text(cx, 0.4, f'置信度 {top.confidence:.2f} | 建议: {top.advice}', ha='center', fontsize=8, color='#2E7D32')
        for x in rx:
            ax.annotate('', xy=(cx, 1.15), xytext=(x, 1.6),
                        arrowprops=dict(arrowstyle='->', color='#4CAF50', lw=1.2))
    ax.text(5, 0.05, '结论 Conclusion', ha='center', fontsize=10, color='#1B5E20', fontweight='bold')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'inference_chain.png'), dpi=140)
    plt.close(fig)

# ---------- 演示 / demo cases ----------
def main():
    print('=' * 60)
    print('专家系统缺陷诊断 / Expert-System RCA (前向推理 forward chaining)')
    cases = [
        ['边缘环形缺陷', '缺陷类型=颗粒', '曝光剂量偏低'],
        ['簇状缺陷', '簇中心对应腔体'],
        ['划痕缺陷'],
        ['随机颗粒缺陷', '图案变形'],
    ]
    for facts in cases:
        print('\n[输入 facts]:', ' + '.join(facts))
        top, err = diagnose(facts)
        if top:
            print(f'  → 诊断 diagnosis: {top.conclusion} (置信度 {top.confidence})')
            print(f'  → 建议 advice: {top.advice}')
            fired = forward_chain(facts)
            plot_chain(facts, fired)
            print('  → 推理链图已保存 / inference chain saved')
        else:
            print(f'  → {err}')
    print('\n[结论] 专家系统将工程师经验编码为规则, 提供可解释的自动诊断。')
    print('  Takeaway: rules encode expert experience into explainable auto-diagnosis.')

if __name__ == '__main__':
    main()
