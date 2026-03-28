from fastapi import APIRouter, Depends, Query, status
from typing import Optional

from app.dependencies import get_github_client
from app.services.github_client import GitHubClient
from app.services.issue_service import IssueService
from app.models.issue_models import CreateIssueRequest, UpdateIssueRequest

router = APIRouter()


def get_issue_service(client: GitHubClient = Depends(get_github_client)) -> IssueService:
    return IssueService(client)


@router.get(
    "/{owner}/{repo}",
    summary="List Issues",
    description="List issues in a repository. Supports filtering by state, labels, and assignee.",
)
async def list_issues(
    owner: str,
    repo: str,
    state: str = Query("open", description="Filter by state: open, closed, or all"),
    labels: Optional[str] = Query(None, description="Comma-separated label names"),
    assignee: Optional[str] = Query(None, description="Filter by assignee username"),
    sort: str = Query("created", description="Sort by: created, updated, comments"),
    direction: str = Query("desc", description="Sort direction: asc or desc"),
    per_page: int = Query(30, ge=1, le=100),
    page: int = Query(1, ge=1),
    service: IssueService = Depends(get_issue_service),
):
    return await service.list_issues(
        owner=owner,
        repo=repo,
        state=state,
        labels=labels,
        assignee=assignee,
        sort=sort,
        direction=direction,
        per_page=per_page,
        page=page,
    )


@router.get(
    "/{owner}/{repo}/{issue_number}",
    summary="Get a Specific Issue",
    description="Get detailed information about a single issue by its number.",
)
async def get_issue(
    owner: str,
    repo: str,
    issue_number: int,
    service: IssueService = Depends(get_issue_service),
):
    return await service.get_issue(owner=owner, repo=repo, issue_number=issue_number)


@router.post(
    "/{owner}/{repo}",
    status_code=status.HTTP_201_CREATED,
    summary="Create an Issue",
    description="Create a new issue in a repository. Requires write access.",
)
async def create_issue(
    owner: str,
    repo: str,
    payload: CreateIssueRequest,
    service: IssueService = Depends(get_issue_service),
):
    return await service.create_issue(owner=owner, repo=repo, payload=payload)


@router.patch(
    "/{owner}/{repo}/{issue_number}",
    summary="Update an Issue",
    description="Update an existing issue. Provide only the fields you want to change.",
)
async def update_issue(
    owner: str,
    repo: str,
    issue_number: int,
    payload: UpdateIssueRequest,
    service: IssueService = Depends(get_issue_service),
):
    return await service.update_issue(
        owner=owner, repo=repo, issue_number=issue_number, payload=payload
    )


@router.patch(
    "/{owner}/{repo}/{issue_number}/close",
    summary="Close an Issue",
    description="Shortcut to close a specific issue.",
)
async def close_issue(
    owner: str,
    repo: str,
    issue_number: int,
    service: IssueService = Depends(get_issue_service),
):
    return await service.close_issue(owner=owner, repo=repo, issue_number=issue_number)


@router.get(
    "/{owner}/{repo}/{issue_number}/comments",
    summary="List Issue Comments",
    description="List all comments on a specific issue.",
)
async def list_comments(
    owner: str,
    repo: str,
    issue_number: int,
    service: IssueService = Depends(get_issue_service),
):
    return await service.list_issue_comments(
        owner=owner, repo=repo, issue_number=issue_number
    )
