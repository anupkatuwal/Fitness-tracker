"""Guards that Alembic migrations stay in step with the ORM models.

Without this, adding a column to a model and forgetting the migration passes
every other test and only breaks in production, where ``create_all`` is off.
"""

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from app.database import Base
from app import models  # noqa: F401  (registers the mappers)


@pytest.fixture()
def migrated_engine(tmp_path):
    """A database built by running the migrations, not by ``create_all``."""
    from alembic import command
    from alembic.config import Config

    db_path = tmp_path / "migrated.db"
    config = Config("alembic.ini")
    config.set_main_option("script_location", "migrations")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{db_path}")
    yield engine
    engine.dispose()


def test_migrations_produce_the_model_schema(migrated_engine):
    """Running the migrations must yield exactly what the models describe."""
    with migrated_engine.connect() as connection:
        context = MigrationContext.configure(connection)
        diff = compare_metadata(context, Base.metadata)

    assert diff == [], (
        "The migrations and the ORM models have drifted apart. Run:\n"
        "  alembic revision --autogenerate -m '<describe the change>'\n"
        f"Outstanding differences: {diff}"
    )


def test_every_model_table_exists_after_migrating(migrated_engine):
    from sqlalchemy import inspect

    tables = set(inspect(migrated_engine).get_table_names())
    for table in ("users", "macro_logs", "exercises", "ped_profiles"):
        assert table in tables, f"{table} missing after 'alembic upgrade head'"
