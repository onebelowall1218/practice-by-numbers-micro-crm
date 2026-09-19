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
(see "Jev (TypeSafe System One) as an optional judgment provider" below).

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

## Jev (TypeSafe System One) as an optional judgment provider

Jev answers narrow typed questions with calibrated probabilities instead of writing prose. That
is exactly the `JudgmentProvider` contract, so `providers/jev_typesafe.py` implements it for
real: judgment can come from Jev while generation (the summary, next action, draft) stays on the
language model, unchanged.

### How to turn it on

Set two environment variables (see `.env.example`):

```
TYPESAFE_API_KEY=...
JUDGMENT_PROVIDER=jev
```

`LLM_PROVIDER` is untouched — it still picks the generation provider (anthropic/openai/rules) the
same way it always did. Nothing else changes: `/api/health` reports `judgment_provider: "jev"`,
and each analysis's provenance line shows which provider actually judged it.

This is opt-in, not the default, so the app still runs with zero keys and the committed
`data/seed_analyses.json` (generated with the LLM judging itself) stays valid — `make eval`
passes without a TypeSafe key.

### The mapping onto `Judgment`

| Judgment field | TypeSafe primitive | Question |
| --- | --- | --- |
| `priority` | Choice (high, medium, low) | "Given this account's interaction history and signals, how urgently should the salesperson act on it?" |
| `waiting_on` | Choice (us, customer, nobody) | "Who owes the next move in this relationship?" |
| `needs_attention` | Noul | "Should the salesperson act on this account within the next 7 days?" (true when the probability is ≥ 0.5) |
| `urgency_score` | Score, 4 ordered levels ("no urgency" → "act today") | Normalised from the returned position (0..3) into 0..1 |
| `confidence` | — | The `priority` Choice's own `.confidence` |

The `priority` and `waiting_on` Choice criteria are not hand-duplicated: both the language model's
system prompt and Jev's criteria are built from the same two dictionaries,
`PRIORITY_CRITERIA` and `WAITING_ON_CRITERIA` in `prompts.py`, so the two providers are judging
against one rubric, not two that can drift apart.

Jev receives the same `CustomerContext` JSON the language model gets (`context.model_dump(mode="json")`
as the `state` argument to `client.system_one(...)`) — TypeSafe recommends named-field state, which
is exactly why `CustomerContext` is a Pydantic model rather than a prose blob.

### What I confirmed against the real SDK (not assumed)

- Package: `typesafe-sdk`. Client: `typesafe_sdk.TypeSafeClient(api_key=...)`. One call answers a
  batch of questions: `client.system_one(state=..., questions={...})`, returning a
  `SystemOneResponse` with `.choices["name"]`, `.nouls["name"]`, `.scores["name"]` accessors.
- `Choice(instructions=..., criteria={...})` — criteria values are short description strings.
  `Noul(instructions=...)` — no criteria, returns a 0..1 probability. `Score(instructions=...,
  criteria=[...ordered levels...])` — returns a probability-weighted position across the list.
- Errors (`TypeSafeError` and its subclasses, e.g. `TypeSafeAuthenticationError`,
  `TypeSafeRateLimitError`) are wrapped into the same `AIProviderError` every other provider
  raises, so `analyzer.run_analysis`'s existing fallback-to-rules path covers Jev with no changes
  to `analyzer.py`.

### Comparing Jev against the LLM

`scripts/compare_judgment.py` runs both providers on the same 12 seed accounts (same
`CustomerContext`, so it's a fair comparison) and prints where `priority` and `waiting_on` agree.
One real run against `claude-opus-5`:

```
Priority agreement:   10/12
Waiting-on agreement: 11/12
```

(Re-running the script will not reproduce this exact table — the LLM side is not perfectly
deterministic between separate calls, so a given account can shift by one priority level run to
run; Jev's answers are far more stable since they're calibrated probabilities, not generated text.)

The recurring disagreement is Northstar Dental Group and Greenfield Pediatrics: Jev tends to call
these "medium" where the LLM says "high," with `waiting_on` still agreeing on "us" in both cases —
a real difference of judgment on how much a same-week unanswered question should raise priority,
not an error on either side. This kind of run is the natural first step toward the
"verify and escalate" pattern: route low-`confidence` Jev calls (see Maple Grove Orthodontics at
0.38 above) to the language model for a second opinion instead of trusting either provider blindly.
That escalation logic is not built — the comparison script is the evidence for whether it would be
worth building, which is the honest way to justify adding it later rather than assuming it helps.

### Latency and cost: Jev vs an LLM, judgment alone

`scripts/benchmark_judgment.py` isolates the judgment step on both sides — Jev's four questions
versus a *separate*, narrower LLM call that returns only `priority`/`waiting_on`/`needs_attention`/
`urgency_score` (not the full narrative the app normally asks for in the same request). That makes
it a fair like-for-like comparison of "get a judgment," not a comparison against the app's actual
default call, which gets judgment and narrative together for one price. One real run, `claude-sonnet-5`
against the same 12 seed accounts:

| | Jev | claude-sonnet-5 |
| --- | --- | --- |
| Average latency | **484 ms** | **2,081 ms** |
| Cost per judgment | not published by TypeSafe | **$0.00357** |
| Total for 12 judgments | — | $0.04287 |

Full per-account numbers in [docs/judgment_benchmark.md](judgment_benchmark.md). Two honest
caveats:

1. **Jev has no public dollar price as of this writing.** Only token counts and latency are
   reported for it; a cost line was not invented. If TypeSafe publishes per-token pricing later,
   `SONNET_5_PRICE_PER_MTOK` in the script has the pattern to extend.
2. **This is not the cost of enabling Jev in the app.** With `JUDGMENT_PROVIDER` unset (the
   default), the LLM's judgment is a byproduct of the narrative call it makes anyway — it costs
   nothing extra. This benchmark answers a narrower, useful question instead: if you needed
   *only* a judgment and had to choose how to get it, Jev is roughly 4× faster than asking an LLM
   for the same narrow answer. That's the concrete case for a typed "System One" model over a
   generative one when generation isn't needed — speed and (once priced) likely cost, not quality;
   the agreement-rate results above are the evidence on quality.
