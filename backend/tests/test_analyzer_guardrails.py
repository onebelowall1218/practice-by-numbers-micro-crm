from datetime import date

from app.schemas import Narrative
from app.services.ai.analyzer import apply_guardrails
from app.services.context import CustomerContext, TimelineEntry
from app.services.signals import Signals

TODAY = date(2026, 9, 1)


def context() -> CustomerContext:
    return CustomerContext(
        today=TODAY,
        customer_id="c1",
        customer_name="Test Dental",
        status="prospect",
        relationship_started=date(2026, 1, 1),
        contacts=[],
        timeline=[TimelineEntry(id="int_1", date=TODAY, type="note", contact_name=None, notes="x")],
        signals=Signals(
            days_since_last_interaction=0,
            last_interaction_type="note",
            last_interaction_date=TODAY,
            last_interaction_contact=None,
            days_since_first_interaction=0,
            interaction_count=1,
            counts_by_type={"note": 1},
            hints=[],
        ),
    )


def narrative(**overrides) -> Narrative:
    base = dict(
        relationship_summary="s",
        priority_reason="r",
        next_action="a",
        suggested_follow_up_date=TODAY,
        follow_up_rationale="w",
        open_items=[],
        evidence_ids=["int_1"],
    )
    return Narrative(**{**base, **overrides})


def test_follow_up_dates_in_the_past_are_moved_to_today():
    fixed = apply_guardrails(narrative(suggested_follow_up_date=date(2026, 8, 1)), context())
    assert fixed.suggested_follow_up_date == TODAY


def test_unknown_evidence_ids_are_dropped():
    fixed = apply_guardrails(narrative(evidence_ids=["int_1", "int_999"]), context())
    assert fixed.evidence_ids == ["int_1"]


def test_open_items_are_capped_at_three():
    fixed = apply_guardrails(narrative(open_items=["a", "b", "c", "d"]), context())
    assert len(fixed.open_items) == 3
