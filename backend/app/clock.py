"""Single source of "today" for the whole app.

The sample data ends on 2026-08-31, so demos pin CRM_TODAY to keep "days since" numbers sensible.
Every date comparison in the backend goes through today() so the override is never bypassed.
"""

from datetime import date

from app.config import get_settings


def today() -> date:
    return get_settings().crm_today or date.today()


def is_demo_clock() -> bool:
    return get_settings().crm_today is not None
