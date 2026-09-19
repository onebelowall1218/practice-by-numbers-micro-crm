"""Pydantic schemas: the single source of truth for every shape the API and AI layer use.

Three groups live here:
1. AI domain models (Judgment, Narrative, Draft) - strict, validated, stored in the database.
2. LLM-facing output models - deliberately plain (strings, enums, lists) because structured-output
   APIs support only a subset of JSON Schema. The analyzer converts them into the strict models.
3. API request/response models.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

Priority = Literal["high", "medium", "low"]
WaitingOn = Literal["us", "customer", "nobody"]
InteractionType = Literal["email", "call", "meeting", "note"]
CustomerStatus = Literal["prospect", "customer"]

# --------------------------------------------------------------------------------------------
# 1. AI domain models
# --------------------------------------------------------------------------------------------


class Judgment(BaseModel):
    """Typed decisions about a customer. This is the part a System One model like Jev could own."""

    priority: Priority
    needs_attention: bool
    waiting_on: WaitingOn
    urgency_score: float = Field(ge=0.0, le=1.0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class Narrative(BaseModel):
    """Generated text that explains the judgment and tells the user what to do."""

    relationship_summary: str
    interaction_summary: str | None = None
    priority_reason: str
    next_action: str
    suggested_follow_up_date: date
    follow_up_rationale: str
    open_items: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class Draft(BaseModel):
    subject: str
    body: str


# --------------------------------------------------------------------------------------------
# 2. LLM-facing output models (kept plain on purpose)
# --------------------------------------------------------------------------------------------


class LlmAnalysisOutput(BaseModel):
    priority: Priority = Field(description="high, medium or low")
    needs_attention: bool = Field(description="True if the user should act within the next week")
    waiting_on: WaitingOn = Field(
        description="'us' if the customer is waiting on the seller, 'customer' if the seller is "
        "waiting on the customer, 'nobody' if the relationship is stable"
    )
    urgency_score: float = Field(description="0.0 (no urgency) to 1.0 (act today)")
    relationship_summary: str = Field(description="2-4 plain sentences on where things stand")
    interaction_summary: str | None = Field(
        description="One sentence summarising the NEW interaction, or null if there is none"
    )
    priority_reason: str = Field(
        description="One sentence with the concrete fact behind the priority"
    )
    next_action: str = Field(description="One imperative sentence naming the contact to act with")
    suggested_follow_up_date: str = Field(description="YYYY-MM-DD, on or after today")
    follow_up_rationale: str = Field(description="Why that date")
    open_items: list[str] = Field(description="Up to 3 unanswered customer asks, or empty")
    evidence_ids: list[str] = Field(description="Interaction ids that support this analysis")


class LlmDraftOutput(BaseModel):
    subject: str
    body: str


# --------------------------------------------------------------------------------------------
# 3. API models
# --------------------------------------------------------------------------------------------


class ContactOut(BaseModel):
    id: str
    name: str
    email: str
    role: str


class InteractionOut(BaseModel):
    id: str
    customer_id: str
    contact_id: str | None
    contact_name: str | None
    type: InteractionType
    occurred_at: date
    notes: str
    ai_summary: str | None


class AnalysisOut(BaseModel):
    created_at: datetime
    trigger: str
    judgment: Judgment
    narrative: Narrative
    judgment_provider: str
    generation_provider: str
    model: str | None
    latency_ms: int | None
    fallback_used: bool


class SignalsOut(BaseModel):
    days_since_last_interaction: int | None
    last_interaction_type: InteractionType | None
    last_interaction_date: date | None
    interaction_count: int
    hints: list[str]


class FollowUpOut(BaseModel):
    date: date | None
    source: Literal["ai", "user"] | None
    completed_at: datetime | None


class CustomerSummaryOut(BaseModel):
    """One row on the dashboard or customer list."""

    id: str
    name: str
    status: CustomerStatus
    follow_up: FollowUpOut
    signals: SignalsOut
    analysis: AnalysisOut | None
    contacts: list[ContactOut]


class CustomerDetailOut(CustomerSummaryOut):
    created_at: date
    interactions: list[InteractionOut]
    analysis_count: int


BucketKey = Literal["overdue", "due_soon", "later", "done"]


class DashboardOut(BaseModel):
    as_of: date
    demo_clock: bool
    buckets: dict[BucketKey, list[CustomerSummaryOut]]


class HealthOut(BaseModel):
    status: Literal["ok"]
    as_of: date
    demo_clock: bool
    judgment_provider: str
    generation_provider: str
    model: str | None


class InteractionCreate(BaseModel):
    type: InteractionType
    contact_id: str | None = None
    occurred_at: date | None = None
    notes: str = Field(min_length=3, max_length=20_000)


class FollowUpUpdate(BaseModel):
    follow_up_date: date | None = None
    completed: bool | None = None
