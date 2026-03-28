from pathlib import Path
from fastapi import APIRouter, Query, Depends
from fastapi.responses import HTMLResponse
from app.services.oauth_service import OAuthService, get_oauth_service

router = APIRouter()

TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "oauth_success.html"


@router.get(
    "/login",
    summary="Initiate OAuth 2.0 GitHub Login",
    description=(
        "Generates a GitHub OAuth authorization URL. "
        "Visit the returned URL in a browser to authenticate and grant permissions."
    ),
)
async def login(
    scopes: list[str] = Query(
        default=["repo", "read:user", "user:email"],
        description="GitHub OAuth scopes to request",
    ),
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    return oauth_service.generate_auth_url(scopes=scopes)


@router.get(
    "/callback",
    response_class=HTMLResponse,
    summary="OAuth 2.0 Callback — Exchange Code for Token",
    description="GitHub redirects here after authorization. Returns a page with your access token.",
)
async def callback(
    code: str = Query(..., description="Authorization code from GitHub"),
    state: str = Query(..., description="State token for CSRF validation"),
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    result = await oauth_service.exchange_code_for_token(code=code, state=state)
    token = result["access_token"]
    scope = result.get("scope", "")

    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = html.replace("{{ token }}", token).replace("{{ scope }}", scope)
    return HTMLResponse(content=html)
