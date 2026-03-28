from typing import Optional
from app.services.github_client import GitHubClient
from app.models.issue_models import CreateIssueRequest, UpdateIssueRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)


class IssueService:
    """
    Service layer for GitHub Issues operations.
    Supports creating, listing, fetching, updating, and closing issues.
    """

    def __init__(self, client: GitHubClient):
        self.client = client

    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[str] = None,
        assignee: Optional[str] = None,
        sort: str = "created",
        direction: str = "desc",
        per_page: int = 30,
        page: int = 1,
    ) -> dict:
        """List issues in a repository with filtering support."""
        params = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": min(per_page, 100),
            "page": page,
        }
        if labels:
            params["labels"] = labels
        if assignee:
            params["assignee"] = assignee

        logger.info(f"Listing issues for {owner}/{repo} (state={state})")
        data = await self.client.get(f"/repos/{owner}/{repo}/issues", params=params)

        # GitHub returns PRs in issues endpoint — filter them out
        issues = [self._format_issue(i) for i in data if not i.get("pull_request")]
        return {
            "count": len(issues),
            "page": page,
            "per_page": per_page,
            "state_filter": state,
            "issues": issues,
        }

    async def get_issue(self, owner: str, repo: str, issue_number: int) -> dict:
        """Get a specific issue by number."""
        logger.info(f"Fetching issue #{issue_number} from {owner}/{repo}")
        data = await self.client.get(f"/repos/{owner}/{repo}/issues/{issue_number}")
        return self._format_issue(data, detailed=True)

    async def create_issue(
        self, owner: str, repo: str, payload: CreateIssueRequest
    ) -> dict:
        """Create a new issue in a repository."""
        body = {"title": payload.title}
        if payload.body:
            body["body"] = payload.body
        if payload.labels:
            body["labels"] = payload.labels
        if payload.assignees:
            body["assignees"] = payload.assignees
        if payload.milestone:
            body["milestone"] = payload.milestone

        logger.info(f"Creating issue in {owner}/{repo}: '{payload.title}'")
        data = await self.client.post(f"/repos/{owner}/{repo}/issues", json=body)
        return self._format_issue(data, detailed=True)

    async def update_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        payload: UpdateIssueRequest,
    ) -> dict:
        """Update an existing issue (title, body, state, labels, etc.)."""
        body = payload.model_dump(exclude_none=True)
        logger.info(f"Updating issue #{issue_number} in {owner}/{repo}")
        data = await self.client.patch(
            f"/repos/{owner}/{repo}/issues/{issue_number}", json=body
        )
        return self._format_issue(data, detailed=True)

    async def close_issue(self, owner: str, repo: str, issue_number: int) -> dict:
        """Close a specific issue."""
        logger.info(f"Closing issue #{issue_number} in {owner}/{repo}")
        data = await self.client.patch(
            f"/repos/{owner}/{repo}/issues/{issue_number}",
            json={"state": "closed"},
        )
        return self._format_issue(data, detailed=True)

    async def list_issue_comments(
        self, owner: str, repo: str, issue_number: int
    ) -> dict:
        """List comments on an issue."""
        logger.info(f"Fetching comments for issue #{issue_number} in {owner}/{repo}")
        data = await self.client.get(
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments"
        )
        comments = [
            {
                "id": c.get("id"),
                "user": c.get("user", {}).get("login"),
                "body": c.get("body"),
                "created_at": c.get("created_at"),
                "updated_at": c.get("updated_at"),
            }
            for c in data
        ]
        return {"count": len(comments), "comments": comments}

    def _format_issue(self, data: dict, detailed: bool = False) -> dict:
        base = {
            "id": data.get("id"),
            "number": data.get("number"),
            "title": data.get("title"),
            "state": data.get("state"),
            "url": data.get("html_url"),
            "user": data.get("user", {}).get("login"),
            "labels": [l.get("name") for l in data.get("labels", [])],
            "assignees": [a.get("login") for a in data.get("assignees", [])],
            "comments": data.get("comments"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "closed_at": data.get("closed_at"),
        }
        if detailed:
            base["body"] = data.get("body")
            base["milestone"] = (
                data.get("milestone", {}).get("title") if data.get("milestone") else None
            )
        return base
