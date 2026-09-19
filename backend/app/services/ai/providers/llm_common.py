"""Shared conversion from the loose LLM output into strict domain models.

Both language-model providers make one structured call that returns judgment and narrative
together (one round trip). They cache that result so judge() and narrate() do not call twice.
"""

from datetime import date

from app.schemas import Judgment, LlmAnalysisOutput, Narrative


def to_judgment(output: LlmAnalysisOutput) -> Judgment:
    return Judgment(
        priority=output.priority,
        needs_attention=output.needs_attention,
        waiting_on=output.waiting_on,
        urgency_score=min(max(output.urgency_score, 0.0), 1.0),
        confidence=None,
    )


def to_narrative(output: LlmAnalysisOutput, today: date) -> Narrative:
    return Narrative(
        relationship_summary=output.relationship_summary,
        interaction_summary=output.interaction_summary or None,
        priority_reason=output.priority_reason,
        next_action=output.next_action,
        suggested_follow_up_date=parse_date(output.suggested_follow_up_date, today),
        follow_up_rationale=output.follow_up_rationale,
        open_items=output.open_items[:3],
        evidence_ids=output.evidence_ids,
    )


def parse_date(value: str, fallback: date) -> date:
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return fallback
