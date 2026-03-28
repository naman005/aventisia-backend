from typing import Optional
from app.services.github_client import GitHubClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CommitService:
    """
    Service layer for GitHub Commits operations.
    Supports listing commits with filtering by author, path, date range.
    """

    def __init__(self, client: GitHubClient):
        self.client = client

    async def list_commits(
        self,
        owner: str,
        repo: str,
        sha: Optional[str] = None,
        path: Optional[str] = None,
        author: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> dict:
        """
        List commits for a repository.
        Supports filtering by branch/sha, file path, author, and date range.
        """
        params: dict = {
            "per_page": min(per_page, 100),
            "page": page,
        }
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path
        if author:
            params["author"] = author
        if since:
            params["since"] = since
        if until:
            params["until"] = until

        logger.info(f"Fetching commits for {owner}/{repo}")
        data = await self.client.get(f"/repos/{owner}/{repo}/commits", params=params)
        commits = [self._format_commit(c) for c in data]
        return {
            "count": len(commits),
            "page": page,
            "per_page": per_page,
            "commits": commits,
        }

    async def get_commit(self, owner: str, repo: str, ref: str) -> dict:
        """Get a specific commit by SHA."""
        logger.info(f"Fetching commit {ref} from {owner}/{repo}")
        data = await self.client.get(f"/repos/{owner}/{repo}/commits/{ref}")
        return self._format_commit(data, detailed=True)

    async def compare_commits(
        self, owner: str, repo: str, base: str, head: str
    ) -> dict:
        """Compare two commits, branches, or tags."""
        logger.info(f"Comparing {base}...{head} in {owner}/{repo}")
        data = await self.client.get(f"/repos/{owner}/{repo}/compare/{base}...{head}")
        return {
            "status": data.get("status"),
            "ahead_by": data.get("ahead_by"),
            "behind_by": data.get("behind_by"),
            "total_commits": data.get("total_commits"),
            "commits": [self._format_commit(c) for c in data.get("commits", [])],
            "files_changed": len(data.get("files", [])),
        }

    def _format_commit(self, data: dict, detailed: bool = False) -> dict:
        commit_data = data.get("commit", {})
        author = commit_data.get("author", {})
        committer = commit_data.get("committer", {})

        base = {
            "sha": data.get("sha"),
            "short_sha": data.get("sha", "")[:7],
            "message": commit_data.get("message", "").split("\n")[0],  # first line only
            "author": {
                "name": author.get("name"),
                "email": author.get("email"),
                "date": author.get("date"),
                "username": data.get("author", {}).get("login") if data.get("author") else None,
            },
            "committer": {
                "name": committer.get("name"),
                "date": committer.get("date"),
            },
            "url": data.get("html_url"),
            "comment_count": commit_data.get("comment_count"),
        }

        if detailed:
            stats = data.get("stats", {})
            base["stats"] = {
                "additions": stats.get("additions"),
                "deletions": stats.get("deletions"),
                "total": stats.get("total"),
            }
            base["files"] = [
                {
                    "filename": f.get("filename"),
                    "status": f.get("status"),
                    "additions": f.get("additions"),
                    "deletions": f.get("deletions"),
                }
                for f in data.get("files", [])
            ]
            base["parents"] = [p.get("sha", "")[:7] for p in data.get("parents", [])]

        return base
