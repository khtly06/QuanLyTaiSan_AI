"""Tests for safe, non-overwriting SQLite backup and restore."""

import sqlite3

import pytest

from database.backup import backup_database, restore_database


def test_backup_and_restore_preserve_data(tmp_path):
    source = tmp_path / "live.db"
    backup = tmp_path / "backups" / "backup.db"
    restored = tmp_path / "recovery" / "restored.db"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE sample (value TEXT NOT NULL)")
        connection.execute("INSERT INTO sample VALUES ('preserved')")

    assert backup_database(backup, source) == backup.resolve()
    assert restore_database(backup, restored) == restored.resolve()

    with sqlite3.connect(restored) as connection:
        assert connection.execute("SELECT value FROM sample").fetchone()[0] == "preserved"
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_backup_and_restore_refuse_to_overwrite_existing_files(tmp_path):
    source = tmp_path / "source.db"
    destination = tmp_path / "existing.db"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE sample (value INTEGER)")
    destination.write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError):
        backup_database(destination, source)
    with pytest.raises(FileExistsError):
        restore_database(source, destination)
    assert destination.read_text(encoding="utf-8") == "keep"


def test_backup_refuses_source_as_its_own_destination(tmp_path):
    source = tmp_path / "source.db"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE sample (value INTEGER)")

    with pytest.raises(ValueError, match="differ"):
        backup_database(source, source)
