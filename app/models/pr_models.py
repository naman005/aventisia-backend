from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class CreatePRRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "feat: Add user authentication",
                "head": "feature/auth",
                "base": "main",
                "body": "## Changes\n- Added JWT authentication\n- Added login/logout endpoints\n\n## Testing\n- Unit tests added",
                "draft": False,
            }
        }
    )

    title: str = Field(..., min_length=1, max_length=256, description="PR title")
    head: str = Field(..., description="Branch name containing changes (e.g. 'feature/my-feature')")
    base: str = Field(..., description="Branch to merge into (e.g. 'main')")
    body: Optional[str] = Field(None, description="PR description (supports Markdown)")
    draft: Optional[bool] = Field(False, description="Create as draft PR")


class UpdatePRRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "feat: Add user authentication [UPDATED]",
                "state": "closed",
            }
        }
    )

    title: Optional[str] = Field(None, min_length=1, max_length=256)
    body: Optional[str] = None
    state: Optional[str] = Field(None, pattern="^(open|closed)$")
    base: Optional[str] = None
