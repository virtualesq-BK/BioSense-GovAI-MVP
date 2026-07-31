import pytest

from biosense.infrastructure.database import to_asyncpg_url


def test_to_asyncpg_url_from_postgresql() -> None:
    assert (
        to_asyncpg_url("postgresql://user:pass@host:5432/db")
        == "postgresql+asyncpg://user:pass@host:5432/db"
    )


def test_to_asyncpg_url_from_postgres_scheme() -> None:
    assert (
        to_asyncpg_url("postgres://user:pass@host:5432/db")
        == "postgresql+asyncpg://user:pass@host:5432/db"
    )


def test_to_asyncpg_url_passthrough() -> None:
    url = "postgresql+asyncpg://user:pass@host:5432/db"
    assert to_asyncpg_url(url) == url
