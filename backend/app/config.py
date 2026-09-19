"""Application settings, read from environment variables or a .env file.

Everything configurable lives here so the rest of the code never touches os.environ.
"""

from datetime import date
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Providers that can do BOTH judgment and generation (an LLM_PROVIDER value).
GenerationProviderName = Literal["anthropic", "openai", "rules"]
# Anything that can own the judgment step. Includes "jev", which only judges — it has no
# generation, so it can never be an LLM_PROVIDER value, only a JUDGMENT_PROVIDER override.
JudgmentProviderName = GenerationProviderName | Literal["jev"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    database_url: str = "sqlite:///./crm.db"

    # "auto" picks anthropic or openai based on which API key is present, else rules.
    llm_provider: GenerationProviderName | Literal["auto"] = "auto"
    # Optional override so a different provider can own typed judgments. Set to "jev" to use
    # TypeSafe's Jev for priority/waiting_on/urgency while the LLM still writes the narrative.
    judgment_provider: JudgmentProviderName | None = None
    llm_model: str | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    typesafe_api_key: str | None = None

    # Pins "today" for demos so staleness math matches the sample data (last note: 2026-08-31).
    crm_today: date | None = None

    # Where the built frontend lives when served by FastAPI (Docker / production).
    frontend_dist: str = "../frontend/dist"


@lru_cache
def get_settings() -> Settings:
    return Settings()
