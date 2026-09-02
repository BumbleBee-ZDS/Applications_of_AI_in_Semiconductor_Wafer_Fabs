import subprocess, collections, os

root = r'H:\code\traework\AI在半导体晶圆厂的应用'
r = subprocess.run(['git', '-c', 'core.quotepath=false', 'diff', '--name-only', '1a4862c', 'HEAD'],
                   capture_output=True, text=True, cwd=root, encoding='utf-8', errors='replace')
added = [l for l in r.stdout.splitlines() if l.strip()]

# group new experiments
exp = collections.defaultdict(set)
for p in added:
    if p.startswith('zh-CN/demos/experiments/'):
        parts = p.split('/')
        proj = parts[3]
        exp[proj].add(parts[-1])

print('=== 新增实验项目: %d 个 ===' % len(exp))
for proj in sorted(exp):
    files = sorted(exp[proj])
    py = [f for f in files if f.endswith('.py')]
    has_web = 'web_app.py' in files
    print('  %-34s %2d 文件  入口:%s  Web:%s' % (proj, len(files), ','.join(py)[:30], 'yes' if has_web else 'no'))

# on-disk check of all experiments now
print()
print('=== experiments 磁盘现状(含新增) ===')
expdir = os.path.join(root, 'zh-CN', 'demos', 'experiments')
for d in sorted(os.listdir(expdir)):
    full = os.path.join(expdir, d)
    if os.path.isdir(full):
        n = sum(len(f) for _, _, f in os.walk(full))
        print('  %-34s %3d 文件' % (d, n))
