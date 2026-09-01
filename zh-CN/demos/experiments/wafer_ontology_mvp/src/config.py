from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env 文件位于项目根目录 (wafer_ontology_mvp/)，使用绝对路径避免工作目录影响
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
# SQLite 数据库也放在项目根目录
SQLITE_PATH = str(Path(__file__).resolve().parent.parent / "fab_ontology.db")


class Settings(BaseSettings):
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str
    SQLITE_DB_PATH: str = SQLITE_PATH
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")


settings = Settings()
