"""
🔬 LLM 良率周报自动生成 / LLM Yield Report Automation
对应第22章(LLM应用·报告生成) / Chapter 22 (LLMs · report generation)

数据->文本: 结构化良率数据 -> LLM 生成专业周报
Data-to-text: structured yield data -> LLM writes a professional weekly report
"""
import os
import json
import urllib.request

# ---------- 1. 结构化数据 / structured data ----------
DATA = {
    'week': 'W35',
    'yield_trend': [82.1, 83.4, 84.0, 84.8, 85.3],      # 最近5周综合良率 %
    'weeks': ['W31', 'W32', 'W33', 'W34', 'W35'],
    'defect_top3': [
        {'type': '颗粒污染', 'loss': 1.8, 'action': '检查洁净室过滤器'},
        {'type': '边缘环形缺陷', 'loss': 1.2, 'action': '检查光刻焦点窗口'},
        {'type': '簇状缺陷', 'loss': 0.9, 'action': '检查腔体消耗件'},
    ],
    'tools': {'EUV-01': '正常', 'ETCH-03': '维护后待验证', 'CMP-02': '正常'},
    'wip': 835,
    'notable': 'W35良率85.3%创新高; ETCH-03维护后需关注批次良率'
}

# ---------- 2. LLM 调用 / LLM call ----------
def get_api_key():
    return os.environ.get('DEEPSEEK_API_KEY', '').strip()

def call_deepseek(system, user):
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.4, "max_tokens": 800,
    }).encode('utf-8')
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions", data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {get_api_key()}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data['choices'][0]['message']['content']

def mock_report(data):
    """Mock: 模板化周报 / template-based weekly report"""
    trend = data['yield_trend']
    delta = trend[-1] - trend[0]
    top1 = data['defect_top3'][0]
    return (
        f"**{data['week']}周良率周报(周报自动生成)**\n\n"
        f"1. 总体良率: 本周综合良率 {trend[-1]:.1f}%, 环比{'上升' if delta>0 else '下降'} {abs(delta):.1f} 个百分点。\n"
        f"2. 缺陷分析: 主要良率损失来自{top1['type']}(损失{top1['loss']}个百分点), 建议{top1['action']}。\n"
        f"3. 设备状态: 大部分设备正常, ETCH-03 维护后需关注。\n"
        f"4. 下周计划: 继续降低颗粒缺陷密度, 验证 ETCH-03 维护效果。\n"
        f"(Mock LLM 生成)"
    )

SYSTEM = (
    "你是晶圆厂良率工程师, 负责撰写周报。必须严格基于给定数据, 不得编造数字。"
    "报告包含: 1)总体良率与趋势 2)缺陷TOP分析 3)设备状态 4)下周计划。用中文Markdown。"
    "You are a fab yield engineer writing a weekly report. Base it strictly on the data, "
    "never invent numbers. Include: 1)overall yield & trend 2)defect TOP 3)tool status "
    "4)next-week plan. Write in Chinese Markdown."
)

def generate_report():
    llm = call_deepseek if get_api_key() else mock_report
    try:
        report = llm(SYSTEM, f"本周数据(JSON): {json.dumps(DATA, ensure_ascii=False)}\n请生成良率周报。")
    except Exception as e:
        report = mock_report(DATA) + f'\n(API失败 fallback: {e})'
    return report

# ---------- 3. 演示 + 可视化 / demo + visualization ----------
def main():
    print('=' * 60)
    print('LLM 良率周报自动生成 / LLM Yield Report Automation')
    print('模式 / Mode:', 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)')
    report = generate_report()
    print('\n' + report + '\n')

    # 可视化趋势 / visualize the trend
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    os.makedirs(out_dir, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    ax = axes[0]
    ax.plot(DATA['weeks'], DATA['yield_trend'], 'o-', color='#1976D2', lw=2.2)
    ax.set_xlabel('周 week'); ax.set_ylabel('综合良率 %')
    ax.set_title('良率周趋势 / Weekly Yield Trend')
    ax.grid(alpha=0.3)
    ax = axes[1]
    tops = DATA['defect_top3']
    ax.barh([t['type'] for t in tops][::-1], [t['loss'] for t in tops][::-1],
            color=['#F44336', '#FF9800', '#FFC107'])
    ax.set_xlabel('良率损失 % / yield loss')
    ax.set_title('缺陷 TOP3 / Defect TOP3')
    ax.grid(alpha=0.3, axis='x')
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'yield_trend.png'), dpi=140)
    plt.close(fig)
    print('[可视化] 趋势图已保存 / saved:', os.path.join(out_dir, 'yield_trend.png'))
    print('[结论] LLM 将数据转化为可读周报, 自动化日常良率会议材料。')
    print('  Takeaway: LLM turns data into readable reports, automating yield meetings.')

if __name__ == '__main__':
    main()
