"""Deterministic signals computed from the interaction history.

These are facts, not judgments: how long since the last touch, how many interactions, and
explicit cues found in the notes. They are given to the AI as context and reused by the
rule-based provider as a fallback. Keeping them in code makes them cheap, testable and stable.
"""

import re
from collections import Counter
from datetime import date

from pydantic import BaseModel

from app.models import Interaction

# Phrase -> plain-English hint. Deliberately small; the AI reads the notes anyway.
HINT_RULES: list[tuple[str, str]] = [
    (r"do not push|don't push", "A note asks not to push the customer before a stated time."),
    (r"no response", "A note records no response from the customer."),
    (r"never scheduled", "The customer never scheduled something we sent."),
    (r"no additional follow-up|no follow-up required", "A note says no follow-up is required."),
    (r"decision in|make a decision", "The customer stated a decision timeframe."),
    (r"high-intent", "A note flags this as a high-intent prospect."),
    (r"before september|by september|deadline", "The customer mentioned a deadline."),
    (
        r"asked (if|whether) we can schedule|requested a demo|asked for a",
        "The customer asked us for something.",
    ),
    (r"inactive for", "A note says the prospect has been inactive."),
]


class Signals(BaseModel):
    days_since_last_interaction: int | None
    last_interaction_type: str | None
    last_interaction_date: date | None
    last_interaction_contact: str | None
    days_since_first_interaction: int | None
    interaction_count: int
    counts_by_type: dict[str, int]
    hints: list[str]


def compute_signals(interactions: list[Interaction], today: date) -> Signals:
    ordered = sorted(interactions, key=lambda i: (i.occurred_at, i.id))
    if not ordered:
        return Signals(
            days_since_last_interaction=None,
            last_interaction_type=None,
            last_interaction_date=None,
            last_interaction_contact=None,
            days_since_first_interaction=None,
            interaction_count=0,
            counts_by_type={},
            hints=[],
        )
    last, first = ordered[-1], ordered[0]
    return Signals(
        days_since_last_interaction=(today - last.occurred_at).days,
        last_interaction_type=last.type,
        last_interaction_date=last.occurred_at,
        last_interaction_contact=last.contact.name if last.contact else None,
        days_since_first_interaction=(today - first.occurred_at).days,
        interaction_count=len(ordered),
        counts_by_type=dict(Counter(i.type for i in ordered)),
        hints=find_hints(ordered),
    )


def find_hints(interactions: list[Interaction]) -> list[str]:
    """Return hints from the most recent three interactions only, so stale cues do not linger."""
    recent_text = " ".join(i.notes.lower() for i in interactions[-3:])
    return [hint for pattern, hint in HINT_RULES if re.search(pattern, recent_text)]
