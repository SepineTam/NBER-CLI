from __future__ import annotations

from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from nber_cli import config_store, db

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def _database_url() -> str:
    x_args = context.get_x_argument(as_dictionary=True)
    db_path = x_args.get("db_path")
    if db_path:
        resolved = Path(db_path).expanduser().resolve(strict=False)
        return f"sqlite:///{resolved.as_posix()}"

    configured_url = config.get_main_option("sqlalchemy.url")
    if configured_url:
        return configured_url

    resolved = config_store.default_db_path()
    return f"sqlite:///{resolved.as_posix()}"


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        db._reject_future_schema(connection)
        if connection.in_transaction():
            connection.commit()
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

    with connectable.begin() as connection:
        db._ensure_full_schema_on_connection(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
