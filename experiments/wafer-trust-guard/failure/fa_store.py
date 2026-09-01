"""失效分析知识库（FA Store）：本地 JSON 文件存储 + 向量检索。

核心隐喻：每一次被 Tape-out Check 拦下的违规，都会写成 FA Report 入库；
下次做类似工艺，资深 PE 先翻历史 —— 让 Verifier 拥有『记忆』。

轻量实现（MVP）：不用 Chroma/FAISS，直接存 failure_log.json（Json 文件），
每次启动 app 自动加载，数据不丢。

物理隔离：本模块只属于 Verifier 一方；Generator（红队/正常）绝对不允许读取
failure/ 目录 —— 设计不知道验证的历史。
"""

import json
import os
from datetime import datetime

import numpy as np

from failure.embedder import embed

# 知识库文件路径（可用环境变量 WAFER_FA_LOG_PATH 覆盖，默认项目根目录）
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FA_LOG_PATH = os.getenv("WAFER_FA_LOG_PATH", os.path.join(_PROJECT_ROOT, "failure_log.json"))

MATCH_THRESHOLD = 0.6  # 相似度 ≥ 0.6 才算『相似历史』

# 首次运行自动播种的 FA 历史档案（模拟真实工厂沉淀下来的失效案例）
_SEED_CASES = [
    {
        "requirement": "高温扩散，需要冷却",
        "block_reason": "温度1300°C且未设置冷却，导致晶圆翘曲",
        "verifier_layer": "LLM_Judge",
        "recipe": {"step_name": "DIFFUSION", "temperature": 1300, "duration_sec": 720, "cooling_required": False, "gas_type": "N2", "cooling_sec": 0},
    },
    {
        "requirement": "清洗晶圆表面",
        "block_reason": "使用了Ar而非O2，去污失败",
        "verifier_layer": "L1静态门禁",
        "recipe": {"step_name": "CLEAN", "temperature": 80, "duration_sec": 60, "cooling_required": False, "gas_type": "Ar", "cooling_sec": 0},
    },
    {
        "requirement": "刻蚀多晶硅",
        "block_reason": "时长仅20秒，刻蚀不完整",
        "verifier_layer": "LLM_Judge",
        "recipe": {"step_name": "ETCH", "temperature": 250, "duration_sec": 20, "cooling_required": False, "gas_type": "N2", "cooling_sec": 0},
    },
]


def _load() -> list:
    if os.path.exists(FA_LOG_PATH):
        try:
            with open(FA_LOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def _save(cases: list) -> None:
    with open(FA_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)


def _next_id(cases: list) -> str:
    """生成 FA-YYYY-NNN 编号（按年份递增）。"""
    prefix = f"FA-{datetime.now().year}"
    nums = []
    for c in cases:
        cid = str(c.get("id", ""))
        if cid.startswith(prefix):
            try:
                nums.append(int(cid.rsplit("-", 1)[-1]))
            except ValueError:
                pass
    return f"{prefix}-{max(nums, default=0) + 1:03d}"


def count() -> int:
    """知识库现有案例数。"""
    return len(_load())


def add_case(req: str, recipe: dict, reason: str, layer: str) -> dict:
    """记录一次被拦截的违规：拼接文本 → 向量化 → 写入 failure_log.json。

    参数：
        req:     用户输入的原始需求
        recipe:  被拦截的 Recipe（dict）
        reason:  拦截原因（中文，如『冷却缺失 / 超温 / 气体违规』）
        layer:   拦截该案例的验证层（L1静态门禁 / L2意图偏离 / LLM_Judge）
    返回：新入库的案例 dict（含自动生成的 FA 编号）。
    """
    cases = _load()
    text = f"需求：{req}。违规原因：{reason}"
    case = {
        "id": _next_id(cases),
        "requirement": req,
        "recipe_snippet": _snippet(recipe),
        "block_reason": reason,
        "verifier_layer": layer,
        "embedding": embed(text),
    }
    cases.append(case)
    _save(cases)
    return case


def search(req: str, top_k: int = 3) -> list:
    """按输入需求检索历史失效案例。

    - 对 req 做 embedding，与库中每条案例的 embedding 算余弦相似度；
    - 只返回相似度 ≥ MATCH_THRESHOLD 的最相似 top_k 条；
    - 返回字段：id / requirement / block_reason / verifier_layer / similarity。
    """
    cases = _load()
    if not cases:
        return []
    qvec = np.asarray(embed(req), dtype=float)
    scored = []
    for c in cases:
        sim = _cosine(qvec, np.asarray(c.get("embedding", []), dtype=float))
        if sim >= MATCH_THRESHOLD:
            scored.append((sim, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "id": c.get("id", "?"),
            "requirement": c.get("requirement", ""),
            "block_reason": c.get("block_reason", ""),
            "verifier_layer": c.get("verifier_layer", ""),
            "similarity": sim,
        }
        for sim, c in scored[:top_k]
    ]


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or a.shape != b.shape:
        return 0.0
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _snippet(recipe: dict) -> str:
    """被拦截的 Recipe 关键字段（用于 FA Report 留档）。"""
    keys = ("step_name", "temperature", "duration_sec", "cooling_required", "gas_type", "cooling_sec")
    return json.dumps({k: recipe.get(k) for k in keys if k in recipe}, ensure_ascii=False)


# 首次启动自动播种（文件不存在时），让『记忆』一开始就有内容
if not os.path.exists(FA_LOG_PATH):
    _cases = []
    for i, s in enumerate(_SEED_CASES, 1):
        _text = f"需求：{s['requirement']}。违规原因：{s['block_reason']}"
        _cases.append(
            {
                "id": f"FA-2024-{i:03d}",
                "requirement": s["requirement"],
                "recipe_snippet": json.dumps(s["recipe"], ensure_ascii=False),
                "block_reason": s["block_reason"],
                "verifier_layer": s["verifier_layer"],
                "embedding": embed(_text),
            }
        )
    _save(_cases)