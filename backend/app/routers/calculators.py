"""BMR / TDEE calculation.

BMR uses the Mifflin-St Jeor equation, the formula most commonly recommended
for healthy adults:

    male:   (10 x kg) + (6.25 x cm) - (5 x age) + 5
    female: (10 x kg) + (6.25 x cm) - (5 x age) - 161

TDEE is BMR multiplied by a standard activity factor. Fiber targets follow the
common 14 g per 1,000 kcal guideline. All of it is an estimate, not a
prescription.
"""

from fastapi import APIRouter

from app.schemas import CalculatorRequest, CalculatorResponse

router = APIRouter(prefix="/calculators", tags=["calculators"])

ACTIVITY_MULTIPLIERS: dict[str, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_ADJUSTMENTS: dict[str, float] = {"cut": -0.20, "maintain": 0.0, "bulk": 0.10}

PROTEIN_G_PER_KG = 2.0
FAT_CALORIE_SHARE = 0.25
KCAL_PER_G_PROTEIN = 4.0
KCAL_PER_G_CARB = 4.0
KCAL_PER_G_FAT = 9.0
FIBER_G_PER_1000_KCAL = 14.0


def mifflin_st_jeor(sex: str, age: int, height_cm: float, weight_kg: float) -> float:
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    return base + 5 if sex == "male" else base - 161


@router.post("/tdee", response_model=CalculatorResponse)
def calculate_tdee(payload: CalculatorRequest) -> CalculatorResponse:
    bmr = mifflin_st_jeor(payload.sex, payload.age, payload.height_cm, payload.weight_kg)
    multiplier = ACTIVITY_MULTIPLIERS[payload.activity_level]
    tdee = bmr * multiplier
    target = tdee * (1 + GOAL_ADJUSTMENTS[payload.goal])

    protein_g = PROTEIN_G_PER_KG * payload.weight_kg
    fats_g = (target * FAT_CALORIE_SHARE) / KCAL_PER_G_FAT
    remaining = target - (protein_g * KCAL_PER_G_PROTEIN) - (fats_g * KCAL_PER_G_FAT)
    carbs_g = max(remaining, 0.0) / KCAL_PER_G_CARB

    return CalculatorResponse(
        bmr=round(bmr, 1),
        tdee=round(tdee, 1),
        target_calories=round(target, 1),
        activity_multiplier=multiplier,
        protein_g=round(protein_g, 1),
        carbs_g=round(carbs_g, 1),
        fats_g=round(fats_g, 1),
        fiber_g=round((target / 1000) * FIBER_G_PER_1000_KCAL, 1),
    )
