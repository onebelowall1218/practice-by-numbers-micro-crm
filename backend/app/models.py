"""SQLAlchemy models. Raw interaction notes are never overwritten; AI output lives beside them."""

from datetime import UTC, date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    """Naive UTC timestamp; SQLite has no timezone type, so the app stores UTC everywhere."""
    return datetime.now(UTC).replace(tzinfo=None)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # prospect | customer
    created_at: Mapped[date] = mapped_column(Date, nullable=False)

    # The follow-up the user is working from. AI suggestions are copied here until the user
    # accepts or changes the date, after which follow_up_source becomes "user".
    follow_up_date: Mapped[date | None] = mapped_column(Date)
    follow_up_source: Mapped[str | None] = mapped_column(String)  # ai | user
    follow_up_completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    contacts: Mapped[list["Contact"]] = relationship(back_populates="customer")
    interactions: Mapped[list["Interaction"]] = relationship(
        back_populates="customer", order_by="Interaction.occurred_at"
    )
    analyses: Mapped[list["CustomerAnalysis"]] = relationship(
        back_populates="customer", order_by="CustomerAnalysis.created_at"
    )


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)

    customer: Mapped[Customer] = relationship(back_populates="contacts")


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), nullable=False)
    contact_id: Mapped[str | None] = mapped_column(ForeignKey("contacts.id"))
    type: Mapped[str] = mapped_column(String, nullable=False)  # email | call | meeting | note
    occurred_at: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    customer: Mapped[Customer] = relationship(back_populates="interactions")
    contact: Mapped[Contact | None] = relationship()


class CustomerAnalysis(Base):
    """One AI analysis run. Rows are append-only; the newest row is the customer's current state."""

    __tablename__ = "customer_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    trigger: Mapped[str] = mapped_column(String, nullable=False)  # seed | new_interaction | manual

    # Judgment (typed decisions)
    priority: Mapped[str] = mapped_column(String, nullable=False)
    needs_attention: Mapped[bool] = mapped_column(Boolean, nullable=False)
    waiting_on: Mapped[str] = mapped_column(String, nullable=False)  # us | customer | nobody
    urgency_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)

    # Narrative (generated text)
    relationship_summary: Mapped[str] = mapped_column(Text, nullable=False)
    priority_reason: Mapped[str] = mapped_column(Text, nullable=False)
    next_action: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_follow_up_date: Mapped[date] = mapped_column(Date, nullable=False)
    follow_up_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    open_items: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # Provenance, so every recommendation can be traced and costed
    signals_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    judgment_provider: Mapped[str] = mapped_column(String, nullable=False)
    generation_provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str | None] = mapped_column(String)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    customer: Mapped[Customer] = relationship(back_populates="analyses")
