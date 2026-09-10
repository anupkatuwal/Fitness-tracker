"""Macro tracking: OpenFoodFacts search plus the user's personal food log."""

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import delete, func, select

from app.deps import CurrentUser, DbSession
from app.models import MacroLog
from app.schemas import (
    DailySummary,
    FoodSearchResponse,
    FoodSearchResult,
    MacroLogCreate,
    MacroLogRead,
    MacroTotals,
    TrendPoint,
    TrendResponse,
)
from app.services import openfoodfacts

router = APIRouter(prefix="/macros", tags=["macros"])


def _goals(user) -> MacroTotals:
    return MacroTotals(
        calories=user.goal_calories,
        protein_g=user.goal_protein_g,
        carbs_g=user.goal_carbs_g,
        fats_g=user.goal_fats_g,
        fiber_g=user.goal_fiber_g,
    )


# ------------------------------------------------------------------ external search
@router.get("/search", response_model=FoodSearchResponse)
async def search_foods(
    current_user: CurrentUser,
    q: str = Query(min_length=2, max_length=128, description="Food search term"),
    page_size: int = Query(default=20, ge=1, le=50),
) -> FoodSearchResponse:
    """Live search against OpenFoodFacts. Macros come back per 100 g."""
    results = await openfoodfacts.search_foods(q, page_size=page_size)
    return FoodSearchResponse(query=q, count=len(results), results=results)


@router.get("/barcode/{barcode}", response_model=FoodSearchResult)
async def lookup_barcode(barcode: str, current_user: CurrentUser) -> FoodSearchResult:
    product = await openfoodfacts.get_food_by_barcode(barcode)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No product with usable nutrition data was found for that barcode.",
        )
    return product


# ----------------------------------------------------------------------- the log
@router.post("/logs", response_model=MacroLogRead, status_code=status.HTTP_201_CREATED)
def create_log(payload: MacroLogCreate, current_user: CurrentUser, db: DbSession) -> MacroLog:
    """Save a selected food to the user's macro log.

    ``calories``/``protein_g``/... are the totals for the amount actually eaten;
    the frontend scales the per-100 g values from OpenFoodFacts before posting.
    """
    entry = MacroLog(
        user_id=current_user.id,
        **payload.model_dump(exclude={"logged_on"}),
        logged_on=payload.logged_on or date.today(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/logs", response_model=list[MacroLogRead])
def list_logs(
    current_user: CurrentUser,
    db: DbSession,
    day: date | None = Query(default=None, description="Defaults to today"),
) -> list[MacroLog]:
    target = day or date.today()
    stmt = (
        select(MacroLog)
        .where(MacroLog.user_id == current_user.id, MacroLog.logged_on == target)
        .order_by(MacroLog.created_at)
    )
    return list(db.scalars(stmt).all())


@router.delete("/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_log(log_id: int, current_user: CurrentUser, db: DbSession) -> None:
    result = db.execute(
        delete(MacroLog).where(MacroLog.id == log_id, MacroLog.user_id == current_user.id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log entry not found.")
    db.commit()


# ------------------------------------------------------------------- aggregations
@router.get("/summary", response_model=DailySummary)
def daily_summary(
    current_user: CurrentUser,
    db: DbSession,
    day: date | None = Query(default=None, description="Defaults to today"),
) -> DailySummary:
    target = day or date.today()
    entries = list(
        db.scalars(
            select(MacroLog)
            .where(MacroLog.user_id == current_user.id, MacroLog.logged_on == target)
            .order_by(MacroLog.created_at)
        ).all()
    )

    totals = MacroTotals(
        calories=round(sum(e.calories for e in entries), 2),
        protein_g=round(sum(e.protein_g for e in entries), 2),
        carbs_g=round(sum(e.carbs_g for e in entries), 2),
        fats_g=round(sum(e.fats_g for e in entries), 2),
        fiber_g=round(sum(e.fiber_g for e in entries), 2),
    )

    return DailySummary(
        day=target,
        totals=totals,
        goals=_goals(current_user),
        entries=[MacroLogRead.model_validate(e) for e in entries],
    )


@router.get("/trend", response_model=TrendResponse)
def macro_trend(
    current_user: CurrentUser,
    db: DbSession,
    days: int = Query(default=7, ge=1, le=90, description="Window size, ending today"),
) -> TrendResponse:
    """Per-day totals for the trailing window. Days with no entries return zeros."""
    end = date.today()
    start = end - timedelta(days=days - 1)

    rows = db.execute(
        select(
            MacroLog.logged_on,
            func.sum(MacroLog.calories),
            func.sum(MacroLog.protein_g),
            func.sum(MacroLog.carbs_g),
            func.sum(MacroLog.fats_g),
            func.sum(MacroLog.fiber_g),
        )
        .where(
            MacroLog.user_id == current_user.id,
            MacroLog.logged_on >= start,
            MacroLog.logged_on <= end,
        )
        .group_by(MacroLog.logged_on)
    ).all()

    by_day = {row[0]: row for row in rows}
    points: list[TrendPoint] = []
    for offset in range(days):
        current = start + timedelta(days=offset)
        row = by_day.get(current)
        points.append(
            TrendPoint(
                day=current,
                calories=round(row[1] or 0.0, 2) if row else 0.0,
                protein_g=round(row[2] or 0.0, 2) if row else 0.0,
                carbs_g=round(row[3] or 0.0, 2) if row else 0.0,
                fats_g=round(row[4] or 0.0, 2) if row else 0.0,
                fiber_g=round(row[5] or 0.0, 2) if row else 0.0,
            )
        )

    return TrendResponse(days=days, goals=_goals(current_user), points=points)
