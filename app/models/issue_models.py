from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class CreateIssueRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Bug: Login page crashes on Safari",
                "body": "## Description\nThe login page crashes when...\n\n## Steps to reproduce\n1. Open Safari\n2. Go to /login",
                "labels": ["bug", "frontend"],
                "assignees": ["octocat"],
            }
        }
    )

    title: str = Field(..., min_length=1, max_length=256, description="Issue title")
    body: Optional[str] = Field(None, description="Issue description (supports Markdown)")
    labels: Optional[list[str]] = Field(None, description="List of label names")
    assignees: Optional[list[str]] = Field(None, description="GitHub usernames to assign")
    milestone: Optional[int] = Field(None, description="Milestone number")


class UpdateIssueRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Updated issue title",
                "state": "closed",
                "labels": ["resolved"],
            }
        }
    )

    title: Optional[str] = Field(None, min_length=1, max_length=256)
    body: Optional[str] = None
    state: Optional[str] = Field(None, pattern="^(open|closed)$")
    labels: Optional[list[str]] = None
    assignees: Optional[list[str]] = None
    milestone: Optional[int] = None
