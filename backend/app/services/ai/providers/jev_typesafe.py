"""Placeholder for a TypeSafe (Jev) judgment provider. Not implemented in this version.

Jev is a "System One" model: it answers narrow typed questions with calibrated probabilities
instead of writing prose. That matches the JudgmentProvider protocol exactly. The questions it
would answer, over the same CustomerContext JSON the language model receives today:

    priority        Choice   options: high | medium | low
    waiting_on      Choice   options: us | customer | nobody
    needs_attention Noul     "Should the salesperson act on this account within 7 days?"
    urgency_score   Score    levels from "no urgency" to "act today"

The returned probabilities would fill Judgment.confidence, letting the analyzer route
low-confidence accounts to the language model for a second opinion. Wiring it in means:
implement judge() below, add "jev" to ProviderName in app/config.py, and set JUDGMENT_PROVIDER=jev.
See docs/AI_DESIGN.md, section "Extending with Jev".
"""

from app.schemas import Judgment
from app.services.context import CustomerContext


class JevJudgmentProvider:
    name = "jev"

    def judge(self, context: CustomerContext) -> Judgment:  # pragma: no cover - future work
        raise NotImplementedError("Jev provider is a documented extension point, not yet built.")
