"""
Schema creation + migration runner.

This module is invoked by POST /admin/tenants (see routers/admin.py) to
auto-provision a new tenant: create schema, run every migration, seed an
empty menu. It also powers the per-tenant and migrate-all endpoints.
"""
from app.services.db import (
    schema_name,
    public_conn,
    tenant_conn,
    MIGRATIONS,
)


async def create_schema(tenant_id: str) -> None:
    """Create the tenant's PostgreSQL schema if it does not exist."""
    sname = schema_name(tenant_id)  # validates tenant_id + builds name
    async with public_conn() as conn:
        await conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{sname}";')


async def _applied_migrations(conn) -> set[str]:
    # schema_migrations might not exist yet on a brand-new schema.
    exists = await conn.fetchval(
        """
        SELECT to_regclass(current_schema() || '.schema_migrations')
        """
    )
    if not exists:
        return set()
    rows = await conn.fetch("SELECT migration_name FROM schema_migrations;")
    return {r["migration_name"] for r in rows}


async def run_migrations(tenant_id: str) -> list[str]:
    """
    Apply only the migrations not yet recorded in this tenant's
    schema_migrations table. Returns the list of newly applied names.
    """
    applied_now: list[str] = []
    async with tenant_conn(tenant_id) as conn:
        # Ensure the migrations table itself exists first.
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              id SERIAL PRIMARY KEY,
              migration_name VARCHAR(100) UNIQUE,
              applied_at TIMESTAMP DEFAULT NOW()
            );
            """
        )
        already = await _applied_migrations(conn)

        for migration in MIGRATIONS:
            if migration["name"] in already:
                continue
            async with conn.transaction():
                await conn.execute(migration["sql"])
                await conn.execute(
                    "INSERT INTO schema_migrations (migration_name) VALUES ($1) "
                    "ON CONFLICT (migration_name) DO NOTHING;",
                    migration["name"],
                )
            applied_now.append(migration["name"])
    return applied_now


async def seed_empty_menu(tenant_id: str) -> None:
    """Default seed: nothing but an empty, ready-to-use menu table.
    (Table already created by migrations; this is a no-op placeholder that
    guarantees the menu exists and is empty for a fresh tenant.)"""
    async with tenant_conn(tenant_id) as conn:
        await conn.execute("SELECT 1 FROM menu_items LIMIT 0;")


async def provision_tenant(tenant_id: str) -> list[str]:
    """
    Full provisioning pipeline used by POST /admin/tenants:
      1. create schema
      2. run all migrations
      3. seed empty default menu
    Returns list of migrations applied.
    """
    await create_schema(tenant_id)
    applied = await run_migrations(tenant_id)
    await seed_empty_menu(tenant_id)
    return applied


async def migrate_all_active() -> dict[str, list[str]]:
    """Run pending migrations across every active tenant."""
    async with public_conn() as conn:
        rows = await conn.fetch(
            "SELECT tenant_id FROM tenants WHERE is_active = true;"
        )
    result: dict[str, list[str]] = {}
    for r in rows:
        result[r["tenant_id"]] = await run_migrations(r["tenant_id"])
    return result
