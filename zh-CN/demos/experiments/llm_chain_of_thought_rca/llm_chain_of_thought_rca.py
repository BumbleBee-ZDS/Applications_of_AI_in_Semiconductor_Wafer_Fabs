"""
🔬 思维链良率根因分析 / Chain-of-Thought RCA
对应第18章(NB 神经符号融合) / Chapter 18 (NB Neuro-Symbolic Fusion)

CoT 分步推理 + 符号规则校验: 观察 -> 假设 -> 验证 -> 结论
CoT stepwise reasoning + symbolic rule check: observe -> hypothesize -> verify -> conclude
"""
import os
import re
import json
import urllib.request

# ---------- 1. 符号规则库(用于校验 LLM 结论) / symbolic rule base ----------
RULES = [
    {'pattern': ['边缘环形', '颗粒'], 'conclusion': '光刻焦点偏移', 'confidence': 0.8},
    {'pattern': ['中心圆形', '高密度'], 'conclusion': '光刻镜头污染', 'confidence': 0.7},
    {'pattern': ['簇状', '腔体'], 'conclusion': '腔体微粒脱落', 'confidence': 0.9},
    {'pattern': ['划痕'], 'conclusion': '机械搬运问题', 'confidence': 0.75},
    {'pattern': ['随机颗粒'], 'conclusion': '洁净室污染', 'confidence': 0.6},
]

def rule_check(facts_text, llm_conclusion):
    """用符号规则校验 LLM 结论 / verify the LLM conclusion against rules"""
    hits = []
    for r in RULES:
        if all(p in facts_text for p in r['pattern']):
            hits.append(r)
    if not hits:
        return '无规则匹配 no rule matched', 0.0
    best = max(hits, key=lambda r: r['confidence'])
    agree = best['conclusion'] in llm_conclusion or any(
        k in llm_conclusion for k in [best['conclusion'][:2]])
    return best['conclusion'], best['confidence'], agree

# ---------- 2. LLM 调用 / LLM call ----------
def get_api_key():
    return os.environ.get('DEEPSEEK_API_KEY', '').strip()

def call_deepseek(system, user):
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.3, "max_tokens": 500,
    }).encode('utf-8')
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions", data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {get_api_key()}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data['choices'][0]['message']['content']

COT_SYSTEM = (
    "你是良率工程师。请严格按四步推理: 1)观察 2)假设 3)验证 4)结论。"
    "每步用【观察】【假设】【验证】【结论】开头。最后一行必须为'结论: xxx'。"
    "You are a yield engineer. Reason strictly in four steps: "
    "1)Observe 2)Hypothesize 3)Verify 4)Conclude. Use 【观察】【假设】【验证】【结论】 tags. "
    "The last line must be '结论: xxx'."
)

def mock_cot(facts_text):
    """Mock: 模板化 CoT 推理, 结论与符号规则库对齐
    template CoT; conclusion aligned with the symbolic rule base"""
    hit = None
    for r in RULES:
        if all(p in facts_text for p in r['pattern']):
            hit = r
            break
    root = hit['conclusion'] if hit else '工艺参数偏移导致系统性缺陷'
    steps = [
        ('【观察】', f'晶圆图显示: {facts_text}。缺陷集中于特定区域。'),
        ('【假设】', f'假设该缺陷与{root}相关的工艺参数偏移有关。'),
        ('【验证】', '对照FDC信号与历史案例, 参数在窗口边缘, 与假设一致。'),
        ('【结论】', f'根因: {root}, 建议按规则库对应措施处理。'),
    ]
    return '\n'.join(f'{tag}{txt}' for tag, txt in steps)

def run_cot(facts_text):
    llm = call_deepseek if get_api_key() else mock_cot
    try:
        if get_api_key():
            raw = llm(COT_SYSTEM, f"缺陷观察事实: {facts_text}\n请按四步推理根因。")
        else:
            raw = llm(f"缺陷观察事实: {facts_text}\n请按四步推理根因。")
    except Exception as e:
        raw = mock_cot(facts_text)
        raw += f'\n(API失败 fallback: {e})'
    # 提取结论 / extract conclusion
    m = re.search(r'结论[:：]\s*(.+)', raw)
    conclusion = m.group(1).strip() if m else raw[-60:]
    return raw, conclusion

# ---------- 3. 演示 + 可视化 / demo + visualization ----------
def main():
    print('=' * 60)
    print('思维链良率根因分析 / CoT RCA (神经+符号 neural+symbolic)')
    print('模式 / Mode:', 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)')
    cases = [
        '晶圆图显示边缘环形缺陷, 缺陷类型为颗粒, 曝光剂量偏低',
        '晶圆图显示簇状缺陷, 簇中心对应某腔体位置',
        '晶圆图显示中心圆形缺陷, 缺陷密度高',
    ]
    all_steps = []
    for facts in cases:
        print('\n[事实 facts]:', facts)
        raw, conclusion = run_cot(facts)
        for line in raw.split('\n')[:4]:
            print('  ', line[:70])
        # 符号校验 / symbolic check
        best = rule_check(facts, conclusion)
        if len(best) == 3:
            print(f'  [符号校验 rule check]: 规则结论={best[0]}, 与LLM一致={best[2]}')
        else:
            print(f'  [符号校验 rule check]: {best}')
        all_steps.append((facts, raw))

    # 可视化 / visualize reasoning steps
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    os.makedirs(out_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 3); ax.axis('off')
    stages = ['观察 Observe', '假设 Hypothesize', '验证 Verify', '结论 Conclude']
    colors = ['#1976D2', '#F9A825', '#7B1FA2', '#2E7D32']
    x = 1.3
    for i, (s, c) in enumerate(zip(stages, colors)):
        ax.add_patch(plt.Rectangle((x-1.05, 1.0), 2.1, 1.0, facecolor=c, alpha=0.88))
        ax.text(x, 1.5, s, ha='center', fontsize=10, color='white', fontweight='bold')
        if i < 3:
            ax.annotate('', xy=(x+1.1, 1.5), xytext=(x+1.05, 1.5),
                        arrowprops=dict(arrowstyle='->', color='#666', lw=1.6))
        x += 2.3
    ax.set_title('CoT 思维链推理步骤 / Chain-of-Thought Steps', fontsize=12, fontweight='bold')
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'cot_steps.png'), dpi=140)
    plt.close(fig)
    print('\n[可视化] 推理步骤图已保存 / steps saved:', os.path.join(out_dir, 'cot_steps.png'))
    print('[结论] CoT 让 LLM 分步推理, 配合符号规则校验, 提升可解释性与可靠性。')
    print('  Takeaway: CoT + rule check = more explainable, more reliable LLM reasoning.')

if __name__ == '__main__':
    main()
