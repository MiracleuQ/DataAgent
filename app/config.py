from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "DataAgent"
    app_env: str = "dev"

    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_sec: int = 60

    history_db_path: str = "data/history.db"
    chart_output_dir: str = "data/charts"
    sandbox_timeout_sec: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
