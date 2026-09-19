"""Loads the sample CSVs and, when available, pre-computed AI analyses into an empty database.

The CSVs were extracted from a PDF and carry line breaks inside quoted notes, so whitespace is
normalised on import. Pre-computed analyses (data/seed_analyses.json) let the demo open with real
AI output instantly and without an API key; if the file is missing the rule-based provider fills in.
"""

import csv
import json
import logging
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Contact, Customer, CustomerAnalysis, Interaction
from app.services.ai.analyzer import analyze_customer

log = logging.getLogger(__name__)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SEED_ANALYSES = DATA_DIR / "seed_analyses.json"


def seed_if_empty(session: Session) -> None:
    if session.scalar(select(Customer).limit(1)) is not None:
        return
    log.info("Empty database: importing sample data from %s", DATA_DIR)
    load_csvs(session)
    if SEED_ANALYSES.exists():
        load_seed_analyses(session)
    else:
        log.info("No seed_analyses.json found; analysing with the configured provider")
        for customer in session.scalars(select(Customer)).all():
            analyze_customer(session, customer, trigger="seed")
    session.commit()


def load_csvs(session: Session) -> None:
    for row in read_csv("customers.csv"):
        session.add(
            Customer(
                id=row["id"],
                name=row["name"],
                status=row["status"],
                created_at=date.fromisoformat(row["created_at"]),
            )
        )
    for row in read_csv("contacts.csv"):
        session.add(Contact(**row))
    for row in read_csv("interactions.csv"):
        session.add(
            Interaction(
                id=row["id"],
                customer_id=row["customer_id"],
                contact_id=row["contact_id"] or None,
                type=row["type"],
                occurred_at=date.fromisoformat(row["occurred_at"]),
                notes=" ".join(row["notes"].split()),
            )
        )
    session.flush()


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA_DIR / name).open(newline="", encoding="utf-8") as handle:
        return [{k: v.strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def load_seed_analyses(session: Session) -> None:
    payload = json.loads(SEED_ANALYSES.read_text(encoding="utf-8"))
    generated_at = datetime.fromisoformat(payload["generated_at"])
    for customer_id, entry in payload["customers"].items():
        customer = session.get(Customer, customer_id)
        if customer is None:
            continue
        analysis = CustomerAnalysis(
            customer_id=customer_id,
            created_at=generated_at,
            trigger="seed",
            **entry["judgment"],
            **entry["narrative"],
            signals_snapshot=entry.get("signals", {}),
            judgment_provider=payload["judgment_provider"],
            generation_provider=payload["generation_provider"],
            model=payload.get("model"),
            latency_ms=entry.get("latency_ms"),
            fallback_used=False,
        )
        analysis.suggested_follow_up_date = date.fromisoformat(
            entry["narrative"]["suggested_follow_up_date"]
        )
        session.add(analysis)
        customer.follow_up_date = analysis.suggested_follow_up_date
        customer.follow_up_source = "ai"
    session.flush()
