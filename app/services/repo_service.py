from typing import Optional
from app.services.github_client import GitHubClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RepoService:
    """
    Service layer for GitHub repository operations.
    Encapsulates all repo-related API calls and data transformations.
    """

    def __init__(self, client: GitHubClient):
        self.client = client

    async def list_user_repos(
        self,
        username: Optional[str] = None,
        repo_type: str = "all",
        sort: str = "updated",
        direction: str = "desc",
        per_page: int = 30,
        page: int = 1,
    ) -> dict:
        """List repositories for authenticated user or a specific user."""
        params = {
            "type": repo_type,
            "sort": sort,
            "direction": direction,
            "per_page": min(per_page, 100),
            "page": page,
        }

        if username:
            endpoint = f"/users/{username}/repos"
            logger.info(f"Fetching repos for user: {username}")
        else:
            endpoint = "/user/repos"
            logger.info("Fetching repos for authenticated user")

        data = await self.client.get(endpoint, params=params)

        repos = [self._format_repo(r) for r in data]
        return {
            "count": len(repos),
            "page": page,
            "per_page": per_page,
            "repositories": repos,
        }

    async def list_org_repos(
        self,
        org: str,
        repo_type: str = "all",
        per_page: int = 30,
        page: int = 1,
    ) -> dict:
        """List repositories for a GitHub organization."""
        params = {"type": repo_type, "per_page": min(per_page, 100), "page": page}
        logger.info(f"Fetching repos for org: {org}")
        data = await self.client.get(f"/orgs/{org}/repos", params=params)
        repos = [self._format_repo(r) for r in data]
        return {"count": len(repos), "page": page, "per_page": per_page, "repositories": repos}

    async def get_repo(self, owner: str, repo: str) -> dict:
        """Get details of a specific repository."""
        logger.info(f"Fetching repo: {owner}/{repo}")
        data = await self.client.get(f"/repos/{owner}/{repo}")
        return self._format_repo(data, detailed=True)

    async def get_repo_languages(self, owner: str, repo: str) -> dict:
        """Get programming languages used in a repository."""
        logger.info(f"Fetching languages for {owner}/{repo}")
        return await self.client.get(f"/repos/{owner}/{repo}/languages")

    def _format_repo(self, data: dict, detailed: bool = False) -> dict:
        base = {
            "id": data.get("id"),
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "private": data.get("private"),
            "url": data.get("html_url"),
            "clone_url": data.get("clone_url"),
            "default_branch": data.get("default_branch"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "language": data.get("language"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "pushed_at": data.get("pushed_at"),
        }
        if detailed:
            base.update({
                "topics": data.get("topics", []),
                "license": data.get("license", {}).get("name") if data.get("license") else None,
                "size": data.get("size"),
                "watchers": data.get("watchers_count"),
                "has_issues": data.get("has_issues"),
                "has_wiki": data.get("has_wiki"),
                "archived": data.get("archived"),
                "disabled": data.get("disabled"),
            })
        return base
