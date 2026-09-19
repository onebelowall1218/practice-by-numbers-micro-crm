# Design decisions

Each decision states the choice, the alternatives considered, and the reasoning behind it.
Read top to bottom in ten minutes; each entry stands alone.

## Product decisions

### 1. The dashboard is a ranked to-do list, not a table

**Choice.** The home screen groups accounts into Overdue, Due this week, Later and Done, sorted by
priority and follow-up date. Each card shows the reason and the next step.

**Alternatives.** A sortable customer table with a priority column; a chat box over the data.

**Why.** The brief says "minimal manual effort" and "understand who may need attention". A table
still makes the user scan and decide. A chat box makes them type. A ranked list answers the
question before they ask it.

### 2. Every AI statement is grounded in the raw timeline

**Choice.** The AI returns `evidence_ids`; the UI renders them as chips that highlight the exact
interactions. Raw notes are never replaced by summaries and are always on the same page.

**Alternatives.** Show only the summary; hide history behind a tab.

**Why.** A salesperson will not trust a recommendation they cannot check in two seconds. Evidence
chips make verification a hover, not an investigation. It also gives an honest signal when the
model is wrong.

### 3. Two levels of summary: the interaction and the relationship

**Choice.** A new interaction gets a one-line summary; the customer gets a rolling relationship
summary that is regenerated on each new interaction.

**Why.** The two answer different questions: "what happened in that call?" versus "where do we
stand?". Keeping both avoids re-reading the history and avoids a summary that only reflects the
latest event.

### 4. The AI proposes, the user decides

**Choice.** The follow-up date is suggested by the AI, but the user can accept, change, or mark it
done. A new interaction resets the schedule because new information supersedes an old plan.

**Why.** Recommendations are only useful if the user stays in control. The model suggests; the
person commits.

### 5. Draft the email, do not send it

**Choice.** "Draft follow-up" produces an editable subject and body and a Copy button. Nothing is
sent and nothing is stored.

**Why.** Sending on the user's behalf needs mail integration, consent and undo. Drafting captures
most of the value in a fraction of the scope and keeps the human in the loop.

### 6. Single user, no authentication

**Choice.** One implicit user. No login, roles or organisations.

**Why.** The exercise is about the core experience in 4 to 6 hours. Authentication adds time and
hides the product behind a login form. The README lists the production path (an auth provider,
`owner_id` on every table, per-request scoping).

## Technical decisions

### 7. Judgment and generation are separate layers

**Choice.** `JudgmentProvider` returns typed decisions (priority, needs attention, waiting on,
urgency, confidence). `GenerationProvider` writes the words. The analyzer always calls judgment
first and hands the result to generation.

**Alternatives.** One prompt that returns everything; keep it as a single opaque call.

**Why.** Typed decisions and prose have different quality bars, different evaluation methods, and
potentially different models. A "System One" model such as TypeSafe's Jev returns typed judgments
with calibrated probabilities and could own the judgment layer without touching the UI, API, or
storage. Both protocols are implemented by the same language model in one round trip by default,
so the split costs nothing in latency when unused.

**This is not hypothetical.** `providers/jev_typesafe.py` implements `JudgmentProvider` against
the real TypeSafe SDK; set `JUDGMENT_PROVIDER=jev` and `TYPESAFE_API_KEY` and priority/waiting_on/
urgency come from Jev while the LLM still writes the summary, next action and draft — no other
file changes. `scripts/compare_judgment.py` runs both on the 12 seed accounts; one real run
against `claude-opus-5` agreed on priority for 10/12 accounts and waiting_on for 11/12 (details in
`docs/AI_DESIGN.md`). It is off by default so the app still runs with zero keys.

### 8. Deterministic signals feed the model and guard its output

**Choice.** `signals.py` computes facts in code (days since last touch, counts, keyword cues such as
"do not push"). They go into the prompt and are stored with each analysis. `apply_guardrails`
clamps past dates, drops unknown evidence ids, and caps text length.

**Why.** Cheap facts should not be re-derived by a language model. Guardrails turn "the model
usually behaves" into "the app always behaves".

### 9. Structured outputs with a deliberately plain LLM schema

**Choice.** The model fills `LlmAnalysisOutput` (strings, enums, lists, no formats or numeric
bounds). Code converts it into strict `Judgment` and `Narrative` models with real dates and ranges.

**Why.** Structured-output APIs support only a subset of JSON Schema. Keeping the model-facing
schema plain avoids provider-specific failures; keeping the domain schema strict protects the app.

### 10. AI runs on write, never on read

**Choice.** Analysis happens when an interaction is added, when the user clicks Re-analyze, or in
the seed script. Dashboards and detail pages read stored results.

**Why.** Reads are frequent and must be instant and free. Writes are rare and can afford several
seconds. The `customer_analyses` table stores every run with provider, model and latency, so cost
and quality can be audited later.

### 11. Provider abstraction with a rule-based fallback

**Choice.** Anthropic, OpenAI and a rule-based provider implement the same protocols. A factory
picks one from environment variables. Any provider failure degrades to rules and flags
`fallback_used`.

**Why.** The evaluator may have no API key; the demo must still run. In production, a model outage
must never take the CRM down.

### 12. Pre-computed seed analyses are committed

**Choice.** `data/seed_analyses.json` holds real Claude output for the 12 sample accounts and loads
on first start.

**Why.** The first impression is instant and costs nothing. It also freezes a known-good baseline
for the eval script.

### 13. An eval script, not just vibes

**Choice.** `scripts/eval.py` checks all 12 accounts against expected priorities and universal
rules (date not in the past, evidence ids real, next action names a real contact).

**Why.** Two expectations were initially wrong (Greenfield, BrightSmile). Reading the model's
stated reasons showed it was applying the rubric more consistently than the author; the
expectations were corrected and the disagreement is documented in `docs/AI_DESIGN.md`. That
loop, expectations, run, read, adjust, is how prompt quality is managed at scale.

### 14. SQLite via SQLAlchemy

**Choice.** A SQLite file, SQLAlchemy 2.0 models, Postgres-compatible types.

**Why.** Zero setup for the evaluator; a one-line `DATABASE_URL` change moves to Postgres. The
data volume in this exercise does not justify a database server.

### 15. Synchronous analysis on save

**Choice.** `POST /interactions` saves the raw note, runs the analysis, and returns the updated
customer in one request (5 to 12 seconds with Claude Opus 5; the UI shows an "Analyzing" state).

**Alternatives.** Return 202 and poll; background job queue.

**Why.** Simplest correct behaviour for one user. The raw note is committed before the model runs,
so a failure never loses data. The production path is a job queue with a status field.

### 16. A demo clock

**Choice.** `CRM_TODAY` pins "today" (default 2026-09-01 in the examples). The UI shows a banner
when it is set.

**Why.** The sample data ends on 31 August 2026. Without a pinned date every account looks stale
and the dashboard tells the wrong story. Being explicit about it is more honest than editing the
data.

### 17. No vector database, no retrieval framework

**Choice.** Each analysis receives the whole account: customer, contacts, ordered timeline,
signals. Plain SQL, plain JSON.

**Why.** Twelve accounts and 56 interactions fit in one prompt many times over. Retrieval
infrastructure would add moving parts without adding accuracy. The README notes when that
changes (thousands of interactions per account, or cross-account questions).
