import json
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import settings
from app.models.schemas import (
    TenantCreate, TenantUpdate, TenantOut, TenantProvisionResponse,
)
from app.services.db import public_conn
from app.services.provisioner import (
    provision_tenant, run_migrations, migrate_all_active,
)
from app.services.security import require_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _row_to_tenant(row) -> dict:
    d = dict(row)
    cfg = d.get("config")
    if isinstance(cfg, str):
        d["config"] = json.loads(cfg)
    elif cfg is None:
        d["config"] = {}
    return d


def _webhook_url(tenant_id: str) -> str:
    return f"{settings.PUBLIC_BASE_URL.rstrip('/')}/webhook/whatsapp/{tenant_id}"


@router.post("/tenants", response_model=TenantProvisionResponse,
             status_code=status.HTTP_201_CREATED)
async def create_tenant(body: TenantCreate):
    """Provision a new restaurant branch: insert registry row, create schema,
    run all migrations, seed empty menu. Zero code changes needed per branch."""
    async with public_conn() as conn:
        existing = await conn.fetchval(
            "SELECT 1 FROM tenants WHERE tenant_id=$1 OR whatsapp_number=$2;",
            body.tenant_id, body.whatsapp_number,
        )
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT,
                                "tenant_id or whatsapp_number already exists")
        row = await conn.fetchrow(
            """
            INSERT INTO tenants
              (tenant_id, name, branch_location, whatsapp_number, logo_url, config)
            VALUES ($1,$2,$3,$4,$5,$6::jsonb)
            RETURNING *;
            """,
            body.tenant_id, body.name, body.branch_location,
            body.whatsapp_number, body.logo_url, json.dumps(body.config),
        )

    # ── AUTO-PROVISION: create schema + migrations + seed menu ──
    migrations_applied = await provision_tenant(body.tenant_id)

    tenant = _row_to_tenant(row)
    return TenantProvisionResponse(
        **tenant,
        webhook_url=_webhook_url(body.tenant_id),
        migrations_applied=migrations_applied,
    )


@router.get("/tenants", response_model=list[TenantOut])
async def list_tenants(is_active: bool | None = Query(default=None)):
    sql = "SELECT * FROM tenants"
    args = []
    if is_active is not None:
        sql += " WHERE is_active = $1"
        args.append(is_active)
    sql += " ORDER BY created_at DESC;"
    async with public_conn() as conn:
        rows = await conn.fetch(sql, *args)
    return [_row_to_tenant(r) for r in rows]


@router.patch("/tenants/{tenant_id}", response_model=TenantOut)
async def update_tenant(tenant_id: str, body: TenantUpdate):
    fields, args, idx = [], [], 1
    data = body.model_dump(exclude_unset=True)
    for key, val in data.items():
        if key == "config":
            fields.append(f"config = ${idx}::jsonb")
            args.append(json.dumps(val))
        else:
            fields.append(f"{key} = ${idx}")
            args.append(val)
        idx += 1
    if not fields:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")
    args.append(tenant_id)
    sql = f"UPDATE tenants SET {', '.join(fields)} WHERE tenant_id = ${idx} RETURNING *;"
    async with public_conn() as conn:
        row = await conn.fetchrow(sql, *args)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found")
    return _row_to_tenant(row)


@router.delete("/tenants/{tenant_id}", response_model=TenantOut)
async def soft_delete_tenant(tenant_id: str):
    """Soft delete only — sets is_active=false, never drops the schema."""
    async with public_conn() as conn:
        row = await conn.fetchrow(
            "UPDATE tenants SET is_active=false WHERE tenant_id=$1 RETURNING *;",
            tenant_id,
        )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found")
    return _row_to_tenant(row)


@router.post("/tenants/{tenant_id}/migrate")
async def migrate_tenant(tenant_id: str):
    async with public_conn() as conn:
        exists = await conn.fetchval(
            "SELECT 1 FROM tenants WHERE tenant_id=$1;", tenant_id)
    if not exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found")
    applied = await run_migrations(tenant_id)
    return {"tenant_id": tenant_id, "migrations_applied": applied}


@router.post("/migrate-all")
async def migrate_all():
    result = await migrate_all_active()
    return {"results": result}
