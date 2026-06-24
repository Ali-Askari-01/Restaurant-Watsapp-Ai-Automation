import json
from fastapi import APIRouter, Depends, Query

from app.models.schemas import CentralOrderOut, TenantStats
from app.services.db import public_conn
from app.services.security import require_admin

router = APIRouter(prefix="/central", tags=["central"],
                   dependencies=[Depends(require_admin)])


@router.get("/orders", response_model=list[CentralOrderOut])
async def central_orders(
    tenant_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
):
    """Aggregated orders across all tenants, read from the central log."""
    sql = "SELECT * FROM central_order_log WHERE 1=1"
    args, idx = [], 1
    if tenant_id:
        sql += f" AND tenant_id = ${idx}"; args.append(tenant_id); idx += 1
    if status:
        sql += f" AND status = ${idx}"; args.append(status); idx += 1
    if date_from:
        sql += f" AND created_at >= ${idx}"; args.append(date_from); idx += 1
    if date_to:
        sql += f" AND created_at <= ${idx}"; args.append(date_to); idx += 1
    sql += " ORDER BY created_at DESC;"
    async with public_conn() as conn:
        rows = await conn.fetch(sql, *args)

    out = []
    for r in rows:
        out.append(CentralOrderOut(
            order_id=str(r["order_id"]),
            customer_name=r["customer_name"],
            customer_phone=r["customer_phone"],
            delivery_address=None,
            items=[],
            total_price=r["total_price"],
            status=r["status"],
            created_at=r["created_at"],
            tenant_id=r["tenant_id"],
            tenant_name=r["tenant_name"],
            branch_location=r["branch_location"],
        ))
    return out


@router.get("/tenants/stats", response_model=list[TenantStats])
async def tenant_stats():
    """Per-tenant aggregates from the central log. Fully dynamic — any new
    tenant appears here automatically the moment its first order logs."""
    sql = """
    SELECT
      t.tenant_id, t.name, t.branch_location, t.is_active,
      COALESCE(SUM(CASE WHEN l.created_at::date = CURRENT_DATE THEN 1 ELSE 0 END),0) AS orders_today,
      COALESCE(SUM(CASE WHEN l.created_at::date = CURRENT_DATE THEN l.total_price ELSE 0 END),0) AS revenue_today,
      COALESCE(COUNT(l.order_id),0) AS orders_all_time,
      COALESCE(SUM(l.total_price),0) AS revenue_all_time,
      MAX(l.created_at) AS last_order_at
    FROM tenants t
    LEFT JOIN central_order_log l ON l.tenant_id = t.tenant_id
    GROUP BY t.tenant_id, t.name, t.branch_location, t.is_active
    ORDER BY t.created_at DESC;
    """
    async with public_conn() as conn:
        rows = await conn.fetch(sql)
    return [
        TenantStats(
            tenant_id=r["tenant_id"], name=r["name"],
            branch_location=r["branch_location"], is_active=r["is_active"],
            orders_today=r["orders_today"], revenue_today=r["revenue_today"],
            orders_all_time=r["orders_all_time"], revenue_all_time=r["revenue_all_time"],
            last_order_at=r["last_order_at"],
        ) for r in rows
    ]
