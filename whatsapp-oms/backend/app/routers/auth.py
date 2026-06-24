from fastapi import APIRouter, HTTPException, status

from app.config import settings
from app.models.schemas import LoginRequest, TokenResponse
from app.services.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    if body.email != settings.ADMIN_EMAIL or body.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    token, expires_in = create_access_token(body.email)
    return TokenResponse(access_token=token, expires_in=expires_in)
