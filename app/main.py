from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager

from app.routers import repos, issues, pull_requests, commits, auth
from app.middleware.auth_middleware import AuthMiddleware
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("GitHub Connector API starting up...")
    yield
    logger.info("GitHub Connector API shutting down...")


app = FastAPI(
    title="GitHub Cloud Connector",
    description=(
        "A production-ready connector to GitHub's API supporting PAT and OAuth 2.0 authentication.\n\n"
        "**How to authenticate in this UI:**\n"
        "1. Click the **Authorize** button at the top right\n"
        "2. Paste your GitHub token in the **Bearer** field (e.g. `ghp_xxxx`)\n"
        "3. Click Authorize — all endpoints will now include your token automatically\n\n"
        "**No token?** Generate one at https://github.com/settings/tokens (scopes: `repo`, `read:user`)"
    ),
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "GitHub PAT or OAuth Token",
            "description": "Paste your GitHub Personal Access Token or OAuth token here.",
        }
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

app.include_router(auth.router, prefix="/auth", tags=["Authentication (OAuth 2.0)"])
app.include_router(repos.router, prefix="/repos", tags=["Repositories"])
app.include_router(issues.router, prefix="/issues", tags=["Issues"])
app.include_router(pull_requests.router, prefix="/pulls", tags=["Pull Requests"])
app.include_router(commits.router, prefix="/commits", tags=["Commits"])


@app.get("/", tags=["Health"])
async def root():
    return {"message": "GitHub Cloud Connector API", "version": "1.0.0", "docs": "/docs", "status": "healthy"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "github-connector"}
