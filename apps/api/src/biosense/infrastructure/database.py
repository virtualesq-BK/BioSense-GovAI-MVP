def to_asyncpg_url(database_url: str) -> str:
    """Normalize Postgres connection strings for SQLAlchemy asyncpg."""
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url
