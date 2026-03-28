from typing import Optional
from app.services.github_client import GitHubClient
from app.models.pr_models import CreatePRRequest, UpdatePRRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PullRequestService:
    """
    Service layer for GitHub Pull Request operations.
    Bonus feature: create, list, and manage PRs.
    """

    def __init__(self, client: GitHubClient):
        self.client = client

    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        sort: str = "created",
        direction: str = "desc",
        base: Optional[str] = None,
        head: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> dict:
        """List pull requests in a repository."""
        params = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": min(per_page, 100),
            "page": page,
        }
        if base:
            params["base"] = base
        if head:
            params["head"] = head

        logger.info(f"Listing PRs for {owner}/{repo} (state={state})")
        data = await self.client.get(f"/repos/{owner}/{repo}/pulls", params=params)
        prs = [self._format_pr(pr) for pr in data]
        return {"count": len(prs), "page": page, "per_page": per_page, "pull_requests": prs}

    async def get_pull_request(
        self, owner: str, repo: str, pr_number: int
    ) -> dict:
        """Get a specific pull request by number."""
        logger.info(f"Fetching PR #{pr_number} from {owner}/{repo}")
        data = await self.client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
        return self._format_pr(data, detailed=True)

    async def create_pull_request(
        self, owner: str, repo: str, payload: CreatePRRequest
    ) -> dict:
        """Create a new pull request."""
        body = {
            "title": payload.title,
            "head": payload.head,
            "base": payload.base,
        }
        if payload.body:
            body["body"] = payload.body
        if payload.draft is not None:
            body["draft"] = payload.draft

        logger.info(f"Creating PR in {owner}/{repo}: '{payload.title}' ({payload.head} -> {payload.base})")
        data = await self.client.post(f"/repos/{owner}/{repo}/pulls", json=body)
        return self._format_pr(data, detailed=True)

    async def update_pull_request(
        self, owner: str, repo: str, pr_number: int, payload: UpdatePRRequest
    ) -> dict:
        """Update an existing pull request."""
        body = payload.model_dump(exclude_none=True)
        logger.info(f"Updating PR #{pr_number} in {owner}/{repo}")
        data = await self.client.patch(
            f"/repos/{owner}/{repo}/pulls/{pr_number}", json=body
        )
        return self._format_pr(data, detailed=True)

    async def list_pr_files(self, owner: str, repo: str, pr_number: int) -> dict:
        """List files changed in a pull request."""
        logger.info(f"Fetching files for PR #{pr_number} in {owner}/{repo}")
        data = await self.client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}/files")
        files = [
            {
                "filename": f.get("filename"),
                "status": f.get("status"),
                "additions": f.get("additions"),
                "deletions": f.get("deletions"),
                "changes": f.get("changes"),
            }
            for f in data
        ]
        return {"count": len(files), "files": files}

    async def merge_pull_request(
        self, owner: str, repo: str, pr_number: int, commit_message: Optional[str] = None
    ) -> dict:
        """Merge a pull request."""
        body = {}
        if commit_message:
            body["commit_message"] = commit_message

        logger.info(f"Merging PR #{pr_number} in {owner}/{repo}")
        data = await self.client.post(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/merge", json=body
        )
        return {
            "merged": data.get("merged"),
            "message": data.get("message"),
            "sha": data.get("sha"),
        }

    def _format_pr(self, data: dict, detailed: bool = False) -> dict:
        base = {
            "id": data.get("id"),
            "number": data.get("number"),
            "title": data.get("title"),
            "state": data.get("state"),
            "draft": data.get("draft"),
            "url": data.get("html_url"),
            "user": data.get("user", {}).get("login"),
            "head": data.get("head", {}).get("ref"),
            "base": data.get("base", {}).get("ref"),
            "mergeable": data.get("mergeable"),
            "merged": data.get("merged"),
            "comments": data.get("comments"),
            "commits": data.get("commits"),
            "additions": data.get("additions"),
            "deletions": data.get("deletions"),
            "changed_files": data.get("changed_files"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "merged_at": data.get("merged_at"),
            "closed_at": data.get("closed_at"),
        }
        if detailed:
            base["body"] = data.get("body")
            base["labels"] = [l.get("name") for l in data.get("labels", [])]
            base["assignees"] = [a.get("login") for a in data.get("assignees", [])]
            base["requested_reviewers"] = [
                r.get("login") for r in data.get("requested_reviewers", [])
            ]
        return base
