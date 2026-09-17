"""Alembic environment.

The database URL and the model metadata both come from the application, so
migrations always target the same database the app does and there is no second
connection string to keep in sync.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base

# Importing the models registers every table on ``Base.metadata``; without this
# autogenerate would see an empty schema and propose dropping everything.
from app import models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def _database_url() -> str:
    """The URL to migrate.

    An explicitly configured URL wins (a caller passing ``-x``, a test, or a CI
    job targeting a scratch database); otherwise it comes from application
    settings. Keeping it out of alembic.ini means no credentials are committed.
    """
    configured = config.get_main_option("sqlalchemy.url", None)
    if configured:
        return configured
    return settings.sqlalchemy_url


# "%" is the config parser's interpolation character, so it must be escaped
# before being stored back — passwords routinely contain one.
config.set_main_option("sqlalchemy.url", _database_url().replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it — useful for DBA review."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Catch column type changes, not just added/dropped columns.
            compare_type=True,
            # SQLite cannot ALTER most columns; batch mode rebuilds the table.
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
