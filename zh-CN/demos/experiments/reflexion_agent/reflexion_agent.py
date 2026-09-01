"""
🔬 反思型 Agent / Reflexion Agent
对应第23章(Agent 自我改进) / Chapter 23 (Agent self-improvement)

Reflexion 循环: 尝试 -> 评估 -> 反思 -> 重试
Reflexion loop: attempt -> evaluate -> reflect -> retry
"""
import os
import json
import urllib.request

# ---------- 任务: 负载均衡派工 / task: load-balanced dispatch ----------
N_TASKS = 8                # 任务数
N_TOOLS = 3                # 设备数
SPEEDS = [2.0, 1.0, 0.5]   # 设备处理速度

def evaluate(plan):
    """评估方案: 返回最大完工时间与负载均衡度 / evaluate a plan"""
    loads = [0.0] * N_TOOLS
    for task, tool in enumerate(plan):
        loads[tool] += 1.0 / SPEEDS[tool]
    makespan = max(loads)
    balance = max(loads) - min(loads)   # 负载差异越大越不均衡
    return makespan, balance, loads

def get_api_key():
    return os.environ.get('DEEPSEEK_API_KEY', '').strip()

def call_deepseek(system, user):
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.4, "max_tokens": 300,
    }).encode('utf-8')
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions", data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {get_api_key()}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data['choices'][0]['message']['content']

# ---------- Agent: 方案生成与反思 / agent: propose & reflect ----------
def initial_plan():
    """初始方案: 全部任务给最快的设备0 / naive: all to the fastest tool"""
    return [0] * N_TASKS

def reflect(plan, makespan, balance, history):
    """反思: 生成改进方向 / reflection: produce an improvement direction"""
    if get_api_key():
        try:
            return call_deepseek(
                '你是反思型Agent。评估上一轮方案: ' +
                f'计划{plan}, 最大完工时间{makespan:.2f}, 负载差异{balance:.2f}, '
                f'设备速度{SPEEDS}。请反思并输出下一轮改进后的方案(JSON数组, 每元素为设备编号)。',
                '给出改进方案')
        except Exception:
            pass
    # Mock 反思: 把负载最高的设备上的一部分任务移到负载最低/最快的空闲设备
    new_plan = list(plan)
    _, _, loads = evaluate(plan)
    max_i = int(loads.index(max(loads)))
    min_i = int(loads.index(min(loads)))
    moved = False
    for i in range(N_TASKS):
        if new_plan[i] == max_i:
            new_plan[i] = min_i
            moved = True
            break
    if not moved:  # 已均衡, 微调
        new_plan[0] = 0
    return new_plan

def reflexion_run(max_rounds=6):
    """执行 Reflexion 循环 / run the reflexion loop"""
    history = []
    plan = initial_plan()
    for r in range(max_rounds):
        makespan, balance, loads = evaluate(plan)
        history.append({'round': r + 1, 'plan': list(plan), 'makespan': makespan,
                        'balance': balance, 'loads': list(loads)})
        if balance < 0.05:      # 已足够均衡 / balanced enough
            history[-1]['note'] = '达标 converged'
            break
        # 反思并生成新方案 / reflect & propose
        new_plan = reflect(plan, makespan, balance, history)
        if new_plan == plan:
            history[-1]['note'] = '无改进 no improvement'
            break
        plan = new_plan
    return history

# ---------- 演示 + 可视化 / demo + visualization ----------
def main():
    print('=' * 60)
    print('反思型 Agent / Reflexion Agent (自我改进 self-improvement)')
    print('模式 / Mode:', 'DeepSeek API' if get_api_key() else 'Mock LLM (离线 offline)')
    print(f'任务: 把 {N_TASKS} 批任务分配给 {N_TOOLS} 台设备(速度 {SPEEDS}), 使负载均衡')
    history = reflexion_run()
    print('\n[迭代过程 iterations]:')
    for h in history:
        print(f"  轮{h['round']}: 方案{h['plan']} | 最大完工 {h['makespan']:.2f} | "
              f"负载差异 {h['balance']:.2f} {h.get('note', '')}")
    best = min(history, key=lambda h: h['makespan'])
    print(f'\n[最终 best]: 轮{best["round"]} 方案{best["plan"]}, 最大完工时间 {best["makespan"]:.2f}')

    # 可视化 / visualize
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    os.makedirs(out_dir, exist_ok=True)

    rounds = [h['round'] for h in history]
    makespans = [h['makespan'] for h in history]
    balances = [h['balance'] for h in history]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].plot(rounds, makespans, 'o-', color='#1976D2', lw=2)
    axes[0].set_xlabel('轮次 round'); axes[0].set_ylabel('最大完工时间 makespan')
    axes[0].set_title('Reflexion: 完工时间下降 / Makespan over rounds')
    axes[0].grid(alpha=0.3)
    axes[1].plot(rounds, balances, 'o-', color='#2E7D32', lw=2)
    axes[1].set_xlabel('轮次 round'); axes[1].set_ylabel('负载差异 balance gap')
    axes[1].set_title('Reflexion: 负载均衡度提升 / Balance improving')
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'reflexion_curve.png'), dpi=140)
    plt.close(fig)
    print('\n[可视化] 反思曲线已保存 / saved:', os.path.join(out_dir, 'reflexion_curve.png'))
    print('[结论] 反思型 Agent 通过"评估+反思+重试"实现自我改进。')
    print('  Takeaway: evaluate + reflect + retry = Agent self-improvement (Reflexion).')

if __name__ == '__main__':
    main()
