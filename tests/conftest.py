from __future__ import annotations

import os

import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_PATH"] = str(db_path)
    os.environ.pop("DATABASE_URL", None)

    application = create_app()
    application.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
        }
    )
    yield application

    if "DATABASE_PATH" in os.environ:
        del os.environ["DATABASE_PATH"]


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_client(client):
    client.post(
        "/register?lang=ru",
        data={
            "name": "Test User",
            "email": "student@academy.test",
            "password": "test-pass-123",
        },
        follow_redirects=True,
    )
    client.post(
        "/login?lang=ru",
        data={"email": "student@academy.test", "password": "test-pass-123"},
        follow_redirects=True,
    )
    return client
