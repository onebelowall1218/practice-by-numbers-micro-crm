"""Checks AI analyses against what a careful salesperson would expect for the 12 sample accounts.

Usage (from backend/):
  uv run python -m scripts.eval            # evaluates data/seed_analyses.json (no API calls)
  uv run python -m scripts.eval --live     # re-runs the configured provider first

Expectations are deliberately tolerant where reasonable people could disagree (e.g. medium|low).
Writes a markdown report to docs/eval_results.md.
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import date

from app.models import Customer
from scripts.common import BACKEND_DIR, load_sample_session

SEED_FILE = BACKEND_DIR / "data" / "seed_analyses.json"
REPORT_FILE = BACKEND_DIR.parent / "docs" / "eval_results.md"


@dataclass
class Expectation:
    priorities: set[str]
    reason: str
    follow_up_not_before: date | None = None
    open_item_keywords: list[str] = field(default_factory=list)


EXPECTED: dict[str, Expectation] = {
    "cust_001": Expectation(
        {"high"}, "Proposal sent Aug 23, no reply; note on Aug 29 flags follow-up"
    ),
    "cust_002": Expectation(
        {"high", "medium"},
        "Happy customer, but her SMS question from Aug 26 is unanswered (waiting on us)",
        open_item_keywords=["sms"],
    ),
    "cust_003": Expectation(
        {"high", "medium"}, "Demo link never used, silent since July, opens 2nd location in October"
    ),
    "cust_004": Expectation({"low"}, "Latency issue resolved; note says no follow-up required"),
    "cust_005": Expectation(
        {"medium", "high"},
        "Received reference; said she will decide in September (decision window)",
    ),
    "cust_006": Expectation(
        {"medium", "low"}, "Healthy customer; expansion hint (second office next year)"
    ),
    "cust_007": Expectation({"medium", "high"}, "Went cold after pricing; inactive over a month"),
    "cust_008": Expectation({"low"}, "Spanish enabled, positive feedback; healthy"),
    "cust_009": Expectation({"high"}, "High-intent, asked about onboarding before Sep 15"),
    "cust_010": Expectation({"low", "medium"}, "Satisfied customer, no engagement since April"),
    "cust_011": Expectation(
        {"medium", "low"},
        "Asked not to push before September planning meeting",
        follow_up_not_before=date(2026, 9, 10),
    ),
    "cust_012": Expectation(
        {"high"}, "Julia asked for a follow-up this week to discuss implementation"
    ),
}


def load_analyses(live: bool) -> tuple[dict, str]:
    if live:
        from scripts.generate_seed_analyses import main as regenerate

        regenerate()
    payload = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    return payload["customers"], f"{payload['generation_provider']} / {payload.get('model')}"


def check_customer(
    customer: Customer, entry: dict, expected: Expectation, today: date
) -> list[str]:
    """Returns a list of failure messages; empty means pass."""
    judgment, narrative = entry["judgment"], entry["narrative"]
    failures: list[str] = []
    if judgment["priority"] not in expected.priorities:
        failures.append(f"priority {judgment['priority']} not in {sorted(expected.priorities)}")
    follow_up = date.fromisoformat(narrative["suggested_follow_up_date"])
    if follow_up < today:
        failures.append(f"follow-up {follow_up} is in the past")
    if expected.follow_up_not_before and follow_up < expected.follow_up_not_before:
        failures.append(f"follow-up {follow_up} before {expected.follow_up_not_before}")
    known_ids = {i.id for i in customer.interactions}
    unknown = [e for e in narrative["evidence_ids"] if e not in known_ids]
    if unknown:
        failures.append(f"unknown evidence ids {unknown}")
    if not narrative["evidence_ids"]:
        failures.append("no evidence ids")
    contact_names = [c.name.split()[0] for c in customer.contacts]
    if not any(name in narrative["next_action"] for name in contact_names):
        failures.append("next_action names no known contact")
    if narrative["relationship_summary"].count(". ") > 4:
        failures.append("relationship summary longer than 4 sentences")
    for keyword in expected.open_item_keywords:
        if not any(keyword in item.lower() for item in narrative["open_items"]):
            failures.append(f"open_items missing '{keyword}'")
    return failures


def main() -> None:
    live = "--live" in sys.argv
    analyses, provider = load_analyses(live)
    session = load_sample_session()
    today = date.fromisoformat(json.loads(SEED_FILE.read_text())["today"])
    rows, passed = [], 0
    for customer_id, expected in EXPECTED.items():
        customer = session.get(Customer, customer_id)
        failures = check_customer(customer, analyses[customer_id], expected, today)
        passed += not failures
        got = analyses[customer_id]["judgment"]["priority"]
        rows.append(
            (
                customer.name,
                "/".join(sorted(expected.priorities)),
                got,
                "pass" if not failures else "FAIL: " + "; ".join(failures),
            )
        )
    write_report(rows, passed, provider, today)
    for row in rows:
        print(f"{row[0]:<28} expected {row[1]:<12} got {row[2]:<7} {row[3]}")
    print(f"\n{passed}/{len(rows)} passed  ({provider}, today={today})")
    sys.exit(0 if passed == len(rows) else 1)


def write_report(rows: list[tuple], passed: int, provider: str, today: date) -> None:
    lines = [
        "# AI quality evaluation",
        "",
        f"Provider: `{provider}`. Demo date: {today}. Result: **{passed}/{len(rows)} passed**.",
        "",
        "Generated by `python -m scripts.eval`. Each row checks the priority against an expected",
        "set,",
        "that the follow-up date is not in the past, that evidence ids exist for that customer,",
        "that the next action names a real contact, and customer-specific constraints.",
        "",
        "| Customer | Expected | Got | Result |",
        "| --- | --- | --- | --- |",
    ]
    lines += [f"| {name} | {exp} | {got} | {result} |" for name, exp, got, result in rows]
    REPORT_FILE.parent.mkdir(exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
