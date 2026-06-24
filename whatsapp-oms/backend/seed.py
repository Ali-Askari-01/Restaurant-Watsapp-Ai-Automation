"""
Seed 3 sample branches of 'Burger Palace' each with a full menu.
Run after the API is up:  python seed.py
Uses the running API for tenant provisioning + direct DB for menu seeding.
"""
import asyncio
import json

from app.config import settings
from app.services.db import (
    init_pool, close_pool, init_public_schema, public_conn, tenant_conn,
)
from app.services.provisioner import provision_tenant

BRANCHES = [
    {
        "tenant_id": "burger_palace_clifton",
        "name": "Burger Palace",
        "branch_location": "Clifton, Karachi",
        "whatsapp_number": "+14155238801",
        "logo_url": "https://placehold.co/200x200?text=BP+Clifton",
        "config": {"currency": "PKR", "opening_hours": "11am-11pm", "delivery_radius_km": 5},
    },
    {
        "tenant_id": "burger_palace_dha",
        "name": "Burger Palace",
        "branch_location": "DHA, Karachi",
        "whatsapp_number": "+14155238802",
        "logo_url": "https://placehold.co/200x200?text=BP+DHA",
        "config": {"currency": "PKR", "opening_hours": "12pm-12am", "delivery_radius_km": 7},
    },
    {
        "tenant_id": "burger_palace_gulshan",
        "name": "Burger Palace",
        "branch_location": "Gulshan, Karachi",
        "whatsapp_number": "+14155238803",
        "logo_url": "https://placehold.co/200x200?text=BP+Gulshan",
        "config": {"currency": "PKR", "opening_hours": "11am-1am", "delivery_radius_km": 6},
    },
]

MENU = [
    ("Classic Beef Burger", "Juicy beef patty with lettuce, tomato & sauce", 650, "Burgers"),
    ("Cheese Burger", "Beef patty with melted cheddar", 750, "Burgers"),
    ("Double Patty Burger", "Two beef patties, double cheese", 1050, "Burgers"),
    ("Crispy Chicken Burger", "Fried chicken fillet with mayo", 700, "Burgers"),
    ("Zinger Burger", "Spicy crispy chicken with hot sauce", 780, "Burgers"),
    ("French Fries", "Golden crispy fries", 250, "Sides"),
    ("Loaded Fries", "Fries topped with cheese & jalapenos", 450, "Sides"),
    ("Chicken Wings (6pc)", "Buffalo style wings", 600, "Sides"),
    ("Soft Drink", "Chilled 345ml can", 120, "Drinks"),
    ("Chocolate Shake", "Thick creamy chocolate shake", 400, "Drinks"),
]


async def seed_menu(tenant_id: str):
    async with tenant_conn(tenant_id) as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM menu_items;")
        if count and count > 0:
            print(f"  menu already seeded for {tenant_id} ({count} items)")
            return
        for name, desc, price, cat in MENU:
            await conn.execute(
                "INSERT INTO menu_items (name, description, price, category) "
                "VALUES ($1,$2,$3,$4);",
                name, desc, price, cat,
            )
    print(f"  seeded {len(MENU)} menu items for {tenant_id}")


async def main():
    await init_pool()
    await init_public_schema()
    for b in BRANCHES:
        async with public_conn() as conn:
            exists = await conn.fetchval(
                "SELECT 1 FROM tenants WHERE tenant_id=$1;", b["tenant_id"])
            if not exists:
                await conn.execute(
                    """INSERT INTO tenants
                       (tenant_id,name,branch_location,whatsapp_number,logo_url,config)
                       VALUES ($1,$2,$3,$4,$5,$6::jsonb);""",
                    b["tenant_id"], b["name"], b["branch_location"],
                    b["whatsapp_number"], b["logo_url"], json.dumps(b["config"]),
                )
                print(f"created tenant {b['tenant_id']}")
            else:
                print(f"tenant {b['tenant_id']} already exists")
        await provision_tenant(b["tenant_id"])
        await seed_menu(b["tenant_id"])
    await close_pool()
    print("\n✅ Seed complete. Webhook URLs:")
    for b in BRANCHES:
        print(f"  {settings.PUBLIC_BASE_URL}/webhook/whatsapp/{b['tenant_id']}")


if __name__ == "__main__":
    asyncio.run(main())
