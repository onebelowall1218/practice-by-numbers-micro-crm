"""Runs one analysis for a customer: context -> judgment -> narrative -> guardrails -> save.

This is the heart of the product. It is called when an interaction is added, when the user
asks for a re-analysis, and by the seed script. It never raises because of an AI failure:
the rule-based provider steps in and the result is marked fallback_used.
"""

import logging
from dataclasses import dataclass
from time import perf_counter

from sqlalchemy.orm import Session

from app.clock import today
from app.models import Customer, CustomerAnalysis, Interaction
from app.schemas import Judgment, Narrative
from app.services.ai.factory import get_providers
from app.services.ai.providers.rules import RulesProvider
from app.services.context import CustomerContext, build_context

log = logging.getLogger(__name__)

MAX_SUMMARY_CHARS = 1200
MAX_LINE_CHARS = 400


@dataclass
class AnalysisResult:
    judgment: Judgment
    narrative: Narrative
    judgment_provider: str
    generation_provider: str
    model: str | None
    latency_ms: int
    fallback_used: bool


def run_analysis(context: CustomerContext) -> AnalysisResult:
    """Pure AI step: no database access, so scripts and tests can call it directly."""
    judgment_provider, generation_provider = get_providers()
    started = perf_counter()
    try:
        judgment = judgment_provider.judge(context)
        narrative = generation_provider.narrate(context, judgment)
        result = AnalysisResult(
            judgment,
            narrative,
            judgment_provider.name,
            generation_provider.name,
            getattr(generation_provider, "model", None),
            0,
            False,
        )
    except Exception as error:  # noqa: BLE001 - any provider failure must degrade gracefully
        log.warning("AI provider failed for %s, using rules: %s", context.customer_id, error)
        rules = RulesProvider()
        judgment = rules.judge(context)
        narrative = rules.narrate(context, judgment)
        result = AnalysisResult(judgment, narrative, rules.name, rules.name, None, 0, True)
    result.latency_ms = int((perf_counter() - started) * 1000)
    result.narrative = apply_guardrails(result.narrative, context)
    return result


def apply_guardrails(narrative: Narrative, context: CustomerContext) -> Narrative:
    """Code-level checks on model output: dates in the past, unknown evidence ids, runaway text."""
    known_ids = context.interaction_ids()
    return narrative.model_copy(
        update={
            "suggested_follow_up_date": max(narrative.suggested_follow_up_date, context.today),
            "evidence_ids": [i for i in narrative.evidence_ids if i in known_ids],
            "relationship_summary": narrative.relationship_summary[:MAX_SUMMARY_CHARS],
            "priority_reason": narrative.priority_reason[:MAX_LINE_CHARS],
            "next_action": narrative.next_action[:MAX_LINE_CHARS],
            "open_items": [item[:MAX_LINE_CHARS] for item in narrative.open_items[:3]],
        }
    )


def analyze_customer(
    session: Session,
    customer: Customer,
    trigger: str,
    new_interaction: Interaction | None = None,
) -> CustomerAnalysis:
    """Analyse, persist the analysis, and refresh the customer's follow-up state."""
    context = build_context(customer, today(), new_interaction)
    result = run_analysis(context)
    analysis = save_analysis(session, customer, trigger, context, result)
    if new_interaction is not None and result.narrative.interaction_summary:
        new_interaction.ai_summary = result.narrative.interaction_summary
    # New information supersedes the previous schedule; the user can adjust it again afterwards.
    customer.follow_up_date = result.narrative.suggested_follow_up_date
    customer.follow_up_source = "ai"
    customer.follow_up_completed_at = None
    session.commit()
    return analysis


def save_analysis(
    session: Session,
    customer: Customer,
    trigger: str,
    context: CustomerContext,
    result: AnalysisResult,
) -> CustomerAnalysis:
    analysis = CustomerAnalysis(
        customer_id=customer.id,
        trigger=trigger,
        **result.judgment.model_dump(),
        **result.narrative.model_dump(exclude={"interaction_summary"}),
        signals_snapshot=context.signals.model_dump(mode="json"),
        judgment_provider=result.judgment_provider,
        generation_provider=result.generation_provider,
        model=result.model,
        latency_ms=result.latency_ms,
        fallback_used=result.fallback_used,
    )
    session.add(analysis)
    return analysis
