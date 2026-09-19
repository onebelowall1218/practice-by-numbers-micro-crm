from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.clock import today
from app.db import get_session
from app.models import Contact, Interaction
from app.routers.common import get_customer_or_404
from app.schemas import CustomerDetailOut, InteractionCreate
from app.services.ai.analyzer import analyze_customer
from app.services.serializers import customer_detail_out

router = APIRouter(prefix="/api/customers", tags=["interactions"])


@router.post("/{customer_id}/interactions", response_model=CustomerDetailOut, status_code=201)
def add_interaction(
    customer_id: str, payload: InteractionCreate, session: Session = Depends(get_session)
) -> CustomerDetailOut:
    """Save the raw interaction first, then let the AI update the customer's state."""
    customer = get_customer_or_404(session, customer_id)
    if payload.contact_id is not None:
        contact = session.get(Contact, payload.contact_id)
        if contact is None or contact.customer_id != customer.id:
            raise HTTPException(status_code=400, detail="Contact does not belong to this customer")
    interaction = Interaction(
        id=f"int_{uuid4().hex[:10]}",
        customer_id=customer.id,
        contact_id=payload.contact_id,
        type=payload.type,
        occurred_at=payload.occurred_at or today(),
        notes=" ".join(payload.notes.split()),
    )
    session.add(interaction)
    session.commit()
    session.refresh(customer)

    analyze_customer(session, customer, trigger="new_interaction", new_interaction=interaction)
    session.refresh(customer)
    return customer_detail_out(customer, today())
