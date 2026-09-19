"""Test setup: rule-based provider, pinned demo date, and a throwaway SQLite file per session."""

import os
import tempfile
from pathlib import Path

os.environ["LLM_PROVIDER"] = "rules"
os.environ["CRM_TODAY"] = "2026-09-01"
os.environ["DATABASE_URL"] = f"sqlite:///{Path(tempfile.mkdtemp()) / 'test.db'}"
os.environ["FRONTEND_DIST"] = "/nonexistent"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
