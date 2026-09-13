"""FabWiki 全局配置。

集中管理：路径、LLM 配置、Mock 模式开关。
Mock 模式是一等公民：无 LLM_API_KEY 时 `LLM_AVAILABLE=False`，上层自动降级 Mock。
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录（fabwiki/）
BASE_DIR = Path(__file__).resolve().parent

# 是否加载 .env；不存在时静默跳过，各配置变量取环境变量的兜底值
load_dotenv(BASE_DIR / ".env")

# ---------- 路径 ----------
DB_PATH = BASE_DIR / "data" / "fab.db"                 # SQLite（模拟 Oracle 数仓）
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
RAW_DIR = KNOWLEDGE_DIR / "raw"
RAW_DICT_DIR = RAW_DIR / "dictionary"                  # L1 抽取产物 {表名}.json
WIKI_DIR = KNOWLEDGE_DIR / "wiki"
WIKI_TABLES_DIR = WIKI_DIR / "tables"
WIKI_COLUMNS_DIR = WIKI_DIR / "columns"
WIKI_METRICS_DIR = WIKI_DIR / "metrics"
WIKI_LINEAGE_DIR = WIKI_DIR / "lineage"
SPEC_DIR = KNOWLEDGE_DIR / "spec"
INDEX_MD = KNOWLEDGE_DIR / "index.md"

# ---------- LLM 配置 ----------
# 优先用 LLM_* 三件套；未设 LLM_API_KEY 时，兼容从 .env 已有的厂商 Key 兜底，
# 方便复用现有 DEEPSEEK_API_KEY / DASHSCOPE_API_KEY。
_LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip() or os.getenv("DEEPSEEK_API_KEY", "").strip()
LLM_API_KEY = _LLM_API_KEY.strip()
LLM_BASE_URL = (os.getenv("LLM_BASE_URL", "").strip()
                or os.getenv("DEEPSEEK_BASE_URL", "").strip()
                or "https://api.deepseek.com/v1").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat").strip()

# Mock 开关：无 Key 则整体降级 Mock
LLM_AVAILABLE = bool(LLM_API_KEY)

# LLM 统一调用参数
LLM_TIMEOUT_SECONDS = 120
LLM_MAX_RETRIES = 1
LLM_TEMPERATURE = 0.2


def ensure_dirs() -> None:
    """确保所有输出目录存在（幂等）。"""
    for d in (DB_PATH.parent, RAW_DICT_DIR, WIKI_TABLES_DIR, WIKI_COLUMNS_DIR,
              WIKI_METRICS_DIR, WIKI_LINEAGE_DIR, SPEC_DIR):
        d.mkdir(parents=True, exist_ok=True)


# 依赖注入点：便于测试时替换 DB/知识目录
def get_db_path() -> Path:
    v = os.getenv("FABWIKI_DB_PATH", "").strip()
    return Path(v) if v else DB_PATH