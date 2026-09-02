"""failure —— 失效分析知识库（FA Store）：让 Verifier 拥有『记忆』。

核心隐喻：每一次被 Tape-out Check 拦下的违规，都会写成 FA Report 入库；
下次做类似工艺，资深 PE 会先翻历史 ——『上次扩散炉超温炸过，这次别再犯』。
"""

from failure import embedder, fa_store  # noqa: F401