from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


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

    @field_validator("llm_api_key")
    @classmethod
    def validate_llm_api_key(cls, v: str) -> str:
        if not v:
            logger.warning("LLM_API_KEY is not set. LLM calls will fail.")
        return v

    @field_validator("llm_timeout_sec")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v < 10:
            logger.warning("llm_timeout_sec is very low, may cause frequent timeouts")
        return v

    @field_validator("sandbox_timeout_sec")
    @classmethod
    def validate_sandbox_timeout(cls, v: int) -> int:
        if v < 5:
            logger.warning("sandbox_timeout_sec is very low")
        return v

    def validate_startup(self) -> List[str]:
        warnings = []
        errors = []

        if not self.llm_api_key:
            errors.append("LLM_API_KEY is required but not set")

        if self.app_env == "production":
            if self.llm_api_key == "EMPTY_KEY":
                errors.append("Production environment requires valid LLM_API_KEY")
            if self.sandbox_timeout_sec > 60:
                warnings.append("sandbox_timeout_sec is high for production")

        data_dir = Path("data")
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Created data directory")

        charts_dir = Path(self.chart_output_dir)
        if not charts_dir.exists():
            charts_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Created charts directory: %s", charts_dir)

        for w in warnings:
            logger.warning(w)
        for e in errors:
            logger.error(e)

        return errors


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_settings() -> bool:
    settings = get_settings()
    errors = settings.validate_startup()
    if errors:
        logger.error("Configuration validation failed with %d errors", len(errors))
        return False
    logger.info("Configuration validation passed")
    return True
