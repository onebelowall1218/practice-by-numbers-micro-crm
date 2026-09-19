"""Anthropic provider using the Messages API structured-output helper (messages.parse)."""

import anthropic

from app.services.ai.generation import AIProviderError
from app.services.ai.providers.llm_base import LanguageModelProvider

DEFAULT_MODEL = "claude-sonnet-5"


class AnthropicProvider(LanguageModelProvider):
    name = "anthropic"

    def __init__(self, api_key: str | None, model: str | None = None) -> None:
        super().__init__()
        self.model = model or DEFAULT_MODEL
        self._client = anthropic.Anthropic(api_key=api_key, max_retries=2, timeout=90.0)

    def complete_structured[T](self, system: str, user: str, output_type: type[T]) -> T:
        try:
            response = self._client.messages.parse(
                model=self.model,
                max_tokens=4000,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_format=output_type,
            )
        except anthropic.APIError as error:
            raise AIProviderError(f"Anthropic request failed: {error}") from error
        if response.stop_reason == "refusal":
            raise AIProviderError("Anthropic declined the request (stop_reason=refusal)")
        if response.parsed_output is None:
            raise AIProviderError("Anthropic returned no parseable structured output")
        return response.parsed_output
