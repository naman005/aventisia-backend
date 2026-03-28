import httpx
from typing import Any, Dict, Optional
from fastapi import HTTPException, status

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class GitHubClient:
    """
    Core HTTP client for GitHub API interactions.
    Handles authentication headers, error translation, and request lifecycle.
    """

    def __init__(self, token: str):
        self.token = token
        self.base_url = settings.GITHUB_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Any:
        url = f"{self.base_url}{endpoint}"
        logger.info(f"GitHub API {method.upper()} {url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=json,
                )
                return self._handle_response(response)
            except httpx.TimeoutException:
                logger.error(f"Timeout calling GitHub API: {url}")
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="GitHub API request timed out. Please try again.",
                )
            except httpx.ConnectError:
                logger.error(f"Connection error calling GitHub API: {url}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unable to connect to GitHub API. Check your network.",
                )

    def _handle_response(self, response: httpx.Response) -> Any:
        logger.debug(f"GitHub API response status: {response.status_code}")

        if response.status_code == 204:
            return None

        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired GitHub token. Please re-authenticate.",
            )

        if response.status_code == 403:
            rate_limit_remaining = response.headers.get("X-RateLimit-Remaining", "N/A")
            if rate_limit_remaining == "0":
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="GitHub API rate limit exceeded. Please wait before retrying.",
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden. Check your token permissions.",
            )

        if response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GitHub resource not found. Verify the owner, repo, or resource ID.",
            )

        if response.status_code == 422:
            errors = response.json().get("errors", [])
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation error from GitHub: {errors}",
            )

        if not response.is_success:
            logger.error(f"GitHub API error {response.status_code}: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"GitHub API error: {response.text}",
            )

        try:
            return response.json()
        except Exception:
            return response.text

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, json: Optional[Dict] = None) -> Any:
        return await self._request("POST", endpoint, json=json)

    async def patch(self, endpoint: str, json: Optional[Dict] = None) -> Any:
        return await self._request("PATCH", endpoint, json=json)

    async def delete(self, endpoint: str) -> Any:
        return await self._request("DELETE", endpoint)
