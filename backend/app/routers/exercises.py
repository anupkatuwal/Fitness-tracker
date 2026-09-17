"""Read-only access to the seeded exercise directory."""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.deps import DbSession
from app.models import Exercise
from app.schemas import ExerciseFilters, ExerciseRead

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[ExerciseRead])
def list_exercises(
    db: DbSession,
    muscle_group: str | None = Query(default=None, description="Filter by primary muscle group"),
    equipment: str | None = Query(default=None, description="Filter by required equipment"),
    difficulty: str | None = Query(default=None, description="Filter by difficulty"),
    search: str | None = Query(default=None, max_length=128, description="Free-text name search"),
) -> list[Exercise]:
    stmt = select(Exercise)

    if muscle_group and muscle_group.lower() != "all":
        stmt = stmt.where(func.lower(Exercise.muscle_group) == muscle_group.strip().lower())
    if equipment and equipment.lower() != "all":
        stmt = stmt.where(func.lower(Exercise.equipment) == equipment.strip().lower())
    if difficulty and difficulty.lower() != "all":
        stmt = stmt.where(func.lower(Exercise.difficulty) == difficulty.strip().lower())
    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Exercise.name).like(term),
                func.lower(Exercise.secondary_muscles).like(term),
            )
        )

    return list(db.scalars(stmt.order_by(Exercise.muscle_group, Exercise.name)).all())


@router.get("/filters", response_model=ExerciseFilters)
def list_filter_options(db: DbSession) -> ExerciseFilters:
    """Distinct filter values, so the UI never hardcodes them."""
    return ExerciseFilters(
        muscle_groups=sorted(db.scalars(select(Exercise.muscle_group).distinct()).all()),
        equipment=sorted(db.scalars(select(Exercise.equipment).distinct()).all()),
        difficulties=sorted(db.scalars(select(Exercise.difficulty).distinct()).all()),
    )


@router.get("/{slug}", response_model=ExerciseRead)
def get_exercise(slug: str, db: DbSession) -> Exercise:
    exercise = db.scalar(select(Exercise).where(Exercise.slug == slug))
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found.")
    return exercise
