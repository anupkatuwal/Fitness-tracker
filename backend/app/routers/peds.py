"""Read-only access to the seeded PED / peptide educational library.

Every response includes the cardiovascular, endocrine and hepatic risk fields.
They are non-nullable in the schema, so a compound can never be served without
its hazard information.
"""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.deps import DbSession
from app.models import PEDProfile
from app.schemas import PEDProfileRead

router = APIRouter(prefix="/peds", tags=["peds"])

DISCLAIMER = (
    "Educational reference only. This is not medical advice and is not an endorsement or "
    "encouragement of use. Every compound listed here carries documented cardiovascular, "
    "endocrine and hepatic risks. Non-medical use is unlawful in many jurisdictions. "
    "Consult a qualified physician."
)


@router.get("", response_model=list[PEDProfileRead])
def list_peds(
    db: DbSession,
    category: str | None = Query(default=None, description="Filter by category"),
    compound_class: str | None = Query(default=None, description="Filter by compound class"),
    search: str | None = Query(default=None, max_length=128),
) -> list[PEDProfile]:
    stmt = select(PEDProfile)

    if category and category.lower() != "all":
        stmt = stmt.where(func.lower(PEDProfile.category) == category.strip().lower())
    if compound_class and compound_class.lower() != "all":
        stmt = stmt.where(func.lower(PEDProfile.compound_class) == compound_class.strip().lower())
    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(func.lower(PEDProfile.name).like(term), func.lower(PEDProfile.aliases).like(term))
        )

    return list(db.scalars(stmt.order_by(PEDProfile.category, PEDProfile.name)).all())


@router.get("/categories", response_model=list[str])
def list_categories(db: DbSession) -> list[str]:
    return sorted(db.scalars(select(PEDProfile.category).distinct()).all())


@router.get("/disclaimer", response_model=dict)
def get_disclaimer() -> dict:
    return {"disclaimer": DISCLAIMER}


@router.get("/{slug}", response_model=PEDProfileRead)
def get_ped(slug: str, db: DbSession) -> PEDProfile:
    profile = db.scalar(select(PEDProfile).where(PEDProfile.slug == slug))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compound not found.")
    return profile
