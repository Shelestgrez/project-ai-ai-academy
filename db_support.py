from __future__ import annotations

import os
import sqlite3
from typing import Optional, Tuple, Type

from flask import Flask, current_app, g

try:
    import psycopg2
    from psycopg2 import errors as pg_errors
except ImportError:  # pragma: no cover - local optional
    psycopg2 = None
    pg_errors = None


def database_url() -> Optional[str]:
    url = os.environ.get("DATABASE_URL")
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def _integrity_errors() -> Tuple[Type[BaseException], ...]:
    errs: list[Type[BaseException]] = [sqlite3.IntegrityError]
    if psycopg2 is not None and pg_errors is not None:
        errs.append(pg_errors.UniqueViolation)
    return tuple(errs)


INTEGRITY_ERRORS: Tuple[Type[BaseException], ...] = _integrity_errors()


def attach_database(app: Flask, sqlite_path: str) -> None:
    url = database_url()
    app.config["DB_BACKEND"] = "postgres" if url else "sqlite"
    app.config["DATABASE_URL"] = url
    app.config["SQLITE_PATH"] = sqlite_path
    app.teardown_appcontext(close_db)


def close_db(_e=None) -> None:
    wrapper: ConnWrapper | None = g.pop("_dbw", None)
    if wrapper is not None:
        wrapper.close()


class ConnWrapper:
    __slots__ = ("_conn", "_backend")

    def __init__(self, conn, backend: str) -> None:
        self._conn = conn
        self._backend = backend

    def execute(self, query: str, params=()):
        q = query.replace("?", "%s") if self._backend == "postgres" else query
        cur = self._conn.cursor()
        cur.execute(q, tuple(params) if params is not None else ())
        return cur

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


def get_db() -> ConnWrapper:
    if "_dbw" not in g:
        backend = current_app.config["DB_BACKEND"]
        if backend == "postgres":
            if psycopg2 is None:
                raise RuntimeError("psycopg2 is required when DATABASE_URL is set")
            from psycopg2.extras import RealDictCursor

            raw = psycopg2.connect(
                current_app.config["DATABASE_URL"],
                cursor_factory=RealDictCursor,
            )
        else:
            raw = sqlite3.connect(current_app.config["SQLITE_PATH"])
            raw.row_factory = sqlite3.Row
        g._dbw = ConnWrapper(raw, backend)
    return g._dbw


def init_schema(app: Flask) -> None:
    backend = app.config["DB_BACKEND"]
    if backend == "sqlite":
        _init_sqlite(app.config["SQLITE_PATH"])
        return
    _init_postgres(app.config["DATABASE_URL"])


def _init_sqlite(path: str) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lesson_id TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            quiz_score INTEGER NOT NULL DEFAULT 0,
            total_questions INTEGER NOT NULL DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, lesson_id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(progress)").fetchall()}
    if "quiz_score" not in columns:
        conn.execute("ALTER TABLE progress ADD COLUMN quiz_score INTEGER NOT NULL DEFAULT 0")
    if "total_questions" not in columns:
        conn.execute("ALTER TABLE progress ADD COLUMN total_questions INTEGER NOT NULL DEFAULT 0")
    conn.commit()
    conn.close()


def _init_postgres(dsn: str) -> None:
    if psycopg2 is None:
        raise RuntimeError("psycopg2 is required when DATABASE_URL is set")
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS progress (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            lesson_id TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            quiz_score INTEGER NOT NULL DEFAULT 0,
            total_questions INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, lesson_id)
        );
        """
    )
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'progress'
        """
    )
    cols = {r[0] for r in cur.fetchall()}
    if "quiz_score" not in cols:
        cur.execute("ALTER TABLE progress ADD COLUMN quiz_score INTEGER NOT NULL DEFAULT 0")
    if "total_questions" not in cols:
        cur.execute("ALTER TABLE progress ADD COLUMN total_questions INTEGER NOT NULL DEFAULT 0")
    conn.commit()
    cur.close()
    conn.close()
