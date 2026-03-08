"""Pydantic request/response models for the Barrier Intelligence chat API."""

from typing import Literal

from pydantic import BaseModel, field_validator

_ALLOWED_MODES = {"next_steps", "explain_plan"}


class ChatRequest(BaseModel):
    session_id: str
    user_question: str
    mode: Literal["next_steps", "explain_plan"]

    @field_validator("mode")
    @classmethod
    def mode_must_be_allowed(cls, v: str) -> str:
        if v not in _ALLOWED_MODES:
            raise ValueError(
                f"mode must be one of {sorted(_ALLOWED_MODES)}; "
                f"'what_if' is not supported in v1"
            )
        return v
