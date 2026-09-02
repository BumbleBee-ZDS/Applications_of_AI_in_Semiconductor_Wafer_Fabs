"""统一配置入口：从 .env 加载 API Key 并导出客户端实例。

- DeepSeek：OpenAI SDK 兼容方式（base_url 默认 https://api.deepseek.com/v1）
- 阿里云 DashScope：Embedding 用千问 qwen3.7-text-embedding

安全约定：代码中不写死任何 API Key，一律从 .env 读取。
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ---- DeepSeek（红队 Agent 生成 + 蓝队 LLM-Judge 共用）----
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ---- 阿里云 DashScope（Embedding 意图对齐层）----
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
QWEN_EMBEDDING_MODEL = os.getenv("QWEN_EMBEDDING_MODEL", "qwen3.7-text-embedding")

# DeepSeek 客户端（OpenAI SDK 兼容方式）
deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL) if DEEPSEEK_API_KEY else None