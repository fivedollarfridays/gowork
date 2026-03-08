"""Request/response schemas for barrier intelligence chat."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request for barrier intelligence assistant."""

    session_id: str
    user_question: str = Field(..., min_length=1, max_length=1000)
    mode: Literal["next_steps", "explain_plan"]
