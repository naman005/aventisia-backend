from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.dependencies import get_github_client
from app.services.github_client import GitHubClient
from app.services.repo_service import RepoService

router = APIRouter()


def get_repo_service(client: GitHubClient = Depends(get_github_client)) -> RepoService:
    return RepoService(client)


@router.get(
    "",
    summary="List Repositories",
    description="List repositories for the authenticated user. Optionally filter by a specific GitHub username.",
)
async def list_repos(
    username: Optional[str] = Query(None, description="GitHub username. Omit for your own repos."),
    repo_type: str = Query("all", description="Filter by: all, owner, public, private, member"),
    sort: str = Query("updated", description="Sort by: created, updated, pushed, full_name"),
    direction: str = Query("desc", description="Sort direction: asc or desc"),
    per_page: int = Query(30, ge=1, le=100),
    page: int = Query(1, ge=1),
    service: RepoService = Depends(get_repo_service),
):
    return await service.list_user_repos(
        username=username,
        repo_type=repo_type,
        sort=sort,
        direction=direction,
        per_page=per_page,
        page=page,
    )


@router.get(
    "/org/{org}",
    summary="List Organization Repositories",
    description="List all repositories for a GitHub organization.",
)
async def list_org_repos(
    org: str,
    repo_type: str = Query("all", description="Filter by: all, public, private, forks, sources, member"),
    per_page: int = Query(30, ge=1, le=100),
    page: int = Query(1, ge=1),
    service: RepoService = Depends(get_repo_service),
):
    return await service.list_org_repos(org=org, repo_type=repo_type, per_page=per_page, page=page)


@router.get(
    "/{owner}/{repo}",
    summary="Get Repository Details",
    description="Get detailed information about a specific repository.",
)
async def get_repo(
    owner: str,
    repo: str,
    service: RepoService = Depends(get_repo_service),
):
    return await service.get_repo(owner=owner, repo=repo)


@router.get(
    "/{owner}/{repo}/languages",
    summary="Get Repository Languages",
    description="Get a breakdown of programming languages used in a repository.",
)
async def get_languages(
    owner: str,
    repo: str,
    service: RepoService = Depends(get_repo_service),
):
    return await service.get_repo_languages(owner=owner, repo=repo)
