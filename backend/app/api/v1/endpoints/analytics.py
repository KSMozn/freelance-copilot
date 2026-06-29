from datetime import date, datetime, time

from fastapi import APIRouter, Query

from app.application.dto.analytics_dto import AnalyticsDashboardResponse
from app.core.deps import AnalyticsServiceDep, CurrentUser

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _to_datetime_start(d: date | None) -> datetime | None:
    if d is None:
        return None
    return datetime.combine(d, time.min)


def _to_datetime_end(d: date | None) -> datetime | None:
    if d is None:
        return None
    return datetime.combine(d, time.max)


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_dashboard(
    user: CurrentUser,
    service: AnalyticsServiceDep,
    from_date: date | None = Query(default=None, alias="from_date"),
    to_date: date | None = Query(default=None, alias="to_date"),
) -> AnalyticsDashboardResponse:
    """Compute the full analytics dashboard for the authenticated user.

    `from_date` / `to_date` (ISO YYYY-MM-DD) filter by `applications.created_at`
    and are inclusive at the day boundary.
    """
    return await service.get_dashboard(
        user_id=user.id,
        from_date=_to_datetime_start(from_date),
        to_date=_to_datetime_end(to_date),
    )
