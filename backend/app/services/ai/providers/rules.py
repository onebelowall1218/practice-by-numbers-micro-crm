"""Rule-based provider: deterministic judgment and narrative with no API call.

Used when no API key is configured, as the fallback when a language model fails, and in tests.
It is intentionally simple and readable; it is a safety net, not the product.
"""

from datetime import date, timedelta

from app.schemas import Draft, Judgment, Narrative, Priority, WaitingOn
from app.services.context import CustomerContext

FOLLOW_UP_DAYS: dict[Priority, int] = {"high": 1, "medium": 5, "low": 21}


class RulesProvider:
    name = "rules"
    model = None

    def judge(self, context: CustomerContext) -> Judgment:
        priority, waiting_on, _ = decide(context)
        return Judgment(
            priority=priority,
            needs_attention=priority != "low",
            waiting_on=waiting_on,
            urgency_score={"high": 0.9, "medium": 0.5, "low": 0.1}[priority],
            confidence=None,
        )

    def narrate(self, context: CustomerContext, judgment: Judgment) -> Narrative:
        _, _, reason = decide(context)
        contact = context.contacts[0].name if context.contacts else "the customer"
        recent = context.timeline[-3:]
        recent_text = " ".join(f"{e.date.isoformat()}: {e.notes}" for e in recent)
        new = context.new_interaction
        return Narrative(
            relationship_summary=(
                f"{context.customer_name} is a {context.status} with "
                f"{context.signals.interaction_count} recorded interactions. "
                f"Recent activity: {recent_text}"
            ),
            interaction_summary=first_sentence(new.notes) if new else None,
            priority_reason=reason,
            next_action=f"Check in with {contact} about the most recent conversation.",
            suggested_follow_up_date=context.today
            + timedelta(days=FOLLOW_UP_DAYS[judgment.priority]),
            follow_up_rationale="Rule-based default spacing for this priority level.",
            open_items=[],
            evidence_ids=[e.id for e in recent],
        )

    def draft_message(self, context: CustomerContext, narrative: Narrative) -> Draft:
        contact = context.contacts[0].name.split()[0] if context.contacts else "there"
        return Draft(
            subject=f"Following up - {context.customer_name}",
            body=(
                f"Hi {contact},\n\nI wanted to follow up on our recent conversation. "
                f"{narrative.next_action}\n\n"
                "Would a short call this week work for you?\n\n[Your name]"
            ),
        )


def decide(context: CustomerContext) -> tuple[Priority, WaitingOn, str]:
    """The whole rule set in one readable function: returns (priority, waiting_on, reason)."""
    hints = " ".join(context.signals.hints)
    days = context.signals.days_since_last_interaction or 0

    if "not to push" in hints:
        return "low", "customer", "The customer asked us not to push before a stated time."
    if "no follow-up is required" in hints:
        return "low", "nobody", "The last note says no follow-up is required."
    if "asked us for something" in hints:
        return "high", "us", "The customer asked us for something in a recent interaction."
    if "no response" in hints or "never scheduled" in hints:
        return "high", "customer", f"Waiting on the customer with no reply for {days} days."
    if context.status == "prospect":
        if days <= 7:
            return "high", "us", f"Active prospect; last touch {days} days ago."
        if days > 30:
            return "medium", "customer", f"Prospect has gone quiet for {days} days."
        return "medium", "customer", f"Prospect; last touch {days} days ago."
    if days > 60:
        return "medium", "nobody", f"Customer not contacted for {days} days; a check-in is due."
    return "low", "nobody", "Customer relationship looks healthy."


def first_sentence(text: str) -> str:
    return text.split(". ")[0].rstrip(".") + "."


def days_between(a: date, b: date) -> int:
    return (b - a).days
