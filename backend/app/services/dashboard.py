"""Dashboard rules: which bucket a customer lands in and how buckets are ordered.

Pure functions over API models so the ranking is unit-testable and lives in one place.
"""

from datetime import date, timedelta

from app.schemas import BucketKey, CustomerSummaryOut

DUE_SOON_DAYS = 7
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def bucket_for(customer: CustomerSummaryOut, today: date) -> BucketKey:
    follow_up = customer.follow_up
    if follow_up.completed_at is not None:
        return "done"
    if follow_up.date is None:
        return "later"
    if follow_up.date < today:
        return "overdue"
    if follow_up.date <= today + timedelta(days=DUE_SOON_DAYS):
        return "due_soon"
    return "later"


def sort_key(customer: CustomerSummaryOut) -> tuple:
    priority = customer.analysis.judgment.priority if customer.analysis else "low"
    days_since = customer.signals.days_since_last_interaction or 0
    return (PRIORITY_RANK[priority], customer.follow_up.date or date.max, -days_since)


def build_buckets(
    customers: list[CustomerSummaryOut], today: date
) -> dict[BucketKey, list[CustomerSummaryOut]]:
    buckets: dict[BucketKey, list[CustomerSummaryOut]] = {
        "overdue": [],
        "due_soon": [],
        "later": [],
        "done": [],
    }
    for customer in customers:
        buckets[bucket_for(customer, today)].append(customer)
    for key in buckets:
        buckets[key].sort(key=sort_key)
    return buckets
