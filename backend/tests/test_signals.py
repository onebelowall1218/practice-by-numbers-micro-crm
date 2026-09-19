from datetime import date

from app.models import Interaction
from app.services.signals import compute_signals


def make(id_: str, day: str, notes: str, type_: str = "email") -> Interaction:
    return Interaction(
        id=id_, customer_id="c", type=type_, occurred_at=date.fromisoformat(day), notes=notes
    )


def test_no_interactions_gives_empty_signals():
    signals = compute_signals([], date(2026, 9, 1))
    assert signals.interaction_count == 0
    assert signals.days_since_last_interaction is None
    assert signals.hints == []


def test_days_since_last_interaction_uses_the_latest_date_regardless_of_order():
    interactions = [make("b", "2026-08-25", "later"), make("a", "2026-08-01", "earlier")]
    signals = compute_signals(interactions, date(2026, 9, 1))
    assert signals.days_since_last_interaction == 7
    assert signals.days_since_first_interaction == 31
    assert signals.last_interaction_date == date(2026, 8, 25)


def test_hints_are_found_only_in_the_three_most_recent_interactions():
    interactions = [
        make("1", "2026-07-01", "No response after pricing."),
        make("2", "2026-08-01", "Sent details."),
        make("3", "2026-08-02", "Sent more details."),
        make("4", "2026-08-03", "Do not push aggressively before the planning meeting."),
    ]
    hints = compute_signals(interactions, date(2026, 9, 1)).hints
    assert any("not to push" in h for h in hints)
    assert not any("no response" in h for h in hints)
