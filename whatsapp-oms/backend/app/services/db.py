"""
Multi-schema connection manager + migration definitions.

RULE: Schema names are constructed ONLY in this module. No other file in the
codebase builds a `tenant_*` schema string. Every tenant-scoped query must go
through `get_tenant_connection()` or `tenant_conn()` so that `search_path`
is always set correctly before any query runs.
"""
import re
import asyncpg
from contextlib import asynccontextmanager
from typing import Optional

from app.config import settings

_pool: Optional[asyncpg.Pool] = None

# Only allow safe identifiers; prevents SQL injection via tenant_id.
_TENANT_ID_RE = re.compile(r"^[a-z0-9_]{1,50}$")


def schema_name(tenant_id: str) -> str:
    """The single source of truth for turning a tenant_id into a schema name."""
    if not _TENANT_ID_RE.match(tenant_id):
        raise ValueError(
            f"Invalid tenant_id '{tenant_id}'. "
            "Use lowercase letters, digits and underscores only."
        )
    return f"tenant_{tenant_id}"


# ──────────────────────────────────────────────────────────────────────────
# Pool lifecycle
# ──────────────────────────────────────────────────────────────────────────
async def init_pool() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            settings.DATABASE_URL, min_size=1, max_size=10, timeout=10
        )


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialised. Call init_pool() on startup.")
    return _pool


# ──────────────────────────────────────────────────────────────────────────
# Connections
# ──────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def public_conn():
    """Connection scoped to the public (central) schema."""
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute("SET search_path TO public")
        yield conn


@asynccontextmanager
async def tenant_conn(tenant_id: str):
    """
    Context-managed tenant connection. Sets search_path to the tenant's
    schema (with public as fallback for gen_random_uuid etc.) for the
    lifetime of the borrowed connection, then resets it on release.
    """
    sname = schema_name(tenant_id)
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(f'SET search_path TO "{sname}", public')
        try:
            yield conn
        finally:
            # Reset so a recycled pooled connection never leaks a search_path.
            await conn.execute("SET search_path TO public")


async def get_tenant_connection(tenant_id: str) -> asyncpg.Connection:
    """
    Spec-required helper. Returns a *standalone* connection (not pooled) with
    search_path already set. Caller is responsible for closing it.
    Prefer `tenant_conn()` (context manager) in application code.
    """
    sname = schema_name(tenant_id)
    conn = await asyncpg.connect(settings.DATABASE_URL)
    await conn.execute(f'SET search_path TO "{sname}", public')
    return conn


# ──────────────────────────────────────────────────────────────────────────
# Public schema bootstrap (tenant registry + central log)
# ──────────────────────────────────────────────────────────────────────────
PUBLIC_DDL = [
    """
    CREATE TABLE IF NOT EXISTS public.tenants (
      tenant_id VARCHAR(50) PRIMARY KEY,
      name VARCHAR(100),
      branch_location VARCHAR(100),
      whatsapp_number VARCHAR(20) UNIQUE,
      logo_url TEXT,
      is_active BOOLEAN DEFAULT true,
      created_at TIMESTAMP DEFAULT NOW(),
      config JSONB DEFAULT '{}'
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS public.central_order_log (
      log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id VARCHAR(50),
      tenant_name VARCHAR(100),
      branch_location VARCHAR(100),
      order_id UUID,
      customer_name VARCHAR(100),
      customer_phone VARCHAR(20),
      total_price DECIMAL(10,2),
      status VARCHAR(20),
      created_at TIMESTAMP
    );
    """,
]


async def init_public_schema() -> None:
    async with public_conn() as conn:
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
        for ddl in PUBLIC_DDL:
            await conn.execute(ddl)


# ──────────────────────────────────────────────────────────────────────────
# Per-tenant migrations (ordered). Add new entries at the END only.
# Each migration runs with search_path already pointed at the tenant schema,
# so DDL is unqualified and lands inside the correct schema.
# ──────────────────────────────────────────────────────────────────────────
MIGRATIONS: list[dict] = [
    {
        "name": "0001_create_menu_items",
        "sql": """
            CREATE TABLE IF NOT EXISTS menu_items (
              id SERIAL PRIMARY KEY,
              name VARCHAR(100),
              description TEXT,
              price DECIMAL(10,2),
              category VARCHAR(50),
              is_available BOOLEAN DEFAULT true
            );
        """,
    },
    {
        "name": "0002_create_orders",
        "sql": """
            CREATE TABLE IF NOT EXISTS orders (
              order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
              customer_name VARCHAR(100),
              customer_phone VARCHAR(20),
              delivery_address TEXT,
              items JSONB,
              total_price DECIMAL(10,2),
              status VARCHAR(20) DEFAULT 'pending',
              created_at TIMESTAMP DEFAULT NOW()
            );
        """,
    },
    {
        "name": "0003_create_conversations",
        "sql": """
            CREATE TABLE IF NOT EXISTS conversations (
              id SERIAL PRIMARY KEY,
              customer_phone VARCHAR(20) UNIQUE,
              context JSONB,
              last_updated TIMESTAMP DEFAULT NOW()
            );
        """,
    },
    {
        "name": "0004_create_schema_migrations",
        "sql": """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              id SERIAL PRIMARY KEY,
              migration_name VARCHAR(100) UNIQUE,
              applied_at TIMESTAMP DEFAULT NOW()
            );
        """,
    },
]
