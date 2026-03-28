import httpx
import secrets
from typing import Optional
from fastapi import HTTPException, status

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# In-memory state store (use Redis in production)
_oauth_states: dict[str, str] = {}


class OAuthService:
    """
    Handles GitHub OAuth 2.0 Authorization Code Flow.
    Generates authorization URLs, exchanges codes for tokens,
    and manages state for CSRF protection.
    """

    def generate_auth_url(self, scopes: list[str] = None) -> dict:
        if not settings.GITHUB_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OAuth not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env",
            )

        state = secrets.token_urlsafe(32)
        _oauth_states[state] = "pending"

        scope_str = " ".join(scopes or ["repo", "read:user", "user:email"])

        auth_url = (
            f"{settings.GITHUB_OAUTH_URL}"
            f"?client_id={settings.GITHUB_CLIENT_ID}"
            f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
            f"&scope={scope_str}"
            f"&state={state}"
        )

        logger.info(f"Generated OAuth URL with state={state}")
        return {
            "authorization_url": auth_url,
            "state": state,
            "message": "Visit the authorization_url to authenticate with GitHub",
        }

    async def exchange_code_for_token(self, code: str, state: str) -> dict:
        if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OAuth not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env",
            )

        if state not in _oauth_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OAuth state. Possible CSRF attempt.",
            )

        del _oauth_states[state]

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(
                    settings.GITHUB_TOKEN_URL,
                    headers={"Accept": "application/json"},
                    data={
                        "client_id": settings.GITHUB_CLIENT_ID,
                        "client_secret": settings.GITHUB_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": settings.GITHUB_REDIRECT_URI,
                    },
                )
                data = response.json()
            except httpx.RequestError as e:
                logger.error(f"Error exchanging OAuth code: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to connect to GitHub for token exchange.",
                )

        if "error" in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub OAuth error: {data.get('error_description', data['error'])}",
            )

        access_token = data.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received from GitHub.",
            )

        logger.info("OAuth token exchange successful")
        return {
            "access_token": access_token,
            "token_type": data.get("token_type", "bearer"),
            "scope": data.get("scope", ""),
            "message": (
                "Authentication successful! Use the access_token as a "
                "Bearer token in the Authorization header."
            ),
        }


def get_oauth_service() -> OAuthService:
    return OAuthService()
