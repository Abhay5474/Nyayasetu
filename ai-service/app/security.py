import hmac

from fastapi import Depends, Header, HTTPException, status

from app.config import Settings, get_settings


def require_internal_token(
    x_internal_token: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Service-to-service auth: only the Spring Boot gateway knows the shared token."""
    if not x_internal_token or not hmac.compare_digest(x_internal_token, settings.internal_token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid internal token")
