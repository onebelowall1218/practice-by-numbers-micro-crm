from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clock import is_demo_clock, today
from app.db import get_session
from app.models import Customer
from app.schemas import DashboardOut
from app.services.dashboard import build_buckets
from app.services.serializers import customer_summary_out

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(session: Session = Depends(get_session)) -> DashboardOut:
    as_of = today()
    customers = session.scalars(select(Customer)).all()
    summaries = [customer_summary_out(c, as_of) for c in customers]
    return DashboardOut(
        as_of=as_of, demo_clock=is_demo_clock(), buckets=build_buckets(summaries, as_of)
    )
