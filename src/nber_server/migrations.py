from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from nber_cli import db


def upgrade_database(db_path: Path | str) -> Path:
    resolved = db.init_database(db_path)
    config = Config()
    config.set_main_option(
        "script_location",
        str(Path(db.__file__).resolve().parent / "migrations"),
    )
    config.set_main_option("sqlalchemy.url", f"sqlite:///{resolved.as_posix()}")
    command.upgrade(config, "head")
    return resolved
