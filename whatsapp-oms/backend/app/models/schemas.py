from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from pydantic import BaseModel, Field


# ─── Auth ───────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ─── Tenants ────────────────────────────────────────────────
class TenantCreate(BaseModel):
    tenant_id: str = Field(..., pattern=r"^[a-z0-9_]{1,50}$",
                           description="lowercase, digits, underscores")
    name: str
    branch_location: str
    whatsapp_number: str
    logo_url: Optional[str] = None
    config: dict[str, Any] = Field(default_factory=dict)


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    branch_location: Optional[str] = None
    whatsapp_number: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[dict[str, Any]] = None


class TenantOut(BaseModel):
    tenant_id: str
    name: Optional[str]
    branch_location: Optional[str]
    whatsapp_number: Optional[str]
    logo_url: Optional[str]
    is_active: bool
    created_at: datetime
    config: dict[str, Any]


class TenantProvisionResponse(TenantOut):
    webhook_url: str
    migrations_applied: list[str]


# ─── Menu ───────────────────────────────────────────────────
class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    category: str
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    category: Optional[str] = None
    is_available: Optional[bool] = None


class MenuItemOut(BaseModel):
    id: int
    name: Optional[str]
    description: Optional[str]
    price: Optional[Decimal]
    category: Optional[str]
    is_available: bool


# ─── Orders ─────────────────────────────────────────────────
class OrderStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|confirmed|preparing|delivered|cancelled)$")


class OrderOut(BaseModel):
    order_id: str
    customer_name: Optional[str]
    customer_phone: Optional[str]
    delivery_address: Optional[str]
    items: Any
    total_price: Optional[Decimal]
    status: str
    created_at: datetime


class CentralOrderOut(OrderOut):
    tenant_id: str
    tenant_name: Optional[str]
    branch_location: Optional[str]


# ─── Central stats ──────────────────────────────────────────
class TenantStats(BaseModel):
    tenant_id: str
    name: Optional[str]
    branch_location: Optional[str]
    is_active: bool
    orders_today: int
    revenue_today: Decimal
    orders_all_time: int
    revenue_all_time: Decimal
    last_order_at: Optional[datetime]


# ─── Webhook ────────────────────────────────────────────────
class WebhookTestMessage(BaseModel):
    """For local JSON testing of the webhook (alongside Twilio form posts)."""
    From: str
    Body: str
