"""
Integration-style tests for the GitHub Connector API.
Uses pytest + httpx AsyncClient. Mocks GitHub API calls to avoid rate limits.
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app

BASE_HEADERS = {"Authorization": "Bearer ghp_test_token_1234567890"}

MOCK_REPO = {
    "id": 1,
    "name": "hello-world",
    "full_name": "octocat/hello-world",
    "description": "My first repo",
    "private": False,
    "html_url": "https://github.com/octocat/hello-world",
    "clone_url": "https://github.com/octocat/hello-world.git",
    "default_branch": "main",
    "stargazers_count": 10,
    "forks_count": 5,
    "open_issues_count": 2,
    "language": "Python",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "pushed_at": "2024-01-01T00:00:00Z",
}

MOCK_ISSUE = {
    "id": 101,
    "number": 1,
    "title": "Test Issue",
    "state": "open",
    "html_url": "https://github.com/octocat/hello-world/issues/1",
    "user": {"login": "octocat"},
    "labels": [],
    "assignees": [],
    "comments": 0,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "closed_at": None,
    "body": "This is a test issue",
    "milestone": None,
    "pull_request": None,  # not a PR
}


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_missing_auth_header():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/repos")
    assert response.status_code == 401
    assert "Authorization" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_repos():
    with patch("app.services.github_client.GitHubClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [MOCK_REPO]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/repos", headers=BASE_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert "repositories" in data
    assert data["count"] == 1
    assert data["repositories"][0]["name"] == "hello-world"


@pytest.mark.asyncio
async def test_get_specific_repo():
    detailed_repo = {**MOCK_REPO, "topics": ["python"], "license": {"name": "MIT"},
                     "size": 100, "watchers_count": 10, "has_issues": True,
                     "has_wiki": False, "archived": False, "disabled": False}
    with patch("app.services.github_client.GitHubClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = detailed_repo
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/repos/octocat/hello-world", headers=BASE_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "hello-world"
    assert "topics" in data


@pytest.mark.asyncio
async def test_list_issues():
    with patch("app.services.github_client.GitHubClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [MOCK_ISSUE]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/issues/octocat/hello-world", headers=BASE_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert "issues" in data
    assert data["count"] == 1
    assert data["issues"][0]["title"] == "Test Issue"


@pytest.mark.asyncio
async def test_create_issue():
    with patch("app.services.github_client.GitHubClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {**MOCK_ISSUE, "title": "New Bug Report"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/issues/octocat/hello-world",
                headers=BASE_HEADERS,
                json={"title": "New Bug Report", "body": "Found a bug!"},
            )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Bug Report"


@pytest.mark.asyncio
async def test_create_issue_missing_title():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/issues/octocat/hello-world",
            headers=BASE_HEADERS,
            json={"body": "No title provided"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_commits():
    mock_commit = {
        "sha": "abc123def456",
        "commit": {
            "message": "feat: Add new feature",
            "author": {"name": "Dev", "email": "dev@example.com", "date": "2024-01-01T00:00:00Z"},
            "committer": {"name": "Dev", "date": "2024-01-01T00:00:00Z"},
            "comment_count": 0,
        },
        "author": {"login": "dev"},
        "html_url": "https://github.com/octocat/hello-world/commit/abc123def456",
    }
    with patch("app.services.github_client.GitHubClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [mock_commit]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/commits/octocat/hello-world", headers=BASE_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["commits"][0]["short_sha"] == "abc123d"
