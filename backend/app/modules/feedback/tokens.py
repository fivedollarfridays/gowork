"""Feedback token generation — URL-safe hashes for feedback URLs."""

import base64
import hashlib

from app.core.config import get_settings


def generate_token(session_id: str) -> str:
    """Generate a deterministic URL-safe token from a session ID.

    Returns a 12-char base64url string (no padding).
    """
    secret = get_settings().feedback_token_secret
    digest = hashlib.sha256(f"{session_id}:{secret}".encode()).digest()
    return base64.urlsafe_b64encode(digest)[:12].decode()
