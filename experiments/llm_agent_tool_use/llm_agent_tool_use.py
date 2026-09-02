"""
🔬 LLM Agent 工具调用 / LLM Agent with Tool Use
对应第23章(Agent 系统) / Chapter 23 (Agent Systems)

ReAct 循环: LLM 思考 -> 调用工具 -> 观察结果 -> 再思考 -> 最终回答
ReAct loop: LLM thinks -> calls a tool -> observes -> thinks again -> final answer
"""
import os
import re
import json
import urllib.request

# ---------- 1. 工具集 / tool set ----------
def query_wip(zone='all'):
    """查询在制品WIP分布 / query WIP distribution"""
    data = {'光刻区': 320, '刻蚀区': 245, '薄膜区': 180, '量测区': 90}
    if zone in data:
        return json.dumps({'zone': zone, 'wip': data[zone]}, ensure_ascii=False)
    return json.dumps({'wip_by_zone': data}, ensure_ascii=False)

def query_tool_status(tool='all'):
    """查询设备状态 / query tool status"""
    data = {'EUV-01': '运行中', 'ETCH-03': '维护中', 'CMP-02': '运行中', '量测-M5': '空闲'}
    if tool in data:
        return json.dumps({'tool': tool, 'status': data[tool]}, ensure_ascii=False)
    return json.dumps({'tools': data}, ensure_ascii=False)

def calc_utilization(tool='EUV-01'):
    """计算设备利用率 / compute tool utilization"""
    util = {'EUV-01': 0.95, 'ETCH-03': 0.62, 'CMP-02': 0.88, '量测-M5': 0.30}
    return json.dumps({'tool': tool, 'utilization': util.get(tool, 0.0)}, ensure_ascii=False)

def get_spec(keyword='压力'):
    """查询工艺规格 / look up a process spec"""
    specs = {'压力': '刻蚀腔体压力 2.0-6.0 mTorr', '温度': '炉管温度均匀性 ±0.5°C',
             'CD': '同型机台 CD 差异 < 1 nm'}
    for k, v in specs.items():
        if k in keyword:
            return json.dumps({'spec': v}, ensure_ascii=False)
    return json.dumps({'error': '未找到相关规格'}, ensure_ascii=False)

TOOLS = {
    'query_wip': {'desc': '查询WIP分布, 参数 zone', 'fn': query_wip},
    'query_tool_status': {'desc': '查询设备状态, 参数 tool', 'fn': query_tool_status},
    'calc_utilization': {'desc': '计算设备利用率, 参数 tool', 'fn': calc_utilization},
    'get_spec': {'desc': '查询工艺规格, 参数 keyword', 'fn': get_spec},
}

# ---------- 2. LLM 调用 / LLM call ----------
def get_api_key():
    return os.environ.get('DEEPSEEK_API_KEY', '').strip()

def call_deepseek(system, user):
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.2, "max_tokens": 300,
    }).encode('utf-8')
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions", data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {get_api_key()}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data['choices'][0]['message']['content']

def mock_llm(system, user, step=0, trace=None):
    """Mock: 第1轮选工具; 后续轮次基于工具结果给出最终回答
    Mock: round 1 picks a tool; later rounds answer with the tool result"""
    trace = trace or []
    if step > 0:
        last = trace[-1] if trace else {}
        if 'result' in last:
            return json.dumps({'final': '根据工具查询结果: ' + last['result'][:90]}, ensure_ascii=False)
        return json.dumps({'final': '信息已足够, 回答完毕。'}, ensure_ascii=False)
    u = user
    if 'WIP' in u or '在制' in u:
        return json.dumps({'action': 'query_wip', 'arg': 'all'}, ensure_ascii=False)
    if '设备' in u or '状态' in u:
        return json.dumps({'action': 'query_tool_status', 'arg': 'all'}, ensure_ascii=False)
    if '利用率' in u:
        return json.dumps({'action': 'calc_utilization', 'arg': 'EUV-01'}, ensure_ascii=False)
    if '规格' in u or '压力' in u or '温度' in u:
        return json.dumps({'action': 'get_spec', 'arg': '压力'}, ensure_ascii=False)
    return json.dumps({'final': '根据已获取的信息, 结论如下: (Mock) ' + user[:40]}, ensure_ascii=False)

