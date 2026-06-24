from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.db import init_pool, close_pool, init_public_schema
from app.routers import auth, admin, tenant, webhook, central


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging

    log = logging.getLogger("uvicorn.error")
    try:
        await init_pool()
        await init_public_schema()
    except Exception as exc:
        log.warning(
            "Database unavailable at startup (%s). Login works; dashboard needs PostgreSQL.",
            exc,
        )
    yield
    try:
        await close_pool()
    except Exception:
        pass


app = FastAPI(title="WhatsApp AI Order Management System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(tenant.router)
app.include_router(webhook.router)
app.include_router(central.router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "whatsapp-ai-oms"}
