"""Compares Jev's typed judgments against the configured LLM's judgments on the 12 seed accounts.

Both providers judge from the exact same CustomerContext (see backend/app/services/context.py),
so any disagreement reflects the models, not the input. Requires TYPESAFE_API_KEY; the configured
LLM_PROVIDER supplies the other side (defaults to whichever key is present, per the usual rules).

Usage (from backend/):  uv run python -m scripts.compare_judgment

This is a read-only comparison: it makes API calls but writes no files and changes no app state.
"""

import sys

from app.clock import today
from app.config import get_settings
from app.models import Customer
from app.services.ai.factory import build_generation_provider, resolve_provider_name
from app.services.ai.providers.jev_typesafe import JevJudgmentProvider
from app.services.context import build_context
from scripts.common import load_sample_session


def main() -> None:
    settings = get_settings()
    if not settings.typesafe_api_key:
        print("TYPESAFE_API_KEY is not set; nothing to compare. See .env.example.")
        sys.exit(1)

    jev = JevJudgmentProvider(settings.typesafe_api_key)
    llm_name = resolve_provider_name(settings)
    llm = build_generation_provider(llm_name, settings)
    print(f"Comparing jev against {llm_name} ({getattr(llm, 'model', None)})\n")

    session = load_sample_session()
    customers = session.query(Customer).order_by(Customer.id).all()

    priority_agree = waiting_on_agree = 0
    llm_column = f"{llm_name} priority"
    header = f"{'Customer':<28} {'jev priority':<13} {llm_column:<16} {'jev conf':<9} {'agree?'}"
    print(header)
    print("-" * len(header))
    for customer in customers:
        context = build_context(customer, today())
        jev_judgment = jev.judge(context)
        llm_judgment = llm.judge(context)  # type: ignore[attr-defined]
        priority_match = jev_judgment.priority == llm_judgment.priority
        waiting_on_match = jev_judgment.waiting_on == llm_judgment.waiting_on
        priority_agree += priority_match
        waiting_on_agree += waiting_on_match
        mark = (
            "priority+waiting_on"
            if priority_match and waiting_on_match
            else (
                "priority only"
                if priority_match
                else ("waiting_on only" if waiting_on_match else "disagree")
            )
        )
        confidence = (
            f"{jev_judgment.confidence:.2f}" if jev_judgment.confidence is not None else "—"
        )
        print(
            f"{customer.name:<28} {jev_judgment.priority:<13} {llm_judgment.priority:<16} "
            f"{confidence:<9} {mark}"
        )

    total = len(customers)
    print(f"\nPriority agreement:   {priority_agree}/{total}")
    print(f"Waiting-on agreement: {waiting_on_agree}/{total}")


if __name__ == "__main__":
    main()
