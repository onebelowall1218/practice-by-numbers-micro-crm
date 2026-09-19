# Code tour

One line per file: what it does and when you would touch it. Read this before opening the code.

## Backend (`backend/`)

| File | What it does | Touch it when |
| --- | --- | --- |
| `pyproject.toml` | Dependencies (uv), ruff and pytest settings | Adding a library |
| `app/main.py` | Creates the FastAPI app, creates tables, seeds, mounts routers and the built frontend | Adding a router |
| `app/config.py` | All settings read from env/.env (`Settings`) | Adding a configuration option |
| `app/clock.py` | `today()` honouring `CRM_TODAY` | Never, unless changing the demo clock |
| `app/db.py` | Engine, session factory, `get_session` dependency | Switching databases |
| `app/models.py` | SQLAlchemy tables: Customer, Contact, Interaction, CustomerAnalysis | Storing something new |
| `app/schemas.py` | Every Pydantic shape: AI domain models, LLM-facing models, API models | Changing what the API or AI returns |
| `app/seed.py` | CSV import (whitespace fix) and loading committed AI analyses | Changing the sample data |
| `app/routers/common.py` | `get_customer_or_404` | Adding shared router helpers |
| `app/routers/health.py` | `GET /api/health` | Exposing new runtime info |
| `app/routers/dashboard.py` | `GET /api/dashboard` | Changing the dashboard payload |
| `app/routers/customers.py` | List, detail, re-analyze, follow-up, draft message | Adding a customer action |
| `app/routers/interactions.py` | `POST /api/customers/{id}/interactions` | Changing how interactions are logged |
| `app/services/signals.py` | Facts from the timeline: days since last touch, counts, hint phrases | Adding a deterministic cue |
| `app/services/context.py` | Builds the `CustomerContext` JSON the AI reasons over | Giving the AI more information |
| `app/services/dashboard.py` | Bucket and sort rules (pure functions) | Changing ranking |
| `app/services/serializers.py` | ORM rows to API models | Changing response shapes |
| `app/services/ai/judgment.py` | `JudgmentProvider` protocol (typed decisions) | Adding a judgment field |
| `app/services/ai/generation.py` | `GenerationProvider` protocol (prose) and `AIProviderError` | Adding generated text |
| `app/services/ai/prompts.py` | System prompts and user-message builders | Tuning model behaviour |
| `app/services/ai/analyzer.py` | Orchestration: context, judgment, generation, guardrails, save | Changing the analysis flow or guardrails |
| `app/services/ai/factory.py` | Picks providers from settings | Adding a provider |
| `app/services/ai/providers/llm_base.py` | Shared LLM logic: one call serves both protocols, cache | Changing how LLM providers behave |
| `app/services/ai/providers/llm_common.py` | Loose LLM output to strict domain models | Changing conversion rules |
| `app/services/ai/providers/llm_anthropic.py` | Anthropic `messages.parse` call | Anthropic-specific settings |
| `app/services/ai/providers/llm_openai.py` | OpenAI `chat.completions.parse` call | OpenAI-specific settings |
| `app/services/ai/providers/rules.py` | Deterministic fallback provider | Changing fallback behaviour |
| `app/services/ai/providers/jev_typesafe.py` | Documented stub for a TypeSafe/Jev judgment provider | Integrating Jev |
| `data/customers.csv`, `contacts.csv`, `interactions.csv` | Sample data from the assignment | Never |
| `data/seed_analyses.json` | Committed Claude analyses for the 12 accounts | Run `make seed-ai` to regenerate |
| `scripts/__init__.py` | Sets safe env defaults before any script runs | Never |
| `scripts/common.py` | In-memory sample database for scripts | Never |
| `scripts/generate_seed_analyses.py` | Regenerates `seed_analyses.json` with the configured provider | After prompt changes |
| `scripts/eval.py` | Checks analyses against expectations, writes `docs/eval_results.md` | Adding an expectation |
| `tests/conftest.py` | Rules provider, demo date, temp database, test client | Never |
| `tests/test_signals.py` | Signal maths and hint detection | Changing signals |
| `tests/test_dashboard_rules.py` | Bucketing and sorting | Changing ranking |
| `tests/test_analyzer_guardrails.py` | Date clamp, evidence filtering, open-item cap | Changing guardrails |
| `tests/test_api.py` | End-to-end API behaviour with the rules provider | Changing endpoints |

## Frontend (`frontend/src/`)

| File | What it does | Touch it when |
| --- | --- | --- |
| `main.tsx` | React entry point | Never |
| `App.tsx` | Query client, router, top bar, toaster | Adding a page |
| `index.css` | Tailwind, shadcn theme, priority colours | Changing colours |
| `api/types.ts` | TypeScript mirror of `backend/app/schemas.py` | Whenever the API changes |
| `api/client.ts` | Fetch wrapper and endpoint functions | Adding an endpoint |
| `api/hooks.ts` | TanStack Query hooks; the only place components fetch | Adding data access |
| `lib/format.ts` | Date phrases ("Due tomorrow", "Last touch 3 days ago") | Changing wording |
| `lib/utils.ts` | shadcn `cn` helper | Never |
| `pages/Dashboard.tsx` | Buckets, filters, search | Changing the daily view |
| `pages/CustomerDetail.tsx` | Account page layout, wires panel, follow-up, timeline, dialogs | Changing the account page |
| `components/AttentionCard.tsx` | One dashboard row: who, why, next step, when | Changing card content |
| `components/AnalysisPanel.tsx` | AI summary, priority reason, next step, open items, evidence, provenance | Showing new AI fields |
| `components/EvidenceChips.tsx` | Chips linking AI output to interactions (hover highlight, click scroll) | Changing grounding UX |
| `components/Timeline.tsx` | Raw interaction history with AI summaries | Changing the timeline |
| `components/FollowUpControl.tsx` | Accept, change, mark done, reopen | Changing follow-up behaviour |
| `components/AddInteractionDialog.tsx` | Log a new interaction | Changing the form |
| `components/DraftMessageDialog.tsx` | Editable email draft with copy | Changing drafting UX |
| `components/PriorityBadge.tsx`, `StatusChip.tsx` | Small labelled badges | Changing labels |
| `components/DemoClockBanner.tsx` | Explains the pinned date | Never |
| `components/ProviderBadge.tsx` | Shows which AI provider is active | Never |
| `components/ui/*` | shadcn/ui primitives (generated) | Prefer not to edit |

## Root

| File | What it does |
| --- | --- |
| `Makefile` | `make install`, `dev`, `test`, `lint`, `eval`, `seed-ai`, `build`, `docker` |
| `Dockerfile`, `docker-compose.yml` | One image: builds the frontend, serves API and UI on :8000 |
| `.env.example` | Every setting with a comment |
***REMOVED_LINE***
***REMOVED_LINE***
