# -*- coding: utf-8 -*-
"""将 9 个选定实验项目从 experiments 复制清理到 zh-CN/demos/experiments/
排除: .env(密钥) / .venv / __pycache__ / .git / 压缩包 / 大模型权重 / 可再生数据库"""
import os, shutil

SRC = r'H:\code\traework\AI在半导体晶圆厂的应用\experiments'
DST = r'H:\code\traework\AI在半导体晶圆厂的应用\zh-CN\demos\experiments'

EXCLUDE_DIRS = {'.venv', '__pycache__', '.git', 'node_modules', '.inscode', 'Qwen2-0.5B',
                'checkpoint-12', '.idea', '.vscode', '.pytest_cache'}
EXCLUDE_EXTS = {'.pyc', '.pyo', '.zip'}
EXCLUDE_FILES = {'.env', 'fab_capacity.db', 'training_args.bin'}

# 源目录 -> 目标目录 (None 表示不复制该层)
JOBS = [
    ('ontology_demo/wafer_ontology_mvp', 'wafer_ontology_mvp'),
    ('FabGraph_MVP', 'FabGraph_MVP'),
    ('fab_ontology_text2sql', 'fab_ontology_text2sql'),
    ('FabCapacityAgent', 'FabCapacityAgent'),
    ('fab_ai_rtd_mvp', 'fab_ai_rtd_mvp'),
    ('fab_llm_fine_tuning', 'fab_llm_fine_tuning'),
    ('wafer-trust-guard', 'wafer-trust-guard'),
    ('fab_agent_test', 'fab_agent_test'),
]

def copy_tree(src, dst):
    n_files, n_bytes = 0, 0
    for dp, dns, fns in os.walk(src):
        dns[:] = [d for d in dns if d not in EXCLUDE_DIRS]
        rel = os.path.relpath(dp, src)
        out_dir = dst if rel == '.' else os.path.join(dst, rel)
        os.makedirs(out_dir, exist_ok=True)
        for fn in fns:
            if fn in EXCLUDE_FILES:
                continue
            if os.path.splitext(fn)[1].lower() in EXCLUDE_EXTS:
                continue
            # 微调项目: 排除大二进制
            if fn in ('tokenizer.json', 'adapter_model.safetensors'):
                if 'fab_llm_fine_tuning' in src and 'lora_adapter' in dp:
                    continue
            s = os.path.join(dp, fn)
            t = os.path.join(out_dir, fn)
            shutil.copy2(s, t)
            n_files += 1
            n_bytes += os.path.getsize(s)
    return n_files, n_bytes

# C9S_agent 特殊处理: 顶层有 test.py 与 .env, 真正代码在 C9S_agent/C9S_agent/ 内
def copy_c9s():
    src_top = os.path.join(SRC, 'C9S_agent')
    src_inner = os.path.join(src_top, 'C9S_agent')
    dst = os.path.join(DST, 'C9S_agent')
    os.makedirs(dst, exist_ok=True)
    n_files, n_bytes = 0, 0
    # 顶层散落文件(排除 .env)
    for fn in os.listdir(src_top):
        p = os.path.join(src_top, fn)
        if os.path.isfile(p) and fn not in EXCLUDE_FILES:
            shutil.copy2(p, os.path.join(dst, fn))
            n_files += 1
            n_bytes += os.path.getsize(p)
    # 内层目录
    f, b = copy_tree(src_inner, dst)
    return n_files + f, n_bytes + b

total_files, total_bytes = 0, 0
for src_rel, dst_name in JOBS:
    src = os.path.join(SRC, src_rel.replace('/', os.sep))
    dst = os.path.join(DST, dst_name)
    f, b = copy_tree(src, dst)
    total_files += f
    total_bytes += b
    print('%-28s -> %-26s %5d files  %6.1f MB' % (src_rel, dst_name, f, b / 1048576))

f, b = copy_c9s()
total_files += f
total_bytes += b
print('%-28s -> %-26s %5d files  %6.1f MB' % ('C9S_agent (flattened)', 'C9S_agent', f, b / 1048576))

print('-' * 70)
print('TOTAL: %d files, %.1f MB' % (total_files, total_bytes / 1048576))
