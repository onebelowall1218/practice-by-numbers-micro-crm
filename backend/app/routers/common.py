"""Shared router helpers."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Customer


def get_customer_or_404(session: Session, customer_id: str) -> Customer:
    customer = session.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return customer
