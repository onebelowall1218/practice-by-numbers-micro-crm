# AI design

How the AI layer works, what it is allowed to decide, how it is kept honest, and how it grows.
Code lives in `backend/app/services/ai/`.

## The job of the AI

Turn one account's raw history into four things the salesperson needs:

| Output | Type | Owner |
| --- | --- | --- |
| Where things stand (relationship summary) | prose | generation |
| Whether it needs attention and how urgently (priority, waiting_on, urgency) | typed decision | judgment |
| What to do next (next action, open items) | prose | generation |
| When (suggested follow-up date and why) | date + prose | generation |

## Two protocols, one round trip

```
CustomerContext ──> JudgmentProvider.judge() ──> Judgment
                                                   │
CustomerContext + Judgment ──> GenerationProvider.narrate() ──> Narrative
```

- `judgment.py` defines `JudgmentProvider`. It returns `Judgment` (priority, needs_attention,
  waiting_on, urgency_score, optional confidence).
- `generation.py` defines `GenerationProvider`. It returns `Narrative` and, separately, `Draft`.
- `providers/llm_base.py` implements both with one structured API call and a small per-context
  cache, so the default path is a single request (5 to 12 seconds on Claude Opus 5).
- `providers/rules.py` implements both with plain rules. It is the fallback and the test double.
- `factory.py` reads `LLM_PROVIDER` and optional `JUDGMENT_PROVIDER` and wires the pair.
- `analyzer.py` runs judgment, then generation, then guardrails, then saves.

Why split them if one call does both today? Because typed decisions and prose have different
quality bars and evaluation methods, and because a dedicated judgment model can slot in later
(see "Extending with Jev").

## What the model sees

`context.py` builds a JSON bundle. No retrieval system is involved; the whole account fits.

```json
{
  "today": "2026-09-01",
  "customer_id": "cust_011",
  "customer_name": "Evergreen Dental Partners",
  "status": "prospect",
  "relationship_started": "2026-07-02",
  "contacts": [{ "id": "contact_012", "name": "Brian Chen", "role": "Owner", "email": "..." }],
  "timeline": [{ "id": "int_045", "date": "2026-07-02", "type": "email", "contact_name": "Brian Chen", "notes": "..." }],
  "signals": {
    "days_since_last_interaction": 18,
    "last_interaction_type": "note",
    "interaction_count": 6,
    "counts_by_type": { "email": 2, "call": 2, "meeting": 1, "note": 1 },
    "hints": ["A note asks not to push the customer before a stated time."]
  },
  "new_interaction_id": null,
  "user_follow_up_date": null
}
```

`signals.py` computes the facts in code. The `hints` list comes from a short table of phrases
("do not push", "no response", "never scheduled", ...) applied to the last three interactions only,
so stale cues do not linger.

## The prompt

`prompts.py`, system prompt for analysis (abridged; the file is the source of truth):

> You are the relationship assistant inside a small CRM used by a salesperson at a dental-technology
> company. The company sells an AI phone-answering and front-desk assistant to dental practices...
> Use only facts present in the timeline. Never invent conversations, dates or commitments.
> Respect the customer's stated timing... Priority means: high = the customer is waiting on us, or a
> time-sensitive opportunity or risk exists; medium = we should nudge or check in soon; low = healthy,
> resolved, or deliberately waiting... next_action is one imperative sentence that names the contact...
> suggested_follow_up_date must be on or after today... evidence_ids lists the interaction ids that
> most support the priority and next action.

The user message states today's date, whether a new interaction was just recorded (and its id),
and the JSON bundle.

## Structured output, in two layers

The model fills `LlmAnalysisOutput` (in `schemas.py`): strings, enums, lists, and a date as a
plain `YYYY-MM-DD` string. No numeric bounds, no format keywords, because structured-output APIs
accept only a subset of JSON Schema and the two providers differ.

Code then converts it to strict domain models (`Judgment`, `Narrative`) with real `date` fields
and `0..1` bounds. Anthropic uses `client.messages.parse(..., output_format=...)`; OpenAI uses
`client.chat.completions.parse(..., response_format=...)`. Both check for refusals and raise
`AIProviderError` on anything unusable.

