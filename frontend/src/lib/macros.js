/** Shared macro metadata, formatting and scaling helpers. */

/* Series colours mirror the validated tokens in index.css. Recharts needs
   literal values, so they are defined once here and imported everywhere. */
export const SERIES = {
  calories: '#d55181',
  protein: '#3987e5',
  carbs: '#d95926',
  fats: '#199e70',
  fiber: '#c98500',
}

export const MACRO_ROWS = [
  { key: 'calories', label: 'Calories', unit: 'kcal', color: SERIES.calories },
  { key: 'protein_g', label: 'Protein', unit: 'g', color: SERIES.protein },
  { key: 'carbs_g', label: 'Carbs', unit: 'g', color: SERIES.carbs },
  { key: 'fats_g', label: 'Fats', unit: 'g', color: SERIES.fats },
  { key: 'fiber_g', label: 'Fiber', unit: 'g', color: SERIES.fiber },
]

export const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack', 'other']

export const round1 = (value) => Math.round((Number(value) || 0) * 10) / 10

export function formatNumber(value, digits = 0) {
  const number = Number(value) || 0
  return number.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

/** Scale OpenFoodFacts per-100g values to the amount actually eaten. */
export function scaleFood(food, gramsPerServing, servings) {
  const grams = (Number(gramsPerServing) || 0) * (Number(servings) || 0)
  const factor = grams / 100
  return {
    calories: round1(food.calories_per_100g * factor),
    protein_g: round1(food.protein_per_100g * factor),
    carbs_g: round1(food.carbs_per_100g * factor),
    fats_g: round1(food.fats_per_100g * factor),
    fiber_g: round1(food.fiber_per_100g * factor),
  }
}

/** ISO date (YYYY-MM-DD) for a Date, in the viewer's local timezone. */
export function toISODate(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 10)
}

/** "Mon 8" — short weekday label for trend axes. */
export function shortDayLabel(isoDate) {
  const [year, month, day] = isoDate.split('-').map(Number)
  const date = new Date(year, month - 1, day)
  return date.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' })
}
