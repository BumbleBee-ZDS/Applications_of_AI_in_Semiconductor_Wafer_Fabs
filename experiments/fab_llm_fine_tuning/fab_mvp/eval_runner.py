"""
评估实验: 验证"小模型预处理 + 强模型" 优于 "直接强模型"
================================================================
实验设计 (隔离小模型质量问题):
  - 用 eval.jsonl 中的标准 JSON 模拟"理想小模型输出"
  - 对每个用例跑两条路径:
    增强路径: DeepSeek + 标准mode_a JSON上下文 (模拟微调良好的小模型)
    直接路径: DeepSeek 无上下文 (仅原始口语问题)
  - 自动化指标对比:
    1. 知识库表名引用数  (YIELD_SUMMARY/PROCESS_LOG/... 7张表)
    2. SQL模板引用正确性  (是否提到 eval.jsonl 标注的正确 SQL_TMPL_xxx)
    3. SQL代码块数       (```sql 块数量)
    4. 实体命中率         (标准JSON entities中的值在输出中出现比例)
    5. 领域缩写使用数     (CP/FT/WAT/SPC/OOC/PM 等在输出中出现数)

运行:
  .venv\\Scripts\\python.exe -m fab_mvp.eval_runner --n 10
  .venv\\Scripts\\python.exe -m fab_mvp.eval_runner --n 10 --mode mode_c
"""
import os
import json
import re
import argparse
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from fab_mvp.knowledge_base import FAB_SCHEMA, SQL_TEMPLATES, GLOSSARY

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")

# DeepSeek 强模型 (与 agent.py 一致)
_llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0.3,
    max_tokens=1500,
)

# ============================================================
# 指标计算
# ============================================================
TABLE_NAMES = list(FAB_SCHEMA.keys())  # 7张表
TEMPLATE_IDS = list(SQL_TEMPLATES.keys())  # 8个模板
GLOSSARY_KEYS = list(GLOSSARY.keys())  # 35个缩写


def count_table_refs(text: str) -> int:
    """指标1: 输出中引用了多少个知识库表名"""
    return sum(1 for t in TABLE_NAMES if t in text)


def check_template_correct(text: str, expected_template: str) -> dict:
    """指标2: 是否提到正确的SQL模板ID; 以及提到几个模板"""
    mentioned = [tid for tid in TEMPLATE_IDS if tid in text]
    return {
        "correct": expected_template in mentioned,
        "mentioned_count": len(mentioned),
        "mentioned": mentioned,
    }


def count_sql_blocks(text: str) -> int:
    """指标3: SQL代码块数量"""
    return len(re.findall(r"```sql", text, re.IGNORECASE))


def entity_hit_rate(text: str, entities: dict) -> dict:
    """指标4: 标准JSON entities中的值在输出中出现比例"""
    vals = []
    for v in entities.values():
        if isinstance(v, str) and len(v) > 1:
            vals.append(v)
        elif isinstance(v, dict):
            vals.extend(str(x) for x in v.values() if isinstance(x, str) and len(x) > 1)
    if not vals:
        return {"hit": 0, "total": 0, "rate": 0.0}
    hit = sum(1 for v in vals if v in text)
    return {"hit": hit, "total": len(vals), "rate": round(hit / len(vals), 2)}


def count_glossary_abbr(text: str) -> int:
    """指标5: 领域缩写使用数 (用词边界匹配避免误匹配)"""
    cnt = 0
    for k in GLOSSARY_KEYS:
        if re.search(r"\b" + re.escape(k) + r"\b", text):
            cnt += 1
    return cnt


def compute_metrics(text: str, expected_template: str, entities: dict) -> dict:
    """计算全部指标"""
    tmpl = check_template_correct(text, expected_template)
    ent = entity_hit_rate(text, entities)
    return {
        "table_refs": count_table_refs(text),
        "template_correct": tmpl["correct"],
        "template_mentioned_cnt": tmpl["mentioned_count"],
        "sql_blocks": count_sql_blocks(text),
        "entity_hit": ent["hit"],
        "entity_total": ent["total"],
        "entity_rate": ent["rate"],
        "glossary_abbr": count_glossary_abbr(text),
        "text_len": len(text),
    }


# ============================================================
# 两条路径的 prompt (与 agent.py 保持一致)
# ============================================================
def build_enhanced_prompt(query: str, mode_a_json: dict, mode_label: str) -> str:
    """增强路径 prompt: DeepSeek + 标准小模型JSON上下文"""
    context_str = json.dumps(mode_a_json, ensure_ascii=False, indent=2)
    return (
        f"你是晶圆厂资深数据工程师。一位工程师用口语提问:\n「{query}」\n\n"
        f"一个小模型已经对该问题做了预处理(模式: {mode_label}), 输出如下结构化上下文:\n{context_str}\n\n"
        f"请基于该上下文, 给出最终回答。要求:\n"
        f"1. 若上下文含 template_id, 请给出对应的SQL(可用知识库模板并填充参数);\n"
        f"2. 若上下文含 enhanced_query, 请据此说明分析思路与涉及表;\n"
        f"3. 输出简洁, 包含【分析思路】和【SQL】两部分。"
    )


def build_direct_prompt(query: str) -> str:
    """直接路径 prompt: DeepSeek 无上下文 (对比基线)"""
    return (
        f"你是晶圆厂数据工程师。请回答以下问题, 若需要查询数据请给出SQL:\n「{query}」"
    )


