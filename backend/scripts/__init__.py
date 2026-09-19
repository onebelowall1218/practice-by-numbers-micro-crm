"""Script package. Runs before any script module, so environment defaults are set first.

Scripts always run against an in-memory copy of the sample data with the demo date pinned,
never against the app's crm.db.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("CRM_TODAY", "2026-09-01")
