"""
🔬 多 Agent 协作诊断 / Multi-Agent Collaboration
对应第23章(多Agent架构) / Chapter 23 (Multi-Agent Architecture)

主持人编排: 咨询工艺/设备/良率/调度四个专业Agent -> 汇总最终决策
Coordinator orchestrates: consult process/equipment/yield/dispatch agents -> final decision
"""
import os
import json
import urllib.request

# ---------- 1. 专业 Agent 定义 / specialist agents ----------
# 每个 Agent 有名称、职责、系统提示词 / each agent: name, role, system prompt
AGENTS = {
    'process':  {'name': '工艺Agent Process', 'role': '工艺参数与窗口',
                 'sys': '你是工艺工程师, 从工艺参数/窗口角度分析问题, 给出专业意见。'},
    'equipment':{'name': '设备Agent Equipment', 'role': '设备状态与维护',
                 'sys': '你是设备工程师, 从设备状态/维护/机台匹配角度分析, 给出专业意见。'},
    'yield':    {'name': '良率Agent Yield', 'role': '数据与根因',
                 'sys': '你是良率工程师, 从数据/晶圆图/根因分析角度给出专业意见。'},
    'dispatch': {'name': '调度Agent Dispatch', 'role': '排程与产能',
                 'sys': '你是生产调度, 从排程/产能/瓶颈角度给出专业意见。'},
}

def get_api_key():
    return os.environ.get('DEEPSEEK_API_KEY', '').strip()

def call_deepseek(system, user):
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.4, "max_tokens": 200,
    }).encode('utf-8')
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions", data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {get_api_key()}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data['choices'][0]['message']['content']

# ---------- 2. Mock 意见生成 / mock opinions ----------
MOCK_OPINIONS = {
    'process':  '工艺视角: 建议检查光刻焦点与刻蚀速率均匀性, 疑似工艺窗口边缘。',
    'equipment':'设备视角: 疑似设备参数漂移, 建议检查对应机台FDC信号与PM状态。',
    'yield':    '良率视角: 晶圆图呈边缘环形缺陷, 损失约1.5个百分点, 建议RCA。',
    'dispatch': '调度视角: 相关批次在瓶颈设备排队, 建议调整派工优先级。',
}

def mock_agent(agent_key, question):
    return f"[{AGENTS[agent_key]['name']}] {MOCK_OPINIONS[agent_key]}"

# ---------- 3. 主持人编排 / coordinator orchestration ----------
def consult_agent(agent_key, question):
    """咨询单个 Agent / consult one agent"""
    if get_api_key():
        try:
            return call_deepseek(AGENTS[agent_key]['sys'], question)
        except Exception as e:
            return mock_agent(agent_key, question) + f' (API fallback: {e})'
    return mock_agent(agent_key, question)

def run_collaboration(question):
    """主持人收集各 Agent 意见并汇总 / coordinator collects & synthesizes"""
    opinions = {}
    for key in ['process', 'equipment', 'yield', 'dispatch']:
        opinions[key] = consult_agent(key, question)
    # 汇总 / synthesize: mock 直接合并; API 模式可再调用主持人 LLM
    summary = '综合四部门意见, 最终决策: 优先执行RCA定位根因, 同步检查设备FDC与PM状态, '
    summary += '若确认工艺窗口边缘则调整参数, 调度侧临时提高相关批次优先级。'
    if get_api_key():
        try:
            joined = '\n'.join(f'{AGENTS[k]["name"]}: {v}' for k, v in opinions.items())
            summary = call_deepseek(
                '你是工厂主持人, 综合以下四个专业Agent的意见, 给出可执行的最终决策(3条以内)。',
                f'问题: {question}\n{joined}')
        except Exception:
            pass
    return opinions, summary

# ---------- 4. 演示 + 可视化 / demo + visualization ----------
def main():
    print('=' * 60)
    print('多 Agent 协作诊断 / Multi-Agent Collaboration')
    print('模式 / Mode:', 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)')
    question = '近三天光刻层良率下降1.8%, 晶圆图显示边缘环形缺陷, 请诊断并给出处理方案。'
    print('\n[问题 question]:', question)
    opinions, summary = run_collaboration(question)
    for key, op in opinions.items():
        print(f'\n  → {AGENTS[key]["name"]} ({AGENTS[key]["role"]}):')
        print(f'    {op[:80]}')
    print(f'\n  【主持人决策 / coordinator decision】:')
    print(f'    {summary[:120]}')

    # 可视化协作流程 / visualize collaboration flow
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    os.makedirs(out_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 5); ax.axis('off')
    # 主持人居中
    ax.add_patch(plt.Rectangle((4.0, 2.1), 2.0, 1.2, facecolor='#1A237E', alpha=0.9))
    ax.text(5, 2.7, '主持人\nCoordinator', ha='center', va='center', fontsize=10, color='white', fontweight='bold')
    # 四个专业 Agent
    agents_pos = [('process', 1.2, 4.2), ('equipment', 8.8, 4.2), ('yield', 1.2, 0.7), ('dispatch', 8.8, 0.7)]
    for key, x, y in agents_pos:
        ax.add_patch(plt.Rectangle((x-1.5, y-0.45), 3.0, 0.9, facecolor='#1976D2', alpha=0.85))
        ax.text(x, y, AGENTS[key]['name'], ha='center', va='center', fontsize=9, color='white', fontweight='bold')
        ax.annotate('', xy=(4.9, 2.7), xytext=(x, y + (0.9 if y < 2.5 else -0.9)),
                    arrowprops=dict(arrowstyle='<->', color='#888', lw=1.2))
    ax.set_title('多 Agent 协作流程 / Multi-Agent Collaboration Flow', fontsize=12, fontweight='bold')
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'agent_collab.png'), dpi=140)
    plt.close(fig)
    print('\n[可视化] 协作流程图已保存 / saved:', os.path.join(out_dir, 'agent_collab.png'))
    print('[结论] 多 Agent 通过角色分工与主持人编排实现跨部门协同。')
    print('  Takeaway: role separation + coordinator orchestration = fab multi-agent teams.')

if __name__ == '__main__':
    main()
