# Vanguard Fitness

A fitness web app in three parts: macro tracking backed by live
[OpenFoodFacts](https://world.openfoodfacts.org) search, a filterable exercise
directory with real form instruction, and an educational PED/peptide reference
that leads with risk rather than burying it.

```
backend/    FastAPI · SQLAlchemy 2.0 · Pydantic v2 · MS SQL Server 2022 (pyodbc)
frontend/   React 19 · Vite · Tailwind v4 · React Router · Recharts · Lucide
```

## Quick start

Two terminals.

```bash
# 1 — backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                  # fill in your SQL Server details
alembic upgrade head                  # create the schema
python seed.py                        # 10 exercises + 10 compound profiles
uvicorn app.main:app --reload         # http://127.0.0.1:8000/docs
```

```bash
# 2 — frontend
cd frontend
npm install
npm run dev                           # http://localhost:5173
```

No SQL Server handy? Set `VANGUARD_USE_SQLITE=true` in `backend/.env` and both
the seed script and the API run against a local SQLite file instead.

**Deploying?** Set `VANGUARD_ENVIRONMENT=production` and a real
`VANGUARD_SECRET_KEY` — the app refuses to start without one. See
[`backend/README.md`](backend/README.md#before-deploying).

Per-directory detail lives in [`backend/README.md`](backend/README.md) and
[`frontend/README.md`](frontend/README.md).

## Features

**Macro Tracker** — search real products by name, pick a portion, and log it.
Daily totals run against your goals as progress bars, with a 7-day trend line
that can switch between calories and protein/carbs/fats. Days you did not log
show as zero rather than being skipped, so gaps stay visible.

**Exercise Directory** — filter by muscle group, equipment and difficulty. Every
entry carries numbered form cues, the mistakes people actually make, and a
safety note.

**PED & Peptide Library** — ten compounds, each with its mechanism, what the
evidence genuinely supports (often much less than the marketing), legal status,
and monitoring guidance. Every compound page opens with a hazard banner and
carries three non-dismissible cards covering **cardiovascular**, **endocrine**
and **hepatic** risk. Card contrast is measured rather than estimated.

**Calculators** — BMR via Mifflin-St Jeor, TDEE via standard activity factors,
and a macro split you can apply to your tracked goals in one click.

## A note on the PED library

This is a reference, not a protocol, and not encouragement. It exists because
people researching these compounds will find information somewhere, and most of
what they find understates the harm. Every profile states its risks up front,
says plainly where human safety data does not exist, and points to a physician
rather than a forum. Nothing here is medical advice.

## Testing

```bash
cd backend && pytest      # 35 tests: auth, scoping, aggregation, parsing, migrations, rate limits
cd frontend && npm run lint && npm run build
```
