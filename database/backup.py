"""Create verified SQLite backups and restore copies without overwriting files."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from sqlalchemy.engine import make_url

from config import Config


def _configured_sqlite_database_path() -> Path:
    url = make_url(Config.SQLALCHEMY_DATABASE_URI)
    if url.get_backend_name() != "sqlite" or url.database in {None, "", ":memory:"}:
        raise ValueError("Backup utility requires a file-backed SQLite database.")
    return Path(url.database).resolve()


def _verify_database(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Database file does not exist: {path}")
    with sqlite3.connect(path) as connection:
        result = connection.execute("PRAGMA integrity_check").fetchone()
    if result is None or result[0] != "ok":
        raise ValueError(f"SQLite integrity check failed for: {path}")


def backup_database(destination: str | Path, source: str | Path | None = None) -> Path:
    """Back up the configured SQLite database to a new, verified file."""
    source_path = (
        Path(source).resolve()
        if source is not None
        else _configured_sqlite_database_path()
    )
    destination_path = Path(destination).resolve()
    if source_path == destination_path:
        raise ValueError("Backup destination must differ from the source database.")
    if destination_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {destination_path}")
    _verify_database(source_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sqlite3.connect(source_path) as source_connection:
            with sqlite3.connect(destination_path) as destination_connection:
                source_connection.backup(destination_connection)
        _verify_database(destination_path)
    except Exception:
        if destination_path.exists():
            destination_path.unlink()
        raise
    return destination_path


def restore_database(source: str | Path, destination: str | Path) -> Path:
    """Restore a verified backup to a new file, never overwriting a database."""
    source_path = Path(source).resolve()
    destination_path = Path(destination).resolve()
    if source_path == destination_path:
        raise ValueError("Restore source and destination must differ.")
    if destination_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {destination_path}")
    _verify_database(source_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sqlite3.connect(source_path) as source_connection:
            with sqlite3.connect(destination_path) as destination_connection:
                source_connection.backup(destination_connection)
        _verify_database(destination_path)
    except Exception:
        if destination_path.exists():
            destination_path.unlink()
        raise
    return destination_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    backup_parser = subparsers.add_parser("backup")
    backup_parser.add_argument("--output", required=True, type=Path)
    restore_parser = subparsers.add_parser("restore")
    restore_parser.add_argument("--source", required=True, type=Path)
    restore_parser.add_argument("--destination", required=True, type=Path)
    arguments = parser.parse_args()

    if arguments.command == "backup":
        result = backup_database(arguments.output)
    else:
        result = restore_database(arguments.source, arguments.destination)
    print(f"Verified SQLite file: {result}")


if __name__ == "__main__":
    main()