## Guardrails (code, not prompt)

`analyzer.apply_guardrails`:

| Check | Action |
| --- | --- |
| Follow-up date before today | Clamp to today |
| Evidence id not in this customer's timeline | Drop it |
| More than three open items | Keep three |
| Over-long text | Truncate (1200 chars summary, 400 chars lines) |
| Any provider exception, refusal or parse failure | Use `RulesProvider`, set `fallback_used=True` |

The UI shows "Rule-based analysis" when the fallback ran, so nobody mistakes a rule for a model.

## Provenance

Every run is a row in `customer_analyses`: trigger (seed, new_interaction, manual), judgment
fields, narrative fields, the signals snapshot, judgment and generation provider names, model,
latency in milliseconds, and the fallback flag. History is never overwritten; the newest row is the
customer's current state.

## Evaluation

`python -m scripts.eval` checks the committed analyses for the 12 sample accounts. Universal
rules: follow-up not in the past, evidence ids real, next action names a real contact, summary at
most four sentences. Per-account expectations are in `scripts/eval.py`; results are written to
`docs/eval_results.md`.

Two expectations changed after the first run:

- **Greenfield Pediatrics** was expected `medium|low` (a happy customer). The model said `high`
  because Emily's question about SMS support had gone unanswered for six days, which is exactly
  the "customer is waiting on us" rule in the prompt. The model was right by the rubric; the
  expectation now allows `high|medium`.
- **BrightSmile Dental** was expected `medium|low`. The model said `high` because Rachel said she
  would decide "in September" and September had just started. Debatable, but defensible as a
  time-sensitive opportunity. The expectation now allows `medium|high`.

Strict expectations were kept where the data is unambiguous: Northstar, Parkview and Central
Avenue must be `high`; Oak & Pine and Maple Grove must be `low`; Evergreen must not be `high` and
its follow-up must fall after 10 September because the customer asked not to be pushed.

Measured on 2026-09-19 with `claude-opus-5`: 12/12 pass, average latency about 7.3 seconds per
account, roughly 2,500 input tokens and 400 output tokens per analysis.

## Cost and latency

| Event | Model calls | Typical latency |
| --- | --- | --- |
| Open dashboard or customer | 0 | instant |
| Add interaction | 1 | 5 to 12 s (Opus 5), faster on Sonnet 5 |
| Draft follow-up | 1 | 3 to 8 s |
| Re-analyze | 1 | 5 to 12 s |
| First start with committed seed | 0 | instant |

Set `LLM_MODEL=claude-sonnet-5` for a cheaper, faster option with the same schema.

## Extending with Jev (TypeSafe System One)

Jev answers narrow typed questions with calibrated probabilities instead of writing prose. That is
the `JudgmentProvider` contract. The stub in `providers/jev_typesafe.py` documents the mapping:

| Judgment field | TypeSafe primitive | Question |
| --- | --- | --- |
| `priority` | Choice (high, medium, low) | "Given this account's timeline, how urgently should the salesperson act?" |
| `waiting_on` | Choice (us, customer, nobody) | "Who owes the next move?" |
| `needs_attention` | Noul | "Should the salesperson act on this account within 7 days?" |
| `urgency_score` | Score | Ordered levels from "no urgency" to "act today" |

The state Jev receives is the same `CustomerContext` JSON shown above; TypeSafe recommends
named-field state, which is why the context is a Pydantic model rather than a prose blob.

Steps to wire it in:

1. Implement `JevJudgmentProvider.judge()` using the TypeSafe SDK; fill `Judgment.confidence` from
   the returned probabilities.
2. Add `"jev"` to `ProviderName` in `config.py` and a branch in `factory.build_provider`.
3. Set `JUDGMENT_PROVIDER=jev`. Generation stays on the language model, which receives the
   judgment and explains it (`prompts.judgment_hint`).
4. Optional: in `analyzer.run_analysis`, route accounts with low `confidence` to the language
   model's own judgment as a second opinion (TypeSafe's "verify and escalate" pattern).

Nothing in the API, storage or UI changes.
