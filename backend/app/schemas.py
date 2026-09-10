"""Pydantic v2 request/response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

ORM = ConfigDict(from_attributes=True)

MealType = Literal["breakfast", "lunch", "dinner", "snack", "other"]
Sex = Literal["male", "female"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]


# --------------------------------------------------------------------------- users
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    full_name: str | None = Field(default=None, max_length=128)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("password must be at most 72 bytes")
        return v


class UserGoalsUpdate(BaseModel):
    age: int | None = Field(default=None, ge=13, le=100)
    sex: Sex | None = None
    height_cm: float | None = Field(default=None, gt=0, le=272)
    weight_kg: float | None = Field(default=None, gt=0, le=650)
    activity_level: ActivityLevel | None = None
    goal_calories: float | None = Field(default=None, ge=0, le=15000)
    goal_protein_g: float | None = Field(default=None, ge=0, le=1000)
    goal_carbs_g: float | None = Field(default=None, ge=0, le=2000)
    goal_fats_g: float | None = Field(default=None, ge=0, le=1000)
    goal_fiber_g: float | None = Field(default=None, ge=0, le=300)


class UserRead(UserBase):
    model_config = ORM

    id: int
    age: int | None = None
    sex: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    activity_level: str | None = None
    goal_calories: float
    goal_protein_g: float
    goal_carbs_g: float
    goal_fats_g: float
    goal_fiber_g: float
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# ----------------------------------------------------------------------- exercises
class ExerciseRead(BaseModel):
    model_config = ORM

    id: int
    name: str
    slug: str
    muscle_group: str
    secondary_muscles: str | None = None
    equipment: str
    mechanic: str
    difficulty: str
    description: str
    form_instructions: str
    common_mistakes: str | None = None
    safety_notes: str | None = None


class ExerciseFilters(BaseModel):
    muscle_groups: list[str]
    equipment: list[str]
    difficulties: list[str]


# ---------------------------------------------------------------------------- peds
class PEDProfileRead(BaseModel):
    model_config = ORM

    id: int
    name: str
    slug: str
    aliases: str | None = None
    compound_class: str
    category: str
    administration_route: str | None = None
    half_life: str | None = None
    mechanism_of_action: str
    claimed_effects: str
    evidence_summary: str
    cardiovascular_risk: str
    endocrine_risk: str
    hepatic_risk: str
    other_risks: str | None = None
    legal_status: str
    medical_supervision_required: bool
    harm_reduction_notes: str
    monitoring_bloodwork: str | None = None


# -------------------------------------------------------------------------- macros
class FoodSearchResult(BaseModel):
    """Normalised OpenFoodFacts hit — macros are always per 100 g/ml."""

    barcode: str | None = None
    name: str
    brand: str | None = None
    image_url: str | None = None
    serving_size_g: float | None = None
    calories_per_100g: float = 0.0
    protein_per_100g: float = 0.0
    carbs_per_100g: float = 0.0
    fats_per_100g: float = 0.0
    fiber_per_100g: float = 0.0


class FoodSearchResponse(BaseModel):
    query: str
    count: int
    results: list[FoodSearchResult]


class MacroLogCreate(BaseModel):
    food_name: str = Field(min_length=1, max_length=255)
    brand: str | None = Field(default=None, max_length=255)
    barcode: str | None = Field(default=None, max_length=64)
    source: str = Field(default="openfoodfacts", max_length=32)
    serving_size_g: float = Field(default=100.0, gt=0, le=10000)
    servings: float = Field(default=1.0, gt=0, le=100)
    meal_type: MealType = "other"
    calories: float = Field(default=0.0, ge=0, le=50000)
    protein_g: float = Field(default=0.0, ge=0, le=5000)
    carbs_g: float = Field(default=0.0, ge=0, le=5000)
    fats_g: float = Field(default=0.0, ge=0, le=5000)
    fiber_g: float = Field(default=0.0, ge=0, le=5000)
    logged_on: date | None = None


class MacroLogRead(BaseModel):
    model_config = ORM

    id: int
    food_name: str
    brand: str | None = None
    barcode: str | None = None
    source: str
    serving_size_g: float
    servings: float
    meal_type: str
    calories: float
    protein_g: float
    carbs_g: float
    fats_g: float
    fiber_g: float
    logged_on: date
    created_at: datetime


class MacroTotals(BaseModel):
    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fats_g: float = 0.0
    fiber_g: float = 0.0


class DailySummary(BaseModel):
    day: date
    totals: MacroTotals
    goals: MacroTotals
    entries: list[MacroLogRead]


class TrendPoint(BaseModel):
    day: date
    calories: float
    protein_g: float
    carbs_g: float
    fats_g: float
    fiber_g: float


class TrendResponse(BaseModel):
    days: int
    goals: MacroTotals
    points: list[TrendPoint]


# --------------------------------------------------------------------- calculators
class CalculatorRequest(BaseModel):
    sex: Sex
    age: int = Field(ge=13, le=100)
    height_cm: float = Field(gt=0, le=272)
    weight_kg: float = Field(gt=0, le=650)
    activity_level: ActivityLevel = "moderate"
    goal: Literal["cut", "maintain", "bulk"] = "maintain"


class CalculatorResponse(BaseModel):
    bmr: float
    tdee: float
    target_calories: float
    activity_multiplier: float
    protein_g: float
    carbs_g: float
    fats_g: float
    fiber_g: float