SYSTEM = (
    "你是晶圆厂生产调度Agent。你可以调用以下工具: " +
    json.dumps({k: v['desc'] for k, v in TOOLS.items()}, ensure_ascii=False) +
    "。请逐步思考: 若需要信息则输出 {\"action\":\"工具名\",\"arg\":\"参数\"}; "
    "若已有足够信息则输出 {\"final\":\"最终回答\"}。只输出JSON。"
    "You are a fab dispatch agent with the tools above. If you need info, output "
    "{\"action\":..,\"arg\":..}; otherwise output {\"final\":..}. JSON only."
)

# ---------- 3. Agent 循环 / Agent loop ----------
def parse_action(text):
    m = re.search(r'\{.*\}', text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None

def agent_run(question, max_steps=6):
    trace = []          # 调用轨迹 / tool-call trace
    llm = call_deepseek if get_api_key() else mock_llm
    for i in range(max_steps):
        if get_api_key():
            ctx = question + ('\n[工具结果] ' + json.dumps(trace[-1]['result']) if trace else '')
            out = llm(SYSTEM, ctx)
        else:
            out = llm(SYSTEM, question, i, trace)
        act = parse_action(out)
        if act is None:
            trace.append({'step': i+1, 'raw': out[:80]}); break
        if 'final' in act:
            trace.append({'step': i+1, 'final': act['final']})
            return trace, act['final']
        name, arg = act.get('action'), act.get('arg', '')
        if name not in TOOLS:
            trace.append({'step': i+1, 'error': f'未知工具 {name}'}); continue
        result = TOOLS[name]['fn'](arg)
        trace.append({'step': i+1, 'tool': name, 'arg': arg, 'result': result[:120]})
    return trace, trace[-1].get('final', '(未给出最终答案 / no final answer)')

# ---------- 4. 演示 + 可视化 / demo + visualization ----------
def main():
    print('=' * 60)
    print('LLM Agent 工具调用 / LLM Agent Tool Use (ReAct)')
    print('模式 / Mode:', 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)')
    questions = [
        '各区域的在制品WIP分布如何? / What is the WIP distribution?',
        'EUV-01 的利用率是多少? / What is EUV-01 utilization?',
        '刻蚀机腔体压力规格是多少? / What is the etch pressure spec?',
    ]
    for q in questions:
        print('\n[问题 question]:', q)
        trace, final = agent_run(q)
        for t in trace:
            if 'tool' in t:
                print(f"  步骤{t['step']}: 调用工具 {t['tool']}({t.get('arg','')}) -> {t['result'][:60]}")
            elif 'final' in t:
                print(f"  步骤{t['step']}: 最终回答 {t['final'][:60]}")
        print('  [最终答案 final]:', final)

    # 可视化轨迹 / visualize trace
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    os.makedirs(out_dir, exist_ok=True)
    trace, final = agent_run('EUV-01 利用率多少? 顺便看看设备状态')
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 3); ax.axis('off')
    x = 1.2
    for t in trace:
        label = f"{t.get('tool', '回答')}\n{t.get('arg','')}" if 'tool' in t else '最终\n回答'
        color = '#1976D2' if 'tool' in t else '#2E7D32'
        ax.add_patch(plt.Rectangle((x-0.9, 1.0), 1.8, 1.0, facecolor=color, alpha=0.85))
        ax.text(x, 1.5, label, ha='center', fontsize=9, color='white', fontweight='bold')
        if len(trace) > 1 and x < 8.5:
            ax.annotate('', xy=(x+0.95, 1.5), xytext=(x+0.9, 1.5),
                        arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
        x += 2.0
    ax.set_title('Agent 工具调用轨迹 / Tool-Call Trace (ReAct)', fontsize=12, fontweight='bold')
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'agent_trace.png'), dpi=140)
    plt.close(fig)
    print('\n[可视化] 轨迹图已保存 / trace saved:', os.path.join(out_dir, 'agent_trace.png'))
    print('[结论] LLM 通过工具调用获取信息并自主推理, 是 Agent 的核心模式。')
    print('  Takeaway: LLM + tool use = Agent, the core pattern behind fab agents.')

if __name__ == '__main__':
    main()
