"""Chooses which providers to use from settings. The only place provider classes are constructed."""

from functools import lru_cache

from app.config import GenerationProviderName, JudgmentProviderName, Settings, get_settings
from app.services.ai.generation import GenerationProvider
from app.services.ai.judgment import JudgmentProvider
from app.services.ai.providers.jev_typesafe import JevJudgmentProvider
from app.services.ai.providers.llm_anthropic import AnthropicProvider
from app.services.ai.providers.llm_openai import OpenAIProvider
from app.services.ai.providers.rules import RulesProvider


def resolve_provider_name(settings: Settings) -> GenerationProviderName:
    if settings.llm_provider != "auto":
        return settings.llm_provider
    if settings.anthropic_api_key:
        return "anthropic"
    if settings.openai_api_key:
        return "openai"
    return "rules"


def build_generation_provider(
    name: GenerationProviderName, settings: Settings
) -> GenerationProvider:
    if name == "anthropic":
        return AnthropicProvider(settings.anthropic_api_key, settings.llm_model)
    if name == "openai":
        return OpenAIProvider(settings.openai_api_key, settings.llm_model)
    return RulesProvider()


def build_judgment_provider(name: JudgmentProviderName, settings: Settings) -> JudgmentProvider:
    if name == "jev":
        return JevJudgmentProvider(settings.typesafe_api_key)
    return build_generation_provider(name, settings)


@lru_cache
def get_providers() -> tuple[JudgmentProvider, GenerationProvider]:
    """Returns (judgment, generation). They are the same object unless JUDGMENT_PROVIDER is set."""
    settings = get_settings()
    generation = build_generation_provider(resolve_provider_name(settings), settings)
    judgment_name = settings.judgment_provider
    judgment = (
        generation if judgment_name is None else build_judgment_provider(judgment_name, settings)
    )
    return judgment, generation
