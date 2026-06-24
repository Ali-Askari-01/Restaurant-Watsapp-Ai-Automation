import json
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.schemas import (
    MenuItemCreate, MenuItemUpdate, MenuItemOut,
    OrderOut, OrderStatusUpdate,
)
from app.services.db import tenant_conn, public_conn
from app.services.security import require_admin

router = APIRouter(prefix="/tenant", tags=["tenant"])


async def _tenant_exists(tenant_id: str) -> bool:
    async with public_conn() as conn:
        return bool(await conn.fetchval(
            "SELECT 1 FROM tenants WHERE tenant_id=$1;", tenant_id))


def _order_row(row) -> dict:
    d = dict(row)
    d["order_id"] = str(d["order_id"])
    if isinstance(d.get("items"), str):
        d["items"] = json.loads(d["items"])
    return d


# ─── Menu (public read, admin write) ────────────────────────
@router.get("/{tenant_id}/menu", response_model=list[MenuItemOut])
async def get_menu(tenant_id: str):
    if not await _tenant_exists(tenant_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found")
    async with tenant_conn(tenant_id) as conn:
        rows = await conn.fetch(
            "SELECT * FROM menu_items ORDER BY category, name;")
    return [dict(r) for r in rows]


@router.post("/{tenant_id}/menu", response_model=MenuItemOut,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
async def add_menu_item(tenant_id: str, body: MenuItemCreate):
    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            """INSERT INTO menu_items (name, description, price, category, is_available)
               VALUES ($1,$2,$3,$4,$5) RETURNING *;""",
            body.name, body.description, body.price, body.category, body.is_available,
        )
    return dict(row)


@router.patch("/{tenant_id}/menu/{item_id}", response_model=MenuItemOut,
              dependencies=[Depends(require_admin)])
async def edit_menu_item(tenant_id: str, item_id: int, body: MenuItemUpdate):
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")
    fields = [f"{k} = ${i+1}" for i, k in enumerate(data)]
    args = list(data.values()) + [item_id]
    sql = f"UPDATE menu_items SET {', '.join(fields)} WHERE id = ${len(args)} RETURNING *;"
    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(sql, *args)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    return dict(row)


@router.delete("/{tenant_id}/menu/{item_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_admin)])
async def delete_menu_item(tenant_id: str, item_id: int):
    async with tenant_conn(tenant_id) as conn:
        res = await conn.execute("DELETE FROM menu_items WHERE id=$1;", item_id)
    if res.endswith("0"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")


# ─── Orders ─────────────────────────────────────────────────
@router.get("/{tenant_id}/orders", response_model=list[OrderOut],
            dependencies=[Depends(require_admin)])
async def list_orders(
    tenant_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
):
    sql = "SELECT * FROM orders WHERE 1=1"
    args, idx = [], 1
    if status_filter:
        sql += f" AND status = ${idx}"; args.append(status_filter); idx += 1
    if date_from:
        sql += f" AND created_at >= ${idx}"; args.append(date_from); idx += 1
    if date_to:
        sql += f" AND created_at <= ${idx}"; args.append(date_to); idx += 1
    sql += " ORDER BY created_at DESC;"
    async with tenant_conn(tenant_id) as conn:
        rows = await conn.fetch(sql, *args)
    return [_order_row(r) for r in rows]


@router.get("/{tenant_id}/orders/{order_id}", response_model=OrderOut)
async def get_order(tenant_id: str, order_id: str):
    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            "SELECT * FROM orders WHERE order_id = $1;", order_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return _order_row(row)


@router.patch("/{tenant_id}/orders/{order_id}/status", response_model=OrderOut,
              dependencies=[Depends(require_admin)])
async def update_order_status(tenant_id: str, order_id: str, body: OrderStatusUpdate):
    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            "UPDATE orders SET status=$1 WHERE order_id=$2 RETURNING *;",
            body.status, order_id,
        )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    # Keep central log in sync.
    async with public_conn() as conn:
        await conn.execute(
            "UPDATE central_order_log SET status=$1 WHERE order_id=$2;",
            body.status, order_id,
        )
    return _order_row(row)


# ─── Public order tracker ────────────────────────────────────
@router.get("/{tenant_id}/track", response_model=OrderOut | None)
async def track_latest_order(tenant_id: str, phone: str = Query(...)):
    """Public: latest order for a phone number (read-only, no list exposure)."""
    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            "SELECT * FROM orders WHERE customer_phone=$1 "
            "ORDER BY created_at DESC LIMIT 1;", phone)
    return _order_row(row) if row else None
