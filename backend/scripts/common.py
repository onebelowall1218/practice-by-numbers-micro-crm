"""Helpers shared by the scripts: a throwaway in-memory database loaded from the CSVs."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.seed import load_csvs

BACKEND_DIR = Path(__file__).resolve().parent.parent


def load_sample_session() -> Session:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    load_csvs(session)
    session.commit()
    return session
