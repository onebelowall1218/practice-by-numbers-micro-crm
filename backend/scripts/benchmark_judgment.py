"""Measures latency and (where priced) cost for Jev vs an LLM doing the judgment step alone.

This isolates judgment from generation on both sides, for a fair comparison:
- Jev: client.system_one() answering only the four judgment questions (its only job).
- LLM: a separate structured-output call asking ONLY for judgment fields, built from the same
  PRIORITY_CRITERIA/WAITING_ON_CRITERIA rubric as Jev and the main analysis prompt, so neither
  side is being asked an easier or harder question. This is deliberately NOT the app's normal
  analysis call (which asks the LLM for judgment and the full narrative together in one request);
  see docs/AI_DESIGN.md for why that's the right default and why this benchmark asks a narrower
  question instead.

Pricing: Anthropic publishes per-token pricing, so a dollar cost is computed for the LLM side.
TypeSafe does not publish public per-token or per-call pricing as of this writing, so only token
counts and latency are reported for Jev — no dollar figure is invented for it.

Usage (from backend/):  uv run python -m scripts.benchmark_judgment
Requires TYPESAFE_API_KEY and ANTHROPIC_API_KEY. Read-only: no files written except the report.
"""

import sys
import time
from statistics import mean

import anthropic
import typesafe_sdk as ts
from pydantic import BaseModel, Field

from app.clock import today
from app.config import get_settings
from app.models import Customer
from app.schemas import Priority, WaitingOn
from app.services.ai.prompts import PRIORITY_CRITERIA, WAITING_ON_CRITERIA, analysis_user_message
from app.services.ai.providers.jev_typesafe import URGENCY_LEVELS
from app.services.context import CustomerContext, build_context
from scripts.common import BACKEND_DIR, load_sample_session

MODEL = (
    "claude-sonnet-5"  # fixed for this benchmark regardless of .env, per the ask to use Sonnet 5
)
REPORT_FILE = BACKEND_DIR.parent / "docs" / "judgment_benchmark.md"

# Anthropic's published per-token rate for claude-sonnet-5, per the claude-api skill's pricing
# table (cached 2026-06-24). Update this if pricing changes; it is not read from any live API.
SONNET_5_PRICE_PER_MTOK = {"input": 2.00, "output": 10.00}

_priority_rubric = "; ".join(f"{level} = {desc}" for level, desc in PRIORITY_CRITERIA.items())
_waiting_on_rubric = "; ".join(f'"{who}" when {desc}' for who, desc in WAITING_ON_CRITERIA.items())

JUDGMENT_ONLY_SYSTEM_PROMPT = f"""You judge one CRM account. Return only a typed judgment,
no prose summary.

Priority means: {_priority_rubric}
waiting_on: {_waiting_on_rubric}
needs_attention: true if the salesperson should act within 7 days.
urgency_score: 0.0 (no urgency) to 1.0 (act today).
"""


class JudgmentOnlyOutput(BaseModel):
    priority: Priority
    waiting_on: WaitingOn
    needs_attention: bool
    urgency_score: float = Field(ge=0.0, le=1.0)


class Sample(BaseModel):
    customer_name: str
    jev_latency_ms: int
    jev_input_tokens: int | None
    jev_output_tokens: int | None
    llm_latency_ms: int
    llm_input_tokens: int
    llm_output_tokens: int
    llm_cost_usd: float


def jev_questions() -> dict[str, ts.Choice | ts.Noul | ts.Score]:
    """The same four questions JevJudgmentProvider.judge() asks, built once and reused per call."""
    return {
        "priority": ts.Choice(
            instructions=(
                "Given this account's interaction history and signals, how urgently "
                "should the salesperson act on it?"
            ),
            criteria=PRIORITY_CRITERIA,
        ),
        "waiting_on": ts.Choice(
            instructions="Who owes the next move in this relationship?",
            criteria=WAITING_ON_CRITERIA,
        ),
        "needs_attention": ts.Noul(
            instructions="Should the salesperson act on this account within the next 7 days?"
        ),
        "urgency": ts.Score(
            instructions="How urgent is it for the salesperson to act on this account right now?",
            criteria=URGENCY_LEVELS,
        ),
    }


def time_jev(
    client: ts.TypeSafeClient, context: CustomerContext
) -> tuple[int, int | None, int | None]:
    started = time.perf_counter()
    result = client.system_one(state=context.model_dump(mode="json"), questions=jev_questions())
    latency_ms = int((time.perf_counter() - started) * 1000)
    return latency_ms, result.usage.input_tokens, result.usage.output_tokens


def time_llm(client: anthropic.Anthropic, context: CustomerContext) -> tuple[int, int, int]:
    started = time.perf_counter()
    response = client.messages.parse(
        model=MODEL,
        max_tokens=1000,
        system=JUDGMENT_ONLY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": analysis_user_message(context)}],
        output_format=JudgmentOnlyOutput,
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    return latency_ms, response.usage.input_tokens, response.usage.output_tokens


def llm_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * SONNET_5_PRICE_PER_MTOK["input"]
        + output_tokens * SONNET_5_PRICE_PER_MTOK["output"]
    ) / 1_000_000


