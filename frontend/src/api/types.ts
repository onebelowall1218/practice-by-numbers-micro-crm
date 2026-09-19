// Mirrors backend/app/schemas.py. Keep the two files in sync when the API changes.

export type Priority = "high" | "medium" | "low";
export type WaitingOn = "us" | "customer" | "nobody";
export type InteractionType = "email" | "call" | "meeting" | "note";
export type CustomerStatus = "prospect" | "customer";
export type BucketKey = "overdue" | "due_soon" | "later" | "done";

export interface Judgment {
  priority: Priority;
  needs_attention: boolean;
  waiting_on: WaitingOn;
  urgency_score: number;
  confidence: number | null;
}

export interface Narrative {
  relationship_summary: string;
  interaction_summary: string | null;
  priority_reason: string;
  next_action: string;
  suggested_follow_up_date: string;
  follow_up_rationale: string;
  open_items: string[];
  evidence_ids: string[];
}

export interface Analysis {
  created_at: string;
  trigger: "seed" | "new_interaction" | "manual";
  judgment: Judgment;
  narrative: Narrative;
  judgment_provider: string;
  generation_provider: string;
  model: string | null;
  latency_ms: number | null;
  fallback_used: boolean;
}

export interface Contact {
  id: string;
  name: string;
  email: string;
  role: string;
}

export interface Interaction {
  id: string;
  customer_id: string;
  contact_id: string | null;
  contact_name: string | null;
  type: InteractionType;
  occurred_at: string;
  notes: string;
  ai_summary: string | null;
}

export interface Signals {
  days_since_last_interaction: number | null;
  last_interaction_type: InteractionType | null;
  last_interaction_date: string | null;
  interaction_count: number;
  hints: string[];
}

export interface FollowUp {
  date: string | null;
  source: "ai" | "user" | null;
  completed_at: string | null;
}

export interface CustomerSummary {
  id: string;
  name: string;
  status: CustomerStatus;
  follow_up: FollowUp;
  signals: Signals;
  analysis: Analysis | null;
  contacts: Contact[];
}

export interface CustomerDetail extends CustomerSummary {
  created_at: string;
  interactions: Interaction[];
  analysis_count: number;
}

export interface Dashboard {
  as_of: string;
  demo_clock: boolean;
  buckets: Record<BucketKey, CustomerSummary[]>;
}

export interface Health {
  status: "ok";
  as_of: string;
  demo_clock: boolean;
  judgment_provider: string;
  generation_provider: string;
  model: string | null;
}

export interface InteractionCreate {
  type: InteractionType;
  contact_id: string | null;
  occurred_at: string | null;
  notes: string;
}

export interface FollowUpUpdate {
  follow_up_date?: string;
  completed?: boolean;
}

export interface Draft {
  subject: string;
  body: string;
}
