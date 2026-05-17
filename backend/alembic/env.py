import asyncio
import os
from logging.config import fileConfig
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

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


database_url = os.environ.get("DATABASE_URL")
if database_url:
    database_url = _normalize_db_url(database_url)
    config.set_main_option("sqlalchemy.url", database_url)

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base
import app.models  # noqa: F401 — registers all models

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
