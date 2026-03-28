from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


# Routes that do NOT require a GitHub token
PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/auth/login",
    "/auth/callback",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts the GitHub token from the Authorization header
    and makes it available in request.state for downstream handlers.

    Supports both:
        - PAT:   Authorization: Bearer ghp_xxxxxxxxxxxx
        - OAuth: Authorization: Bearer gho_xxxxxxxxxxxx
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS or request.url.path.startswith("/docs"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": (
                        "Authorization header is required. "
                        "Use: Authorization: Bearer <your_github_token>"
                    )
                },
            )

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                status_code=401,
                content={
                    "detail": (
                        "Invalid Authorization header format. "
                        "Expected: Authorization: Bearer <token>"
                    )
                },
            )

        token = parts[1]
        if not token or len(token) < 10:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token appears invalid. Please provide a valid GitHub token."},
            )

        request.state.github_token = token
        return await call_next(request)
