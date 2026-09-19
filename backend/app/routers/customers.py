from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clock import today
from app.db import get_session
from app.models import Customer, utc_now
from app.routers.common import get_customer_or_404
from app.schemas import CustomerDetailOut, CustomerSummaryOut, Draft, FollowUpUpdate, Narrative
from app.services.ai.analyzer import analyze_customer
from app.services.ai.factory import get_providers
from app.services.context import build_context
from app.services.serializers import customer_detail_out, customer_summary_out, latest_analysis

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("", response_model=list[CustomerSummaryOut])
def list_customers(session: Session = Depends(get_session)) -> list[CustomerSummaryOut]:
    customers = session.scalars(select(Customer).order_by(Customer.name)).all()
    return [customer_summary_out(c, today()) for c in customers]


@router.get("/{customer_id}", response_model=CustomerDetailOut)
def get_customer(customer_id: str, session: Session = Depends(get_session)) -> CustomerDetailOut:
    return customer_detail_out(get_customer_or_404(session, customer_id), today())


@router.post("/{customer_id}/analyze", response_model=CustomerDetailOut)
def reanalyze(customer_id: str, session: Session = Depends(get_session)) -> CustomerDetailOut:
    customer = get_customer_or_404(session, customer_id)
    analyze_customer(session, customer, trigger="manual")
    session.refresh(customer)
    return customer_detail_out(customer, today())


@router.patch("/{customer_id}/follow-up", response_model=CustomerDetailOut)
def update_follow_up(
    customer_id: str, update: FollowUpUpdate, session: Session = Depends(get_session)
) -> CustomerDetailOut:
    customer = get_customer_or_404(session, customer_id)
    if update.follow_up_date is not None:
        customer.follow_up_date = update.follow_up_date
        customer.follow_up_source = "user"
        customer.follow_up_completed_at = None
    if update.completed is not None:
        customer.follow_up_completed_at = utc_now() if update.completed else None
    session.commit()
    session.refresh(customer)
    return customer_detail_out(customer, today())


@router.post("/{customer_id}/draft-message", response_model=Draft)
def draft_message(customer_id: str, session: Session = Depends(get_session)) -> Draft:
    customer = get_customer_or_404(session, customer_id)
    analysis = latest_analysis(customer)
    context = build_context(customer, today())
    if analysis is None:
        analyze_customer(session, customer, trigger="manual")
        analysis = latest_analysis(customer)
    narrative = Narrative.model_validate(analysis, from_attributes=True)
    _, generation = get_providers()
    return generation.draft_message(context, narrative)
