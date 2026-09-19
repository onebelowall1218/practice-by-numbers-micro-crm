"""Runs the configured AI provider over every sample customer and writes data/seed_analyses.json.

Usage (from backend/):  uv run python -m scripts.generate_seed_analyses
The output is committed so the demo opens with real AI results instantly and without a key.
"""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from app.clock import today
from app.models import Customer
from app.services.ai.analyzer import run_analysis
from app.services.ai.factory import get_providers
from app.services.context import CustomerContext, build_context
from scripts.common import BACKEND_DIR, load_sample_session

OUTPUT = BACKEND_DIR / "data" / "seed_analyses.json"


def analyse_one(context: CustomerContext) -> tuple[str, dict]:
    """Runs in a worker thread; receives plain data, never a database session."""
    result = run_analysis(context)
    flag = "  (fallback)" if result.fallback_used else ""
    print(
        f"  {context.customer_name:<30} {result.judgment.priority:<7} "
        f"{result.latency_ms:>6} ms{flag}"
    )
    return context.customer_id, {
        "judgment": result.judgment.model_dump(),
        "narrative": result.narrative.model_dump(mode="json", exclude={"interaction_summary"}),
        "signals": context.signals.model_dump(mode="json"),
        "latency_ms": result.latency_ms,
    }


def main() -> None:
    judgment, generation = get_providers()
    model = getattr(generation, "model", None)
    print(
        f"Provider: judgment={judgment.name} generation={generation.name} "
        f"model={model} today={today()}"
    )
    session = load_sample_session()
    customers = session.query(Customer).order_by(Customer.id).all()
    contexts = [build_context(customer, today()) for customer in customers]
    with ThreadPoolExecutor(max_workers=4) as pool:
        entries = dict(pool.map(analyse_one, contexts))
    payload = {
        "generated_at": datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds"),
        "today": today().isoformat(),
        "judgment_provider": judgment.name,
        "generation_provider": generation.name,
        "model": model,
        "customers": entries,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    average_ms = sum(entry["latency_ms"] for entry in entries.values()) / len(entries)
    print(f"Wrote {OUTPUT} ({len(entries)} customers, {average_ms:.0f} ms average)")


if __name__ == "__main__":
    main()
