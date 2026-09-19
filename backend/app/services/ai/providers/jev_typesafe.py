"""TypeSafe (Jev) judgment provider.

Jev is a "System One" model: it answers narrow typed questions with calibrated probabilities
instead of writing prose. See docs/AI_DESIGN.md, "Jev (TypeSafe System One) as an optional
judgment provider", for how it's turned on and how it compares against the LLM.

This class implements JudgmentProvider only — priority, waiting_on, needs_attention, urgency,
and a real confidence score — never generation, so it is always paired with a language model
that writes the words. `judge()` and `_to_judgment()` are split so the conversion logic (the
part with real decisions in it) is unit-testable without a network call; see
tests/test_jev_provider.py.
"""

import typesafe_sdk as ts

from app.schemas import Judgment, Priority, WaitingOn
from app.services.ai.generation import AIProviderError
from app.services.ai.prompts import PRIORITY_CRITERIA, WAITING_ON_CRITERIA
from app.services.context import CustomerContext

# Ordered from calmest to most urgent. The Score primitive returns a probability-weighted
# position across this list (e.g. 2.16 out of 0..3), which we normalise into Judgment's 0..1 range.
URGENCY_LEVELS = ["no urgency", "worth tracking", "act this week", "act today"]


class JevJudgmentProvider:
    name = "jev"

    def __init__(self, api_key: str | None = None) -> None:
        self._client = ts.TypeSafeClient(api_key=api_key)

    def judge(self, context: CustomerContext) -> Judgment:
        try:
            result = self._client.system_one(
                state=context.model_dump(mode="json"),
                questions={
                    "priority": ts.Choice(
                        instructions=(
                            "Given this account's interaction history and signals, how "
                            "urgently should the salesperson act on it?"
                        ),
                        criteria=PRIORITY_CRITERIA,
                    ),
                    "waiting_on": ts.Choice(
                        instructions="Who owes the next move in this relationship?",
                        criteria=WAITING_ON_CRITERIA,
                    ),
                    "needs_attention": ts.Noul(
                        instructions=(
                            "Should the salesperson act on this account within the next 7 days?"
                        )
                    ),
                    "urgency": ts.Score(
                        instructions=(
                            "How urgent is it for the salesperson to act on this account right now?"
                        ),
                        criteria=URGENCY_LEVELS,
                    ),
                },
            )
        except ts.TypeSafeError as error:
            raise AIProviderError(f"Jev request failed: {error}") from error
        return _to_judgment(result)


def _to_judgment(result: ts.SystemOneResponse) -> Judgment:
    """Pure conversion from a system_one response to our domain Judgment. No network here."""
    priority: Priority = result.choices["priority"].choice  # type: ignore[assignment]
    waiting_on: WaitingOn = result.choices["waiting_on"].choice  # type: ignore[assignment]
    urgency_score = result.scores["urgency"].score / (len(URGENCY_LEVELS) - 1)
    return Judgment(
        priority=priority,
        needs_attention=result.nouls["needs_attention"].noul >= 0.5,
        waiting_on=waiting_on,
        urgency_score=min(max(urgency_score, 0.0), 1.0),
        confidence=result.choices["priority"].confidence,
    )
