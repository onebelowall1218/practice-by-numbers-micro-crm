"""Chooses which providers to use from settings. The only place provider classes are constructed."""

from functools import lru_cache

from app.config import ProviderName, Settings, get_settings
from app.services.ai.generation import GenerationProvider
from app.services.ai.judgment import JudgmentProvider
from app.services.ai.providers.llm_anthropic import AnthropicProvider
from app.services.ai.providers.llm_openai import OpenAIProvider
from app.services.ai.providers.rules import RulesProvider


def resolve_provider_name(settings: Settings) -> ProviderName:
    if settings.llm_provider != "auto":
        return settings.llm_provider
    if settings.anthropic_api_key:
        return "anthropic"
    if settings.openai_api_key:
        return "openai"
    return "rules"


def build_provider(name: ProviderName, settings: Settings):
    if name == "anthropic":
        return AnthropicProvider(settings.anthropic_api_key, settings.llm_model)
    if name == "openai":
        return OpenAIProvider(settings.openai_api_key, settings.llm_model)
    return RulesProvider()


@lru_cache
def get_providers() -> tuple[JudgmentProvider, GenerationProvider]:
    """Returns (judgment, generation). They are the same object unless JUDGMENT_PROVIDER is set."""
    settings = get_settings()
    generation = build_provider(resolve_provider_name(settings), settings)
    judgment_name = settings.judgment_provider
    judgment = generation if judgment_name is None else build_provider(judgment_name, settings)
    return judgment, generation
