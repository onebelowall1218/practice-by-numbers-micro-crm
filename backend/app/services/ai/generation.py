"""Generation protocol: the words the user reads (summary, reason, next action, drafts).

Generation receives the Judgment so the narrative always explains a decision that was already
made, instead of making its own. Only language models implement this protocol.
"""

from typing import Protocol

from app.schemas import Draft, Judgment, Narrative
from app.services.context import CustomerContext


class GenerationProvider(Protocol):
    name: str
    model: str | None

    def narrate(self, context: CustomerContext, judgment: Judgment) -> Narrative: ...

    def draft_message(self, context: CustomerContext, narrative: Narrative) -> Draft: ...


class AIProviderError(RuntimeError):
    """Raised by any provider when it cannot return a usable result. The analyzer falls back."""
