"""Base class for language-model providers (Anthropic, OpenAI).

One structured API call returns judgment and narrative together. judge() makes the call and
caches the output; narrate() reuses it when it is asked about the same context, so the normal
path costs one round trip. If a different judgment provider decided first (e.g. Jev), narrate()
makes its own call and tells the model which judgment to explain.
"""

import hashlib
from abc import ABC, abstractmethod

from app.schemas import Draft, Judgment, LlmAnalysisOutput, LlmDraftOutput, Narrative
from app.services.ai.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    DRAFT_SYSTEM_PROMPT,
    analysis_user_message,
    draft_user_message,
    judgment_hint,
)
from app.services.ai.providers.llm_common import to_judgment, to_narrative
from app.services.context import CustomerContext

CACHE_LIMIT = 64


class LanguageModelProvider(ABC):
    name: str
    model: str

    def __init__(self) -> None:
        self._cache: dict[str, LlmAnalysisOutput] = {}

    # ---- JudgmentProvider -------------------------------------------------------------------

    def judge(self, context: CustomerContext) -> Judgment:
        return to_judgment(self._analysis_for(context))

    # ---- GenerationProvider -----------------------------------------------------------------

    def narrate(self, context: CustomerContext, judgment: Judgment) -> Narrative:
        output = self._analysis_for(context, judgment)
        return to_narrative(output, context.today)

    def draft_message(self, context: CustomerContext, narrative: Narrative) -> Draft:
        output = self.complete_structured(
            DRAFT_SYSTEM_PROMPT, draft_user_message(context, narrative), LlmDraftOutput
        )
        return Draft(subject=output.subject, body=output.body)

    # ---- internals --------------------------------------------------------------------------

    def _analysis_for(
        self, context: CustomerContext, judgment: Judgment | None = None
    ) -> LlmAnalysisOutput:
        key = _context_key(context)
        cached = self._cache.get(key)
        if cached is not None and _agrees(cached, judgment):
            return cached
        user_message = analysis_user_message(context)
        if judgment is not None:
            user_message = judgment_hint(judgment) + "\n\n" + user_message
        output = self.complete_structured(ANALYSIS_SYSTEM_PROMPT, user_message, LlmAnalysisOutput)
        if len(self._cache) > CACHE_LIMIT:
            self._cache.clear()
        self._cache[key] = output
        return output

    @abstractmethod
    def complete_structured[T](self, system: str, user: str, output_type: type[T]) -> T:
        """Provider-specific structured call. Must raise AIProviderError on any failure."""


def _context_key(context: CustomerContext) -> str:
    return hashlib.sha256(context.model_dump_json().encode()).hexdigest()


def _agrees(output: LlmAnalysisOutput, judgment: Judgment | None) -> bool:
    return judgment is None or (
        output.priority == judgment.priority and output.waiting_on == judgment.waiting_on
    )
