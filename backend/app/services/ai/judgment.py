"""Judgment protocol: typed decisions about a customer (priority, attention, urgency).

Kept separate from text generation on purpose. A System One model such as TypeSafe's Jev
returns exactly this kind of typed answer, which is why `providers/jev_typesafe.py` implements
this protocol and nothing else. See docs/AI_DESIGN.md, "Jev (TypeSafe System One) as an
optional judgment provider".
"""

from typing import Protocol

from app.schemas import Judgment
from app.services.context import CustomerContext


class JudgmentProvider(Protocol):
    name: str

    def judge(self, context: CustomerContext) -> Judgment: ...
