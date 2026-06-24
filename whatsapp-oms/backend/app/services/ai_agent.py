"""
GPT-4o conversational order-taking agent.

Conversation state is held in an in-memory dict keyed by
(tenant_id, customer_phone). The model is steered with a tool/JSON contract:
it returns a reply message plus a structured `order` block once the customer
confirms, so we can deterministically create the order.
"""
import json
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from app.services.db import tenant_conn, public_conn

# In-memory sessions: { (tenant_id, phone): {"messages": [...], "cart": [...] } }
_SESSIONS: dict[tuple[str, str], dict] = {}

_openai_client = None
if settings.OPENAI_API_KEY:
    try:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception as e:  # pragma: no cover
        print(f"[ai_agent] OpenAI init failed: {e}")
        _openai_client = None


def _session_key(tenant_id: str, phone: str) -> tuple[str, str]:
    return (tenant_id, phone)


def get_session(tenant_id: str, phone: str) -> dict:
    key = _session_key(tenant_id, phone)
    if key not in _SESSIONS:
        _SESSIONS[key] = {"messages": [], "cart": []}
    return _SESSIONS[key]


def reset_session(tenant_id: str, phone: str) -> None:
    _SESSIONS.pop(_session_key(tenant_id, phone), None)


async def _load_tenant(tenant_id: str) -> Optional[dict]:
    async with public_conn() as conn:
        row = await conn.fetchrow(
            "SELECT tenant_id, name, branch_location, config "
            "FROM tenants WHERE tenant_id = $1 AND is_active = true;",
            tenant_id,
        )
    return dict(row) if row else None


async def _load_menu(tenant_id: str) -> list[dict]:
    async with tenant_conn(tenant_id) as conn:
        rows = await conn.fetch(
            "SELECT id, name, description, price, category "
            "FROM menu_items WHERE is_available = true ORDER BY category, name;"
        )
    return [dict(r) for r in rows]


def _menu_text(menu: list[dict], currency: str) -> str:
    if not menu:
        return "(No items available right now.)"
    by_cat: dict[str, list[dict]] = {}
    for m in menu:
        by_cat.setdefault(m["category"] or "Other", []).append(m)
    lines = []
    for cat, items in by_cat.items():
        lines.append(f"\n*{cat}*")
        for it in items:
            lines.append(
                f"  [{it['id']}] {it['name']} — {currency} {it['price']}"
                + (f" — {it['description']}" if it.get("description") else "")
            )
    return "\n".join(lines)


def _build_system_prompt(tenant: dict, menu: list[dict]) -> str:
    cfg = tenant.get("config") or {}
    if isinstance(cfg, str):
        cfg = json.loads(cfg)
    currency = cfg.get("currency", "PKR")
    hours = cfg.get("opening_hours", "not specified")
    return f"""You are the friendly WhatsApp ordering assistant for \
"{tenant['name']}" ({tenant['branch_location']} branch).

Opening hours: {hours}. Currency: {currency}.

Your ONLY job is to take food orders. Do not answer unrelated questions or
provide general support — politely redirect to ordering.

CURRENT MENU (use these exact item ids, names and prices):
{_menu_text(menu, currency)}

RULES:
1. Greet the customer warmly on first contact and offer to share the menu.
2. Help them add/remove items and answer price questions from the menu above.
3. Only sell items that exist on the menu. Never invent items or prices.
4. Before confirming, you MUST collect: customer name, delivery address, and
   phone number.
5. Show a clear itemised order summary with line totals and a grand total,
   then ask for explicit confirmation ("yes" / "confirm").
6. Compute totals using the menu prices and quantities.

OUTPUT FORMAT — respond with STRICT JSON only, no markdown:
{{
  "reply": "<the message to send the customer>",
  "order_ready": <true|false>,
  "order": {{
     "customer_name": "...",
     "customer_phone": "...",
     "delivery_address": "...",
     "items": [{{"item_id": 1, "name": "Burger", "qty": 2, "price": 500}}],
     "total_price": 1000
  }} | null
}}

Set "order_ready" to true ONLY after the customer has explicitly confirmed AND
name, phone and address are all collected. Otherwise set it false and "order"
to null. Always keep "reply" conversational and human."""


def _fallback_response(tenant: dict, menu: list[dict], user_text: str) -> dict:
    """Used when OpenAI is not configured — keeps the demo functional."""
    cfg = tenant.get("config") or {}
    if isinstance(cfg, str):
        cfg = json.loads(cfg)
    currency = cfg.get("currency", "PKR")
    reply = (
        f"Hi! Welcome to {tenant['name']} ({tenant['branch_location']}). "
        f"Here's our menu:\n{_menu_text(menu, currency)}\n\n"
        "(AI is in demo mode — set OPENAI_API_KEY to enable full ordering.)"
    )
    return {"reply": reply, "order_ready": False, "order": None}


async def handle_message(tenant_id: str, phone: str, text: str) -> dict:
    """
    Process one inbound customer message. Returns:
      {"reply": str, "order_created": bool, "order_id": str|None}
    """
    tenant = await _load_tenant(tenant_id)
    if not tenant:
        return {"reply": "Sorry, this restaurant is not available.",
                "order_created": False, "order_id": None}

    menu = await _load_menu(tenant_id)
    session = get_session(tenant_id, phone)
    session["messages"].append({"role": "user", "content": text})

    if _openai_client is None:
        result = _fallback_response(tenant, menu, text)
    else:
        system_prompt = _build_system_prompt(tenant, menu)
        messages = [{"role": "system", "content": system_prompt}] + session["messages"]
        try:
            completion = _openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.4,
            )
            raw = completion.choices[0].message.content
            result = json.loads(raw)
        except Exception as e:
            print(f"[ai_agent] OpenAI error: {e}")
            result = _fallback_response(tenant, menu, text)

    reply = result.get("reply", "Sorry, could you repeat that?")
    session["messages"].append({"role": "assistant", "content": reply})

    order_created = False
    order_id = None
    if result.get("order_ready") and result.get("order"):
        order_id = await _create_order(tenant, result["order"])
        order_created = True
        reset_session(tenant_id, phone)

    return {"reply": reply, "order_created": order_created, "order_id": order_id}


async def _create_order(tenant: dict, order: dict) -> str:
    tenant_id = tenant["tenant_id"]
    items = order.get("items", [])
    total = order.get("total_price") or sum(
        float(i.get("price", 0)) * int(i.get("qty", 1)) for i in items
    )
    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO orders
              (customer_name, customer_phone, delivery_address, items,
               total_price, status)
            VALUES ($1, $2, $3, $4::jsonb, $5, 'pending')
            RETURNING order_id, created_at;
            """,
            order.get("customer_name"),
            order.get("customer_phone"),
            order.get("delivery_address"),
            json.dumps(items),
            total,
        )
    order_id = str(row["order_id"])

    # Mirror to central log (public schema).
    async with public_conn() as conn:
        await conn.execute(
            """
            INSERT INTO central_order_log
              (tenant_id, tenant_name, branch_location, order_id,
               customer_name, customer_phone, total_price, status, created_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,'pending',$8);
            """,
            tenant_id,
            tenant["name"],
            tenant["branch_location"],
            row["order_id"],
            order.get("customer_name"),
            order.get("customer_phone"),
            total,
            row["created_at"],
        )
    return order_id
