# WhatsApp AI Order Management System (Multi-Tenant)

A schema-per-tenant SaaS that lets a restaurant chain run a WhatsApp AI ordering
bot per branch, all monitored from one central dashboard. **Adding a new branch
requires zero code changes** — one API call (or dashboard form) provisions a new
schema, runs all migrations, and the branch instantly appears in the dashboard
and gets its own webhook URL.

## Stack

FastAPI · PostgreSQL (multi-schema) · React (Vite) + Tailwind · OpenAI GPT-4o ·
Twilio WhatsApp (mockable) · JWT auth · raw SQL via `asyncpg` (no ORM).

## Architecture

- Each branch = one tenant = one PostgreSQL schema `tenant_<tenant_id>`.
- A shared `public` schema holds the tenant registry (`tenants`) and the
  aggregation layer (`central_order_log`).
- The central dashboard reads only from `public` — never from tenant schemas.
- All schema names are built in exactly one place: `app/services/db.py`.
  Every tenant query runs through `tenant_conn()`, which sets `search_path`
  before any query and resets it on release.

## Prerequisites

- Python 3.11+
- Node 18+
- PostgreSQL 14+ (needs `pgcrypto` for `gen_random_uuid()` — auto-created on boot)

## Backend Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in DATABASE_URL, JWT_SECRET, OPENAI_API_KEY
createdb whatsapp_oms         # or create the DB however you prefer
uvicorn app.main:app --reload --port 8000
```

On startup the app creates the `public` schema tables automatically.

### Seed 3 sample branches

```bash
python seed.py
```

Creates `burger_palace_clifton`, `burger_palace_dha`, `burger_palace_gulshan`,
each provisioned (schema + migrations) with a 10-item menu.

## Frontend Setup

```bash
cd frontend
cp .env.example .env          # VITE_API_URL=http://localhost:8000
npm install
npm run dev                   # http://localhost:5173
```

- Dashboard: `http://localhost:5173/login` (use ADMIN_EMAIL / ADMIN_PASSWORD)
- Branch site: `http://localhost:5173/branch/burger_palace_clifton`

## Provisioning a New Branch (Zero Code Changes)

### Via API

```bash
TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@burgerpalace.com","password":"admin123"}' | jq -r .access_token)

curl -X POST localhost:8000/admin/tenants \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{
    "tenant_id":"burger_palace_saddar",
    "name":"Burger Palace",
    "branch_location":"Saddar, Karachi",
    "whatsapp_number":"+14155238804",
    "logo_url":"https://placehold.co/200x200",
    "config":{"currency":"PKR","opening_hours":"11am-11pm","delivery_radius_km":5}
  }'
```

The response includes the new `webhook_url` and the migrations applied. The
branch is now live in the dashboard's Branches Overview immediately.

### Via Dashboard

Login → **Add New Branch** → fill the form → submit. The new branch card
appears under **Branches Overview** with no redeploy.

## Running Migrations on Existing Tenants

When you add a new entry to `MIGRATIONS` in `db.py`:

```bash
# one tenant
curl -X POST localhost:8000/admin/tenants/burger_palace_clifton/migrate \
  -H "Authorization: Bearer $TOKEN"

# all active tenants
curl -X POST localhost:8000/admin/migrate-all -H "Authorization: Bearer $TOKEN"
```

## Testing the WhatsApp Webhook Locally

### Quick JSON test (no Twilio)

```bash
curl -X POST localhost:8000/webhook/whatsapp/burger_palace_clifton \
  -H 'Content-Type: application/json' \
  -d '{"From":"whatsapp:+923001234567","Body":"Hi, I want to order"}'
```

The JSON response contains the AI `reply`. If `OPENAI_API_KEY` is unset, a demo
fallback returns the menu. If Twilio creds are unset, the outbound send is
printed to the server console.

### With Twilio + ngrok

```bash
ngrok http 8000
```

In the Twilio WhatsApp Sandbox console, set the inbound webhook to:

```
https://<your-ngrok-id>.ngrok-free.app/webhook/whatsapp/<tenant_id>
```

Point each branch's number/sandbox to its own `tenant_id` URL — one route
pattern serves every tenant.

## Sample curl Commands

```bash
# Login
curl -X POST localhost:8000/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"owner@burgerpalace.com","password":"admin123"}'

# List tenants
curl localhost:8000/admin/tenants -H "Authorization: Bearer $TOKEN"

# Public menu
curl localhost:8000/tenant/burger_palace_clifton/menu

# Add menu item (admin)
curl -X POST localhost:8000/tenant/burger_palace_clifton/menu \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"Veggie Burger","price":600,"category":"Burgers"}'

# Central aggregated orders
curl "localhost:8000/central/orders?status=pending" \
  -H "Authorization: Bearer $TOKEN"

# Per-tenant stats
curl localhost:8000/central/tenants/stats -H "Authorization: Bearer $TOKEN"

# Update order status
curl -X PATCH localhost:8000/tenant/burger_palace_clifton/orders/<order_id>/status \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"status":"preparing"}'

# Soft-delete a branch (preserves schema + data)
curl -X DELETE localhost:8000/admin/tenants/burger_palace_dha \
  -H "Authorization: Bearer $TOKEN"
```

## MVP Constraints

No payments, no email/SMS, AI scope is order-taking only, sessions are in-memory
(keyed by `(tenant_id, customer_phone)`), raw SQL (no SQLAlchemy), FastAPI only.
