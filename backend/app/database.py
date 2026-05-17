from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def _normalize_db_url(url: str) -> str:
    from urllib.parse import urlparse, urlunparse, urlencode, parse_qs
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            url = "postgresql+asyncpg://" + url[len(prefix):]
            break
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    qs.pop("sslmode", None)
    new_query = urlencode({k: v[0] for k, v in qs.items()})
    return urlunparse(parsed._replace(query=new_query))


def _create_engine():
    from app.config import get_settings
    settings = get_settings()
    db_url = _normalize_db_url(settings.DATABASE_URL)
    return create_async_engine(
        db_url,
        echo=settings.ECHO_SQL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


class _DatabaseState:
    """Lazy-initialised engine and session factory.
    Engine is not created until the first database call so that settings are
    guaranteed to be fully loaded (especially in tests that swap DATABASE_URL).
    """

    def __init__(self):
        self._engine = None
        self._factory = None

    def _ensure(self):
        if self._engine is None:
            self._engine = _create_engine()
            self._factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

    def session(self) -> AsyncSession:
        self._ensure()
        return self._factory()


_state = _DatabaseState()

# Kept for compatibility with code that does `async with AsyncSessionLocal() as db:`
AsyncSessionLocal = _state.session


async def get_db() -> AsyncSession:
    async with _state.session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
