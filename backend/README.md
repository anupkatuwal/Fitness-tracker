# Vanguard Fitness — backend

FastAPI + SQLAlchemy 2.0 + Pydantic v2, targeting Microsoft SQL Server 2022
through `pyodbc`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then fill in your values
```

### Database

The production target is SQL Server 2022. You need the Microsoft ODBC driver
installed on the machine (`ODBC Driver 18 for SQL Server`) plus a database:

```sql
CREATE DATABASE VanguardFitness;
```

Set `VANGUARD_DB_HOST`, `VANGUARD_DB_USER`, `VANGUARD_DB_PASSWORD` and friends
in `.env`. To run the whole stack with SQL Server in Docker:

```bash
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=YourStrong@Passw0rd" \
  -p 1433:1433 -d mcr.microsoft.com/mssql/server:2022-latest
```

If the ODBC driver is not available (CI, or a quick local run), set
`VANGUARD_USE_SQLITE=true` and everything works against a local SQLite file.
`VANGUARD_DATABASE_URL` overrides both.

### Seed and run

```bash
python seed.py            # 10 exercises + 10 PED/peptide profiles
python seed.py --reset    # drop and recreate the tables first
uvicorn app.main:app --reload
```

Interactive API docs: <http://127.0.0.1:8000/docs>

## Tests

```bash
pytest                    # 23 tests, runs against SQLite
```

## API

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | — | Create an account, returns a JWT |
| POST | `/api/auth/login` | — | OAuth2 password flow; username **or** email |
| GET / PATCH | `/api/auth/me` | ✓ | Read / update profile and macro goals |
| GET | `/api/exercises` | — | Filter by `muscle_group`, `equipment`, `difficulty`, `search` |
| GET | `/api/exercises/filters` | — | Distinct filter values |
| GET | `/api/exercises/{slug}` | — | One exercise |
| GET | `/api/peds` | — | Filter by `category`, `compound_class`, `search` |
| GET | `/api/peds/categories` | — | Distinct categories |
| GET | `/api/peds/{slug}` | — | One compound, always including its risk fields |
| GET | `/api/macros/search?q=` | ✓ | Live OpenFoodFacts search |
| GET | `/api/macros/barcode/{code}` | ✓ | OpenFoodFacts barcode lookup |
| POST / GET | `/api/macros/logs` | ✓ | Save / list food log entries |
| DELETE | `/api/macros/logs/{id}` | ✓ | Delete an entry you own |
| GET | `/api/macros/summary` | ✓ | One day's totals against goals |
| GET | `/api/macros/trend?days=` | ✓ | Per-day totals, zero-filled |
| POST | `/api/calculators/tdee` | — | BMR / TDEE / macro split |

## Notes

**OpenFoodFacts.** `app/services/openfoodfacts.py` calls the public API and
normalises every product to **per-100 g** macros. Upstream payloads are treated
as untrusted — fields go missing, arrive as `null`, or arrive as strings, and
energy is sometimes only given in kilojoules — so everything passes through a
coercion helper and products with no usable macros are dropped rather than
returned as zeros. The frontend scales per-100 g values to the portion eaten
before posting a log entry.

**Macro log totals** are stored for the amount actually eaten, not per 100 g.

**PED risk fields.** `cardiovascular_risk`, `endocrine_risk` and `hepatic_risk`
are non-nullable columns and required response fields. A compound cannot be
stored or served without them.

**Passwords** are bcrypt-hashed and capped at 72 bytes, which is bcrypt's own
limit — longer input is rejected rather than silently truncated.
