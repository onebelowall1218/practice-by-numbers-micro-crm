"""Builds the context bundle the AI reasons over: customer, contacts, timeline and signals.

The dataset is small and relational, so this replaces any retrieval system. The same bundle
is what a TypeSafe/Jev judgment would receive as named-field state.
"""

from datetime import date

from pydantic import BaseModel

from app.models import Customer, Interaction
from app.services.signals import Signals, compute_signals


class ContactContext(BaseModel):
    id: str
    name: str
    role: str
    email: str


class TimelineEntry(BaseModel):
    id: str
    date: date
    type: str
    contact_name: str | None
    notes: str


class CustomerContext(BaseModel):
    today: date
    customer_id: str
    customer_name: str
    status: str
    relationship_started: date
    contacts: list[ContactContext]
    timeline: list[TimelineEntry]  # oldest first
    signals: Signals
    new_interaction_id: str | None = None
    user_follow_up_date: date | None = None

    @property
    def new_interaction(self) -> TimelineEntry | None:
        return next((e for e in self.timeline if e.id == self.new_interaction_id), None)

    def contact_names(self) -> list[str]:
        return [c.name for c in self.contacts]

    def interaction_ids(self) -> set[str]:
        return {e.id for e in self.timeline}


def build_context(
    customer: Customer, today: date, new_interaction: Interaction | None = None
) -> CustomerContext:
    interactions = sorted(customer.interactions, key=lambda i: (i.occurred_at, i.id))
    return CustomerContext(
        today=today,
        customer_id=customer.id,
        customer_name=customer.name,
        status=customer.status,
        relationship_started=customer.created_at,
        contacts=[
            ContactContext(id=c.id, name=c.name, role=c.role, email=c.email)
            for c in customer.contacts
        ],
        timeline=[
            TimelineEntry(
                id=i.id,
                date=i.occurred_at,
                type=i.type,
                contact_name=i.contact.name if i.contact else None,
                notes=i.notes,
            )
            for i in interactions
        ],
        signals=compute_signals(interactions, today),
        new_interaction_id=new_interaction.id if new_interaction else None,
        user_follow_up_date=(
            customer.follow_up_date if customer.follow_up_source == "user" else None
        ),
    )
