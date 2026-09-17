"""Vanguard Fitness API entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, calculators, exercises, macros, peds

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Refuses to start in production with a forgeable JWT signing key.
    settings.enforce_production_safety()
    init_db()
    logger.info("Database ready at %s", settings.sqlalchemy_url.split("://")[0])
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Backend for Vanguard Fitness: macro tracking backed by OpenFoodFacts, "
        "an exercise directory, and an educational PED/peptide reference library."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth.router, exercises.router, peds.router, macros.router, calculators.router):
    app.include_router(router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
