"""OpenAI provider using the Chat Completions structured-output helper (completions.parse)."""

import openai

from app.services.ai.generation import AIProviderError
from app.services.ai.providers.llm_base import LanguageModelProvider

DEFAULT_MODEL = "gpt-4.1"


class OpenAIProvider(LanguageModelProvider):
    name = "openai"

    def __init__(self, api_key: str | None, model: str | None = None) -> None:
        super().__init__()
        self.model = model or DEFAULT_MODEL
        self._client = openai.OpenAI(api_key=api_key, max_retries=2, timeout=90.0)

    def complete_structured[T](self, system: str, user: str, output_type: type[T]) -> T:
        try:
            completion = self._client.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format=output_type,
            )
        except openai.OpenAIError as error:
            raise AIProviderError(f"OpenAI request failed: {error}") from error
        message = completion.choices[0].message
        if message.refusal:
            raise AIProviderError(f"OpenAI declined the request: {message.refusal}")
        if message.parsed is None:
            raise AIProviderError("OpenAI returned no parseable structured output")
        return message.parsed
