"""Turns database rows into API response models. Keeps routers free of mapping code."""

from datetime import date

from app.models import Customer, CustomerAnalysis, Interaction
from app.schemas import (
    AnalysisOut,
    ContactOut,
    CustomerDetailOut,
    CustomerSummaryOut,
    FollowUpOut,
    InteractionOut,
    Judgment,
    Narrative,
    SignalsOut,
)
from app.services.signals import compute_signals


def latest_analysis(customer: Customer) -> CustomerAnalysis | None:
    return customer.analyses[-1] if customer.analyses else None


def analysis_out(analysis: CustomerAnalysis) -> AnalysisOut:
    return AnalysisOut(
        created_at=analysis.created_at,
        trigger=analysis.trigger,
        judgment=Judgment.model_validate(analysis, from_attributes=True),
        narrative=Narrative.model_validate(analysis, from_attributes=True),
        judgment_provider=analysis.judgment_provider,
        generation_provider=analysis.generation_provider,
        model=analysis.model,
        latency_ms=analysis.latency_ms,
        fallback_used=analysis.fallback_used,
    )


def interaction_out(interaction: Interaction) -> InteractionOut:
    return InteractionOut(
        id=interaction.id,
        customer_id=interaction.customer_id,
        contact_id=interaction.contact_id,
        contact_name=interaction.contact.name if interaction.contact else None,
        type=interaction.type,
        occurred_at=interaction.occurred_at,
        notes=interaction.notes,
        ai_summary=interaction.ai_summary,
    )


def customer_summary_out(customer: Customer, today: date) -> CustomerSummaryOut:
    signals = compute_signals(customer.interactions, today)
    analysis = latest_analysis(customer)
    return CustomerSummaryOut(
        id=customer.id,
        name=customer.name,
        status=customer.status,
        follow_up=FollowUpOut(
            date=customer.follow_up_date,
            source=customer.follow_up_source,
            completed_at=customer.follow_up_completed_at,
        ),
        signals=SignalsOut(**signals.model_dump(include=set(SignalsOut.model_fields))),
        analysis=analysis_out(analysis) if analysis else None,
        contacts=[ContactOut.model_validate(c, from_attributes=True) for c in customer.contacts],
    )


def customer_detail_out(customer: Customer, today: date) -> CustomerDetailOut:
    summary = customer_summary_out(customer, today)
    newest_first = sorted(customer.interactions, key=lambda i: (i.occurred_at, i.id), reverse=True)
    return CustomerDetailOut(
        **summary.model_dump(),
        created_at=customer.created_at,
        interactions=[interaction_out(i) for i in newest_first],
        analysis_count=len(customer.analyses),
    )
