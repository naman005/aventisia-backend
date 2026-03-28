from fastapi import Request, HTTPException, status
from app.services.github_client import GitHubClient
from app.config import get_settings

settings = get_settings()


def get_github_client(request: Request) -> GitHubClient:
    """
    FastAPI dependency: resolves the GitHub token from one of two sources (in priority order):
    1. Authorization header (set by AuthMiddleware on request.state)
    2. GITHUB_TOKEN environment variable (fallback for local dev / server-side PAT)
    """
    token = getattr(request.state, "github_token", None)

    if not token:
        token = settings.GITHUB_TOKEN

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "No GitHub token found. "
                "Provide via 'Authorization: Bearer <token>' header "
                "or set GITHUB_TOKEN in your .env file."
            ),
        )

    return GitHubClient(token=token)
