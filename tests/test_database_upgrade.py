"""Tests for additive upgrades from the repository's prior SQLite schema."""

import sqlite3

from app import create_app
from app.models import db
from sqlalchemy import text


def test_startup_adds_workflow_columns_without_losing_existing_rows(tmp_path):
    database_path = tmp_path / "old-schema.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT NOT NULL
            );
            INSERT INTO users VALUES
                (1, 'existing', 'existing@example.invalid', 'hash', 'staff', 'Existing');
            CREATE TABLE inventory (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                status TEXT
            );
            CREATE TABLE inventory_details (
                id INTEGER PRIMARY KEY,
                inventory_id INTEGER NOT NULL,
                asset_id INTEGER NOT NULL,
                expected_status TEXT,
                actual_status TEXT,
                variance_note TEXT
            );
            CREATE TABLE repairs (
                id INTEGER PRIMARY KEY,
                asset_id INTEGER NOT NULL,
                request_date DATE NOT NULL,
                repair_date DATE,
                status TEXT,
                description TEXT NOT NULL,
                cost FLOAT,
                notes TEXT
            );
            CREATE TABLE disposals (
                id INTEGER PRIMARY KEY,
                asset_id INTEGER NOT NULL,
                disposal_date DATE NOT NULL,
                reason TEXT NOT NULL,
                liquidation_value FLOAT,
                status TEXT
            );
            CREATE TABLE transfers (
                id INTEGER PRIMARY KEY,
                asset_id INTEGER NOT NULL,
                from_department_id INTEGER NOT NULL,
                to_department_id INTEGER NOT NULL,
                transfer_date DATE NOT NULL,
                reason TEXT,
                notes TEXT
            );
            """
        )

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "upgrade-test-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
            "SEED_DEMO_DATA": False,
        }
    )

    with app.app_context():
        assert db.session.execute(
            text("SELECT username FROM users WHERE id = 1")
        ).scalar_one() == "existing"
        assert db.session.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        inspector = db.inspect(db.engine)
        assert {
            "created_by"
        }.issubset({column["name"] for column in inspector.get_columns("inventory")})
        assert {"checked_by", "checked_at"}.issubset(
            {column["name"] for column in inspector.get_columns("inventory_details")}
        )
        assert "inventory_observations" in inspector.get_table_names()
        assert {"requested_by", "updated_by"}.issubset(
            {column["name"] for column in inspector.get_columns("repairs")}
        )
        assert {"requested_by", "decided_by", "decided_at"}.issubset(
            {column["name"] for column in inspector.get_columns("disposals")}
        )
        assert "performed_by" in {
            column["name"] for column in inspector.get_columns("transfers")
        }