def main() -> None:
    settings = get_settings()
    if not settings.typesafe_api_key:
        print("TYPESAFE_API_KEY is not set; nothing to benchmark. See .env.example.")
        sys.exit(1)
    if not settings.anthropic_api_key:
        print("ANTHROPIC_API_KEY is not set; nothing to benchmark. See .env.example.")
        sys.exit(1)

    jev_client = ts.TypeSafeClient(api_key=settings.typesafe_api_key)
    llm_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    print(f"Benchmarking jev vs {MODEL} on judgment latency and cost\n")

    session = load_sample_session()
    customers = session.query(Customer).order_by(Customer.id).all()
    samples: list[Sample] = []

    llm_ms_header = f"{MODEL} ms"
    header = (
        f"{'Customer':<28} {'jev ms':<8} {'jev tok':<9} {llm_ms_header:<15} "
        f"{'sonnet tok':<11} {'sonnet $':<10}"
    )
    print(header)
    print("-" * len(header))
    for customer in customers:
        context = build_context(customer, today())
        jev_ms, jev_in, jev_out = time_jev(jev_client, context)
        llm_ms, llm_in, llm_out = time_llm(llm_client, context)
        cost = llm_cost(llm_in, llm_out)
        jev_tokens = f"{(jev_in or 0) + (jev_out or 0)}" if jev_in is not None else "n/a"
        samples.append(
            Sample(
                customer_name=customer.name,
                jev_latency_ms=jev_ms,
                jev_input_tokens=jev_in,
                jev_output_tokens=jev_out,
                llm_latency_ms=llm_ms,
                llm_input_tokens=llm_in,
                llm_output_tokens=llm_out,
                llm_cost_usd=cost,
            )
        )
        print(
            f"{customer.name:<28} {jev_ms:<8} {jev_tokens:<9} {llm_ms:<15} "
            f"{llm_in + llm_out:<11} ${cost:.5f}"
        )

    write_report(samples)
    print_summary(samples)


def print_summary(samples: list[Sample]) -> None:
    total_llm_cost = sum(s.llm_cost_usd for s in samples)
    print()
    print(f"Average jev latency:    {mean(s.jev_latency_ms for s in samples):.0f} ms")
    print(f"Average {MODEL} latency: {mean(s.llm_latency_ms for s in samples):.0f} ms")
    print(f"Total {MODEL} cost for {len(samples)} judgments: ${total_llm_cost:.5f}")
    print(f"Average {MODEL} cost per judgment: ${total_llm_cost / len(samples):.5f}")
    print("Jev cost: not computed — TypeSafe does not publish public per-token/per-call pricing.")


def write_report(samples: list[Sample]) -> None:
    total_llm_cost = sum(s.llm_cost_usd for s in samples)
    lines = [
        "# Judgment latency and cost benchmark: Jev vs an LLM",
        "",
        f"Generated by `backend/scripts/benchmark_judgment.py`. Both sides answer only the "
        f"judgment question (priority, waiting_on, needs_attention, urgency) over the same "
        f"account context — not the app's normal combined judgment+narrative call. LLM side "
        f"uses `{MODEL}`.",
        "",
        "## Results",
        "",
        f"| Customer | jev ms | jev tokens | {MODEL} ms | {MODEL} tokens | {MODEL} cost |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for s in samples:
        jev_tokens = (
            f"{(s.jev_input_tokens or 0) + (s.jev_output_tokens or 0)}"
            if s.jev_input_tokens is not None
            else "n/a"
        )
        llm_tokens = s.llm_input_tokens + s.llm_output_tokens
        lines.append(
            f"| {s.customer_name} | {s.jev_latency_ms} | {jev_tokens} | "
            f"{s.llm_latency_ms} | {llm_tokens} | ${s.llm_cost_usd:.5f} |"
        )
    lines += [
        "",
        "## Summary",
        "",
        f"- Average jev latency: **{mean(s.jev_latency_ms for s in samples):.0f} ms**",
        f"- Average {MODEL} latency: **{mean(s.llm_latency_ms for s in samples):.0f} ms**",
        f"- Total {MODEL} cost for {len(samples)} judgments: **${total_llm_cost:.5f}**",
        f"- Average {MODEL} cost per judgment: **${total_llm_cost / len(samples):.5f}**",
        (
            f"- Anthropic pricing used: ${SONNET_5_PRICE_PER_MTOK['input']:.2f}/MTok input, "
            f"${SONNET_5_PRICE_PER_MTOK['output']:.2f}/MTok output (published rate for "
            f"`claude-sonnet-5`)."
        ),
        (
            "- Jev cost: not computed. TypeSafe does not publish public per-token or per-call "
            "pricing as of this writing (checked docs.typesafe.ai); only token counts and "
            "latency are reported. Update `SONNET_5_PRICE_PER_MTOK` and add a Jev rate here if "
            "pricing becomes available."
        ),
        (
            "- This measures the judgment step in isolation on both sides. The app's default "
            "flow asks the LLM for judgment and narrative together in one call, so when Jev is "
            "not enabled, the LLM's judgment costs nothing extra beyond the narrative it already "
            "has to generate — see docs/AI_DESIGN.md."
        ),
    ]
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {REPORT_FILE}")


if __name__ == "__main__":
    main()