# ============================================================
# 主流程
# ============================================================
def run_eval(n: int = 10, mode: str = "mode_a"):
    eval_path = os.path.join(DATA_DIR, "eval.jsonl")
    cases = []
    with open(eval_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    cases = cases[:n]
    print(f"加载 {len(cases)} 条评估用例 (mode={mode})\n")

    mode_label = {"mode_a": "领域感知增强", "mode_b": "术语翻译", "mode_c": "SQL模板路由"}.get(mode, mode)

    results = []
    for i, c in enumerate(cases):
        q = c["user_query"]
        # 取标准JSON作为"理想小模型输出"
        if mode == "mode_a":
            small_out = c["mode_a_enhance"]
        elif mode == "mode_b":
            small_out = {"translated": c["mode_b_translate"]}
        else:
            small_out = c["mode_c_route"]
        # 期望模板与实体 (从mode_a_enhance和mode_c_route提取)
        expected_tmpl = c["mode_c_route"]["template_id"]
        entities = c["mode_a_enhance"].get("entities", {})

        print(f"[{i+1}/{len(cases)}] {q[:40]}...  (期望模板: {expected_tmpl})")

        # 增强路径
        prompt_e = build_enhanced_prompt(q, small_out, mode_label)
        try:
            enhanced_text = _llm.invoke(prompt_e).content
        except Exception as e:
            enhanced_text = f"[ERROR] {e}"

        # 直接路径
        prompt_d = build_direct_prompt(q)
        try:
            direct_text = _llm.invoke(prompt_d).content
        except Exception as e:
            direct_text = f"[ERROR] {e}"

        m_e = compute_metrics(enhanced_text, expected_tmpl, entities)
        m_d = compute_metrics(direct_text, expected_tmpl, entities)

        results.append({
            "query": q,
            "expected_template": expected_tmpl,
            "enhanced_metrics": m_e,
            "direct_metrics": m_d,
            "enhanced_text": enhanced_text,
            "direct_text": direct_text,
        })

    # 保存详细结果
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    detail_path = os.path.join(OUTPUT_DIR, "eval_detail.json")
    with open(detail_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n详细结果已保存: {detail_path}")

    # 汇总统计
    print_summary(results)
    save_summary(results, mode)


def print_summary(results: list):
    n = len(results)
    print("\n" + "=" * 70)
    print("汇总对比 (增强路径 vs 直接路径, 均值)")
    print("=" * 70)
    metrics = ["table_refs", "template_correct", "template_mentioned_cnt",
               "sql_blocks", "entity_hit", "entity_rate", "glossary_abbr", "text_len"]
    labels = ["知识库表名引用数", "正确模板命中(0/1)", "模板引用数",
              "SQL代码块数", "实体命中数", "实体命中率", "领域缩写数", "文本长度"]
    print(f"{'指标':<20} {'增强路径':>12} {'直接路径':>12} {'差值':>10} {'增强胜':>8}")
    print("-" * 70)
    for m, label in zip(metrics, labels):
        vals_e = [r["enhanced_metrics"][m] for r in results]
        vals_d = [r["direct_metrics"][m] for r in results]
        avg_e = sum(vals_e) / n
        avg_d = sum(vals_d) / n
        diff = avg_e - avg_d
        win = sum(1 for e, d in zip(vals_e, vals_d) if e > d)
        print(f"{label:<20} {avg_e:>12.2f} {avg_d:>12.2f} {diff:>+10.2f} {win:>5}/{n}")

    # 模板正确率
    tmpl_correct_e = sum(1 for r in results if r["enhanced_metrics"]["template_correct"])
    tmpl_correct_d = sum(1 for r in results if r["direct_metrics"]["template_correct"])
    print("-" * 70)
    print(f"{'模板正确率':<20} {tmpl_correct_e/n*100:>11.1f}% {tmpl_correct_d/n*100:>11.1f}%")


def save_summary(results: list, mode: str):
    n = len(results)
    summary = {
        "mode": mode,
        "n_cases": n,
        "metrics": {},
    }
    metric_keys = ["table_refs", "template_correct", "template_mentioned_cnt",
                   "sql_blocks", "entity_hit", "entity_rate", "glossary_abbr", "text_len"]
    for mk in metric_keys:
        vals_e = [r["enhanced_metrics"][mk] for r in results]
        vals_d = [r["direct_metrics"][mk] for r in results]
        summary["metrics"][mk] = {
            "enhanced_avg": round(sum(vals_e) / n, 2),
            "direct_avg": round(sum(vals_d) / n, 2),
            "diff": round(sum(vals_e) / n - sum(vals_d) / n, 2),
            "enhanced_wins": sum(1 for e, d in zip(vals_e, vals_d) if e > d),
        }
    summary["template_accuracy"] = {
        "enhanced": sum(1 for r in results if r["enhanced_metrics"]["template_correct"]),
        "direct": sum(1 for r in results if r["direct_metrics"]["template_correct"]),
    }
    path = os.path.join(OUTPUT_DIR, "eval_summary.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"汇总已保存: {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10, help="评估用例数")
    ap.add_argument("--mode", type=str, default="mode_a",
                    choices=["mode_a", "mode_b", "mode_c"],
                    help="用哪种模式的标注作为理想小模型输出")
    args = ap.parse_args()
    run_eval(args.n, args.mode)
