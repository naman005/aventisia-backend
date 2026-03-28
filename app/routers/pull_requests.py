from fastapi import APIRouter, Depends, Query, status
from typing import Optional

from app.dependencies import get_github_client
from app.services.github_client import GitHubClient
from app.services.pr_service import PullRequestService
from app.models.pr_models import CreatePRRequest, UpdatePRRequest

router = APIRouter()


def get_pr_service(client: GitHubClient = Depends(get_github_client)) -> PullRequestService:
    return PullRequestService(client)


@router.get(
    "/{owner}/{repo}",
    summary="List Pull Requests",
    description="List pull requests in a repository with filtering support.",
)
async def list_pull_requests(
    owner: str,
    repo: str,
    state: str = Query("open", description="Filter by state: open, closed, or all"),
    sort: str = Query("created", description="Sort by: created, updated, popularity, long-running"),
    direction: str = Query("desc"),
    base: Optional[str] = Query(None, description="Filter by base branch name"),
    head: Optional[str] = Query(None, description="Filter by head branch (user:branch)"),
    per_page: int = Query(30, ge=1, le=100),
    page: int = Query(1, ge=1),
    service: PullRequestService = Depends(get_pr_service),
):
    return await service.list_pull_requests(
        owner=owner,
        repo=repo,
        state=state,
        sort=sort,
        direction=direction,
        base=base,
        head=head,
        per_page=per_page,
        page=page,
    )


@router.get(
    "/{owner}/{repo}/{pr_number}",
    summary="Get a Pull Request",
    description="Get detailed information about a specific pull request.",
)
async def get_pull_request(
    owner: str,
    repo: str,
    pr_number: int,
    service: PullRequestService = Depends(get_pr_service),
):
    return await service.get_pull_request(owner=owner, repo=repo, pr_number=pr_number)


@router.post(
    "/{owner}/{repo}",
    status_code=status.HTTP_201_CREATED,
    summary="Create a Pull Request",
    description=(
        "Create a new pull request. The `head` branch must exist in the repository "
        "and contain commits not in the `base` branch."
    ),
)
async def create_pull_request(
    owner: str,
    repo: str,
    payload: CreatePRRequest,
    service: PullRequestService = Depends(get_pr_service),
):
    return await service.create_pull_request(owner=owner, repo=repo, payload=payload)


@router.patch(
    "/{owner}/{repo}/{pr_number}",
    summary="Update a Pull Request",
    description="Update an existing pull request. Provide only the fields you want to change.",
)
async def update_pull_request(
    owner: str,
    repo: str,
    pr_number: int,
    payload: UpdatePRRequest,
    service: PullRequestService = Depends(get_pr_service),
):
    return await service.update_pull_request(
        owner=owner, repo=repo, pr_number=pr_number, payload=payload
    )


@router.get(
    "/{owner}/{repo}/{pr_number}/files",
    summary="List PR Files",
    description="List all files changed in a pull request.",
)
async def list_pr_files(
    owner: str,
    repo: str,
    pr_number: int,
    service: PullRequestService = Depends(get_pr_service),
):
    return await service.list_pr_files(owner=owner, repo=repo, pr_number=pr_number)


@router.post(
    "/{owner}/{repo}/{pr_number}/merge",
    summary="Merge a Pull Request",
    description="Merge a pull request. Requires write access and the PR must be mergeable.",
)
async def merge_pull_request(
    owner: str,
    repo: str,
    pr_number: int,
    commit_message: Optional[str] = Query(None, description="Custom commit message for the merge"),
    service: PullRequestService = Depends(get_pr_service),
):
    return await service.merge_pull_request(
        owner=owner, repo=repo, pr_number=pr_number, commit_message=commit_message
    )
