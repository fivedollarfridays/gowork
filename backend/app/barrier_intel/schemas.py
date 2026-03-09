"""Request/response schemas for barrier intelligence chat."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request for barrier intelligence assistant."""

    session_id: str = Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    user_question: str = Field(..., min_length=1, max_length=1000)
    mode: Literal["next_steps", "explain_plan"]
