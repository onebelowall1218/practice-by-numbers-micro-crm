from datetime import date, datetime

from app.schemas import CustomerSummaryOut, FollowUpOut, SignalsOut
from app.services.dashboard import bucket_for, build_buckets

TODAY = date(2026, 9, 1)


def summary(name: str, follow_up: date | None, completed: bool = False) -> CustomerSummaryOut:
    return CustomerSummaryOut(
        id=name,
        name=name,
        status="prospect",
        follow_up=FollowUpOut(
            date=follow_up, source="ai", completed_at=datetime(2026, 9, 1) if completed else None
        ),
        signals=SignalsOut(
            days_since_last_interaction=3,
            last_interaction_type="email",
            last_interaction_date=TODAY,
            interaction_count=1,
            hints=[],
        ),
        analysis=None,
        contacts=[],
    )


def test_past_follow_up_is_overdue():
    assert bucket_for(summary("a", date(2026, 8, 30)), TODAY) == "overdue"


def test_follow_up_within_seven_days_is_due_soon():
    assert bucket_for(summary("a", TODAY), TODAY) == "due_soon"
    assert bucket_for(summary("a", date(2026, 9, 8)), TODAY) == "due_soon"


def test_follow_up_after_seven_days_is_later():
    assert bucket_for(summary("a", date(2026, 9, 9)), TODAY) == "later"


def test_completed_follow_up_is_done_even_if_overdue():
    assert bucket_for(summary("a", date(2026, 8, 1), completed=True), TODAY) == "done"


def test_build_buckets_sorts_by_follow_up_date_when_priority_is_equal():
    buckets = build_buckets([summary("late", date(2026, 9, 5)), summary("soon", TODAY)], TODAY)
    assert [c.name for c in buckets["due_soon"]] == ["soon", "late"]
