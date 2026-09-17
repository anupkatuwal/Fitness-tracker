"""SQLAlchemy ORM models for Vanguard Fitness.

Column types are chosen to map cleanly onto Microsoft SQL Server 2022
(``NVARCHAR``/``NVARCHAR(MAX)``/``FLOAT``/``DATETIME2``) while remaining
portable to SQLite for local development.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    """Naive UTC timestamp (SQL Server ``DATETIME2`` has no timezone)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(128))

    # Body metrics used by the TDEE/BMR calculators.
    age: Mapped[int | None] = mapped_column(Integer)
    sex: Mapped[str | None] = mapped_column(String(16))
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    activity_level: Mapped[str | None] = mapped_column(String(32))

    # Daily macro targets.
    goal_calories: Mapped[float] = mapped_column(Float, default=2500.0, nullable=False)
    goal_protein_g: Mapped[float] = mapped_column(Float, default=180.0, nullable=False)
    goal_carbs_g: Mapped[float] = mapped_column(Float, default=280.0, nullable=False)
    goal_fats_g: Mapped[float] = mapped_column(Float, default=80.0, nullable=False)
    goal_fiber_g: Mapped[float] = mapped_column(Float, default=35.0, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    macro_logs: Mapped[list["MacroLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )


class MacroLog(Base):
    """One logged food entry for a user on a given day."""

    __tablename__ = "macro_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    food_name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(255))
    barcode: Mapped[str | None] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(32), default="openfoodfacts", nullable=False)

    serving_size_g: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    servings: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(32), default="other", nullable=False)

    # Totals for the logged amount (serving_size_g * servings), not per 100 g.
    calories: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    carbs_g: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fats_g: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fiber_g: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    logged_on: Mapped[date] = mapped_column(Date, default=lambda: utcnow().date(), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="macro_logs")


class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (UniqueConstraint("name", name="uq_exercises_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)

    muscle_group: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    secondary_muscles: Mapped[str | None] = mapped_column(String(255))
    equipment: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    mechanic: Mapped[str] = mapped_column(String(32), default="compound", nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), default="intermediate", nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)
    form_instructions: Mapped[str] = mapped_column(Text, nullable=False)
    common_mistakes: Mapped[str | None] = mapped_column(Text)
    safety_notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class PEDProfile(Base):
    """Educational reference entry for a performance-enhancing compound.

    Every row carries explicit cardiovascular, endocrine and hepatic risk text;
    the API and UI treat these fields as required, non-dismissible content.
    """

    __tablename__ = "ped_profiles"
    __table_args__ = (UniqueConstraint("name", name="uq_ped_profiles_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    aliases: Mapped[str | None] = mapped_column(String(255))

    compound_class: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    administration_route: Mapped[str | None] = mapped_column(String(64))
    half_life: Mapped[str | None] = mapped_column(String(64))

    mechanism_of_action: Mapped[str] = mapped_column(Text, nullable=False)
    claimed_effects: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Mandatory hazard fields, surfaced as hazard cards on every compound page.
    cardiovascular_risk: Mapped[str] = mapped_column(Text, nullable=False)
    endocrine_risk: Mapped[str] = mapped_column(Text, nullable=False)
    hepatic_risk: Mapped[str] = mapped_column(Text, nullable=False)
    other_risks: Mapped[str | None] = mapped_column(Text)

    legal_status: Mapped[str] = mapped_column(Text, nullable=False)
    medical_supervision_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    harm_reduction_notes: Mapped[str] = mapped_column(Text, nullable=False)
    monitoring_bloodwork: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


# Spec-facing alias: the schema is referred to as ``PED_Profile``.
PED_Profile = PEDProfile
