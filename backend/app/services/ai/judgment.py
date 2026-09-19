"""Judgment protocol: typed decisions about a customer (priority, attention, urgency).

Kept separate from text generation on purpose. A System One model such as TypeSafe's Jev
returns exactly this kind of typed answer, so it can implement this protocol later without
touching the rest of the app. See docs/AI_DESIGN.md, section "Extending with Jev".
"""

from typing import Protocol

from app.schemas import Judgment
from app.services.context import CustomerContext


class JudgmentProvider(Protocol):
    name: str

    def judge(self, context: CustomerContext) -> Judgment: ...
