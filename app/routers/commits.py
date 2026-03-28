from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.dependencies import get_github_client
from app.services.github_client import GitHubClient
from app.services.commit_service import CommitService

router = APIRouter()


def get_commit_service(client: GitHubClient = Depends(get_github_client)) -> CommitService:
    return CommitService(client)


@router.get(
    "/{owner}/{repo}",
    summary="List Commits",
    description=(
        "List commits for a repository. Supports filtering by branch/SHA, "
        "file path, author, and date range (ISO 8601 format)."
    ),
)
async def list_commits(
    owner: str,
    repo: str,
    sha: Optional[str] = Query(None, description="Branch name or commit SHA to start from"),
    path: Optional[str] = Query(None, description="Only commits touching this file path"),
    author: Optional[str] = Query(None, description="GitHub username or email of author"),
    since: Optional[str] = Query(None, description="ISO 8601 date — only commits after this (e.g. 2024-01-01T00:00:00Z)"),
    until: Optional[str] = Query(None, description="ISO 8601 date — only commits before this"),
    per_page: int = Query(30, ge=1, le=100),
    page: int = Query(1, ge=1),
    service: CommitService = Depends(get_commit_service),
):
    return await service.list_commits(
        owner=owner,
        repo=repo,
        sha=sha,
        path=path,
        author=author,
        since=since,
        until=until,
        per_page=per_page,
        page=page,
    )


@router.get(
    "/{owner}/{repo}/{ref}",
    summary="Get a Specific Commit",
    description="Get full details of a commit by its SHA, including file changes and stats.",
)
async def get_commit(
    owner: str,
    repo: str,
    ref: str,
    service: CommitService = Depends(get_commit_service),
):
    return await service.get_commit(owner=owner, repo=repo, ref=ref)


@router.get(
    "/{owner}/{repo}/compare/{base}/{head}",
    summary="Compare Two Commits or Branches",
    description="Compare two commits, branches, or tags to see the diff and commits between them.",
)
async def compare_commits(
    owner: str,
    repo: str,
    base: str,
    head: str,
    service: CommitService = Depends(get_commit_service),
):
    return await service.compare_commits(owner=owner, repo=repo, base=base, head=head)
