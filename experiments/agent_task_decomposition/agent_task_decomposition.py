"""
🔬 Agent 任务分解与执行 / Agent Task Decomposition & Execution
对应第17章(SA 符号行为融合)与第23章(Agent 规划)
Chapters 17 (SA fusion) & 23 (Agent planning)

规划-执行: 目标 -> 子任务列表 -> 逐个调用工具 -> 汇总报告
Plan-then-execute: goal -> subtasks -> run tools -> completion report
"""
import os
import json
import urllib.request

# ---------- 1. 工具集 / tool set ----------
def query_yield_data(layer='光刻层'):
    """查询良率数据 / query yield data"""
    return json.dumps({'layer': layer, 'yield': 84.2, 'trend': [85.1, 84.8, 84.2, 83.5],
                       'note': '良率连续4周下降'}, ensure_ascii=False)

def analyze_wafermap(layer='光刻层'):
    """缺陷模式分析 / analyze wafer map"""
    return json.dumps({'layer': layer, 'dominant_defect': '边缘环形缺陷',
                       'estimated_loss': 1.6, 'zone': 'edge'}, ensure_ascii=False)

def analyze_fdc(step='光刻'):
    """FDC 参数相关性分析 / analyze FDC correlation"""
    return json.dumps({'step': step, 'correlated_params': {'focus_offset': 0.82, 'exposure_dose': 0.71},
                       'outlier_tool': 'LITHO-02'}, ensure_ascii=False)

def suggest_actions(finding='边缘环形缺陷'):
    """生成优化建议 / suggest actions"""
    return json.dumps({'finding': finding,
                       'actions': ['检查LITHO-02焦点窗口', 'FEM复核曝光剂量', '边缘清洗参数优化'],
                       'expected_gain': '良率 +0.8~1.2%'}, ensure_ascii=False)

TOOLS = {
    'query_yield_data': {'fn': query_yield_data},
    'analyze_wafermap': {'fn': analyze_wafermap},
    'analyze_fdc': {'fn': analyze_fdc},
    'suggest_actions': {'fn': suggest_actions},
}

# ---------- 2. 任务分解 / task decomposition ----------
def get_api_key():
    return os.environ.get('DEEPSEEK_API_KEY', '').strip()

def call_deepseek(system, user):
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.3, "max_tokens": 400,
    }).encode('utf-8')
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions", data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {get_api_key()}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data['choices'][0]['message']['content']

DEFAULT_PLAN = [
    ('收集良率数据', 'query_yield_data', '光刻层'),
    ('缺陷模式分析', 'analyze_wafermap', '光刻层'),
    ('FDC参数相关性分析', 'analyze_fdc', '光刻'),
    ('生成优化建议', 'suggest_actions', '边缘环形缺陷'),
]

def decompose(goal):
    """把目标分解为子任务 / decompose goal into subtasks (rule-based default)"""
    if get_api_key():
        try:
            raw = call_deepseek(
                '你是规划Agent, 把目标分解为有序子任务列表, 每个子任务指定工具与参数。'
                '可用工具: ' + ', '.join(TOOLS) + '。输出JSON数组[{"task":..,"tool":..,"arg":..}]',
                f'目标: {goal}')
            import re
            m = re.search(r'\[.*\]', raw, re.S)
            if m:
                plan = json.loads(m.group(0))
                return [(p['task'], p['tool'], p.get('arg', '')) for p in plan][:6]
        except Exception:
            pass
    return DEFAULT_PLAN

def execute(goal):
    """执行计划并汇总 / execute the plan and summarize"""
    plan = decompose(goal)
    results = []
    for task, tool, arg in plan:
        if tool not in TOOLS:
            results.append({'task': task, 'tool': tool, 'result': '(未知工具 unknown tool)'})
            continue
        try:
            res = TOOLS[tool]['fn'](arg)
        except Exception as e:
            res = str(e)
        results.append({'task': task, 'tool': tool, 'arg': arg, 'result': res})
    # 汇总报告 / completion report
    report = f"【完成报告】针对「{goal}」:\n"
    for r in results:
        report += f"  - {r['task']}: {r['result'][:90]}\n"
    if get_api_key():
        try:
            report = call_deepseek(
                '你是执行Agent, 根据子任务执行结果写一段完成报告(含结论与建议)。',
                json.dumps(results, ensure_ascii=False))
        except Exception:
            pass
    return plan, results, report

# ---------- 3. 演示 + 可视化 / demo + visualization ----------
def main():
    print('=' * 60)
    print('Agent 任务分解与执行 / Task Decomposition & Execution (SA融合)')
    print('模式 / Mode:', 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)')
    goal = '提升光刻层良率, 找出根因并给出优化方案'
    print('\n[目标 goal]:', goal)
    plan, results, report = execute(goal)
    print('\n[任务分解 plan]:')
    for i, (task, tool, arg) in enumerate(plan, 1):
        print(f'  {i}. {task} -> 工具 {tool}({arg})')
    print('\n[执行结果 results]:')
    for r in results:
        print(f'  - {r["task"]}: {r["result"][:70]}')
    print('\n[完成报告 report]:')
    print('  ' + report.replace('\n', '\n  ')[:400])

    # 可视化任务树 / visualize task tree
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    os.makedirs(out_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis('off')
    ax.add_patch(plt.Rectangle((3.8, 3.0), 2.4, 0.8, facecolor='#1A237E', alpha=0.9))
    ax.text(5, 3.4, '目标 goal', ha='center', fontsize=10, color='white', fontweight='bold')
    n = len(plan)
    for i, (task, tool, arg) in enumerate(plan):
        x = 1.0 + i * (8.0 / max(n, 1))
        y = 1.2
        ax.add_patch(plt.Rectangle((x-1.15, y-0.5), 2.3, 1.0, facecolor='#1976D2', alpha=0.85))
        ax.text(x, y + 0.18, task[:7], ha='center', fontsize=8, color='white', fontweight='bold')
        ax.text(x, y - 0.18, tool, ha='center', fontsize=7, color='#E3F2FD')
        ax.plot([5, x], [3.0, 1.7], color='#B0BEC5', lw=1)
    ax.set_title('Agent 任务分解树 / Task Decomposition Tree', fontsize=12, fontweight='bold')
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'task_tree.png'), dpi=140)
    plt.close(fig)
    print('\n[可视化] 任务树已保存 / saved:', os.path.join(out_dir, 'task_tree.png'))
    print('[结论] 规划-执行 Agent 将高层目标落地为可执行任务链(SA融合)。')
    print('  Takeaway: plan-then-execute turns high-level goals into executable task chains (SA).')

if __name__ == '__main__':
    main()
