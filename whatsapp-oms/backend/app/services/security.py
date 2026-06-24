from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

bearer = HTTPBearer(auto_error=False)


def create_access_token(subject: str) -> tuple[str, int]:
    expire_seconds = settings.JWT_EXPIRY_HOURS * 3600
    expire = datetime.now(timezone.utc) + timedelta(seconds=expire_seconds)
    payload = {"sub": subject, "role": "admin", "exp": expire}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expire_seconds


def require_admin(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> str:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing token")
    try:
        payload = jwt.decode(
            creds.credentials, settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    if payload.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return payload["sub"]
