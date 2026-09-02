"""失效分析知识库 · Embedder：千问 qwen3.7-text-embedding 封装。

统一入口 embed(text) -> List[float]：
- 模型从 .env 读取（QWEN_EMBEDDING_MODEL，默认 qwen3.7-text-embedding）；
- 异常兜底：任何失败都返回零向量 [0.0]，绝不向上抛错（保证 Demo 不崩）。
"""

import config

try:
    import dashscope as _dashscope
    from dashscope import TextEmbedding as _TextEmbedding

    _AVAILABLE = bool(config.DASHSCOPE_API_KEY)
    if _AVAILABLE:
        _dashscope.api_key = config.DASHSCOPE_API_KEY
except Exception:
    _AVAILABLE = False


def embed(text: str) -> list:
    """文本 → 向量（List[float]）。失败返回零向量，不报错。"""
    if _AVAILABLE:
        try:
            resp = _TextEmbedding.call(model=config.QWEN_EMBEDDING_MODEL, input=text)
            if resp.status_code == 200:
                return list(resp.output["embeddings"][0]["embedding"])
        except Exception:
            pass
    return [0.0]