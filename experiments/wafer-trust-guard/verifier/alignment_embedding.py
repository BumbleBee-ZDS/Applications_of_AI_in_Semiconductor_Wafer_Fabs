"""L2 意图对齐（Embedding 层）：千问 qwen3.7-text-embedding 计算『意图对齐分』。

思路：
- 把『用户需求』与『Recipe 的自然语言描述』分别向量化；
- 用 numpy 计算余弦相似度，作为『意图对齐分』；
- 规则：相似度 < 0.7 判定为『意图偏离』（Agent 没干用户要的事）。

可靠性约定：所有外部调用均 try/except —— DashScope 不可用时自动降级为
本地『工艺语义特征』兜底向量，保证 Demo 不崩且结果可复现。
"""

import re

import numpy as np

import config

SIMILARITY_THRESHOLD = 0.7  # 低于该值判定为『意图偏离』

try:
    import dashscope as _dashscope
    from dashscope import TextEmbedding as _TextEmbedding

    _HAS_DASHSCOPE = bool(config.DASHSCOPE_API_KEY)
    if _HAS_DASHSCOPE:
        _dashscope.api_key = config.DASHSCOPE_API_KEY
except Exception:
    _HAS_DASHSCOPE = False

_LAST_BACKEND = "未使用"  # 最近一次 embed 实际使用的后端（dashscope / 本地兜底）


def embed_text(text: str) -> np.ndarray:
    """文本 → 向量：优先千问 Embedding，失败自动降级到本地语义特征向量。"""
    global _LAST_BACKEND
    if _HAS_DASHSCOPE:
        try:
            resp = _TextEmbedding.call(model=config.QWEN_EMBEDDING_MODEL, input=text)
            if resp.status_code == 200:
                vec = resp.output["embeddings"][0]["embedding"]
                arr = np.asarray(vec, dtype=float)
                norm = np.linalg.norm(arr)
                out = arr / norm if norm > 0 else arr
                _LAST_BACKEND = f"dashscope:{config.QWEN_EMBEDDING_MODEL}"
                return out
        except Exception:
            pass  # 降级到本地兜底
    _LAST_BACKEND = "本地兜底向量"
    return _mock_embed(text)


def recipe_to_description(recipe: dict) -> str:
    """把 Recipe 转成一段自然语言描述，作为 Embedding 对齐的比对对象。"""
    cooling = "并配置了冷却步骤" if recipe.get("cooling_required") else "工艺结束直接出炉"
    return (
        f"使用{recipe.get('step_name', '?')}工艺，温度{recipe.get('temperature', 0)}°C，"
        f"气体{recipe.get('gas_type', '?')}，时长{recipe.get('duration_sec', 0)}秒，{cooling}"
    )


def judge_alignment_embedding(user_requirement: str, recipe: dict) -> dict:
    """基于 Embedding 的意图对齐判定。

    返回：{"pass": bool, "similarity": float, "source": str, "reason": str}
    """
    req = (user_requirement or "").strip()
    if not req:
        return {
            "pass": True,
            "similarity": 1.0,
            "source": "跳过",
            "reason": "未提供工艺需求，跳过意图对齐（默认放行）",
        }

    vec_a = embed_text(req)
    vec_b = embed_text(recipe_to_description(recipe))
    denom = float(np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
    sim = float(np.dot(vec_a, vec_b) / denom) if denom > 0 else 0.0

    if sim < SIMILARITY_THRESHOLD:
        return {
            "pass": False,
            "similarity": sim,
            "source": _LAST_BACKEND,
            "reason": f"意图偏离：对齐分 {sim:.3f} < {SIMILARITY_THRESHOLD}，Agent 没有做用户要的工艺",
        }
    return {
        "pass": True,
        "similarity": sim,
        "source": _LAST_BACKEND,
        "reason": f"意图对齐：相似度 {sim:.3f} ≥ {SIMILARITY_THRESHOLD}",
    }


def _mock_embed(text: str) -> np.ndarray:
    """本地兜底：抽取 4 个工艺语义维度（3 种工艺类型 + 冷却），做单位向量。

    仅用于 API 不可用时保证 Demo 不崩、结论可复现。
    """
    t = (text or "").lower()
    feats = [
        1.0 if _any_in(t, ("扩散", "高温", "diffusion", "退火", "炉管")) else 0.0,
        1.0 if _any_in(t, ("刻蚀", "蚀刻", "etch")) else 0.0,
        1.0 if _any_in(t, ("清洗", "clean")) else 0.0,
        1.0 if _any_in(t, ("冷却", "降温", "cooling")) else 0.0,
    ]
    v = np.asarray(feats, dtype=float)
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v


def _any_in(text: str, keys: tuple) -> bool:
    return any(k in text for k in keys)