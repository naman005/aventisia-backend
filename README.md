# GitHub Cloud Connector

A production-ready REST API connector for the GitHub API built with **Python + FastAPI**.

Supports **Personal Access Token (PAT)** and **OAuth 2.0** authentication, and exposes clean, documented endpoints for managing repositories, issues, pull requests, and commits.

---

## Features

| Category | Feature |
|---|---|
| Auth | PAT (Bearer token) + OAuth 2.0 Authorization Code Flow |
| Repos | List user/org repos, get repo details, get language breakdown |
| Issues | List, get, create, update, close issues + list comments |
| Pull Requests | List, get, create, update, merge PRs + list changed files |
| Commits | List, get, compare commits with filtering by author/date/path |
| Security | Token never hardcoded; CSRF protection via OAuth state; middleware auth |
| Errors | Structured error handling for 401, 403, 404, 422, 429, 504 |
| Docs | Auto-generated Swagger UI + ReDoc |
| Tests | Async test suite with mocked GitHub API calls |

---

## Project Structure

```
github-connector/
├── app/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── config.py                # Settings via pydantic-settings + .env
│   ├── dependencies.py          # FastAPI dependency injection
│   ├── middleware/
│   │   └── auth_middleware.py   # Bearer token extraction middleware
│   ├── models/
│   │   ├── issue_models.py      # Pydantic request/response models for issues
│   │   └── pr_models.py         # Pydantic models for pull requests
│   ├── routers/
│   │   ├── auth.py              # OAuth 2.0 login + callback endpoints
│   │   ├── repos.py             # Repository endpoints
│   │   ├── issues.py            # Issue endpoints
│   │   ├── pull_requests.py     # Pull request endpoints (bonus)
│   │   └── commits.py           # Commit endpoints
│   ├── services/
│   │   ├── github_client.py     # Core async HTTP client for GitHub API
│   │   ├── oauth_service.py     # OAuth 2.0 flow logic
│   │   ├── repo_service.py      # Repository business logic
│   │   ├── issue_service.py     # Issue business logic
│   │   ├── pr_service.py        # Pull request business logic
│   │   └── commit_service.py    # Commit business logic
│   └── utils/
│       └── logger.py            # Structured logger
├── tests/
│   └── test_api.py              # Async integration tests
├── .env.example                 # Environment variable template
├── .gitignore
├── pyproject.toml               # pytest configuration
├── requirements.txt
└── README.md
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- A GitHub account
- A GitHub Personal Access Token (PAT)


### Step 1 — Clone and enter the project

```bash
git clone <your-repo-url>
cd github-connector
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set your token:

```env
GITHUB_TOKEN=ghp_your_personal_access_token_here
GITHUB_CLIENT_ID=your_oauth_app_client_id
GITHUB_CLIENT_SECRET=your_oauth_app_client_secret
```

**How to generate a PAT:**
1. Go to → https://github.com/settings/tokens
2. Click **Generate new token (classic)**
3. Select scopes: `repo`, `read:user`, `user:email`
4. Copy the token and paste it as `GITHUB_TOKEN` in `.env`

### Step 4 — Run the server

```bash
uvicorn app.main:app --reload
```

The API is now running at → **http://localhost:8000**

**Swagger UI**: http://localhost:8000/docs

---

### Step 5 — Run tests

```bash
pytest -v
```

---

## Authentication

### Option A — PAT (Personal Access Token)

Pass your GitHub token as a Bearer token in every request header:

```
Authorization: Bearer ghp_your_token_here
```

### Option B — OAuth 2.0

> Requires `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in `.env`

1. **Initiate login** → `GET /auth/login`
   - Returns an `authorization_url`
2. **Visit the URL** in your browser and authorize the app
3. **GitHub redirects** to `/auth/callback?code=...&state=...`
4. The callback returns an `access_token`
5. **Use it as Bearer token** in subsequent requests

---

## API Endpoints

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |

---

### Authentication (OAuth 2.0)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/login` | Generate GitHub OAuth authorization URL |
| GET | `/auth/callback` | Exchange OAuth code for access token |

---

### Repositories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/repos` | List repos for authenticated user |
| GET | `/repos?username={user}` | List repos for a specific GitHub user |
| GET | `/repos/org/{org}` | List repos for an organization |
| GET | `/repos/{owner}/{repo}` | Get repo details |
| GET | `/repos/{owner}/{repo}/languages` | Get language breakdown |

---

### Issues

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/issues/{owner}/{repo}` | List issues (filter by state, labels, assignee) |
| GET | `/issues/{owner}/{repo}/{number}` | Get a specific issue |
| POST | `/issues/{owner}/{repo}` | Create a new issue |
| PATCH | `/issues/{owner}/{repo}/{number}` | Update an issue |
| PATCH | `/issues/{owner}/{repo}/{number}/close` | Close an issue |
| GET | `/issues/{owner}/{repo}/{number}/comments` | List issue comments |

---

### Pull Requests *(Bonus)*

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pulls/{owner}/{repo}` | List PRs (filter by state, base, head) |
| GET | `/pulls/{owner}/{repo}/{number}` | Get a specific PR |
| POST | `/pulls/{owner}/{repo}` | Create a new PR |
| PATCH | `/pulls/{owner}/{repo}/{number}` | Update a PR |
| GET | `/pulls/{owner}/{repo}/{number}/files` | List files changed in a PR |
| POST | `/pulls/{owner}/{repo}/{number}/merge` | Merge a PR |

---

### Commits

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/commits/{owner}/{repo}` | List commits (filter by author, path, date) |
| GET | `/commits/{owner}/{repo}/{sha}` | Get a specific commit |
| GET | `/commits/{owner}/{repo}/compare/{base}/{head}` | Compare two branches/SHAs |

---

##  Postman Testing Guide

### Setup

1. Open Postman
2. Create a new collection: **GitHub Cloud Connector**
3. Add a **Collection Variable**:
   - Key: `base_url` → Value: `http://localhost:8000`
   - Key: `token` → Value: `ghp_your_token_here`
4. In the collection's **Authorization** tab, set:
   - Type: `Bearer Token`
   - Token: `{{token}}`

All requests in the collection will inherit this auth header.
