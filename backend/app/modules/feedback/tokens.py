"""Feedback token generation — cryptographically random URL-safe tokens."""

import secrets


def generate_token(session_id: str) -> str:
    """Generate a random URL-safe token (16 chars, ~96 bits of entropy).

    The session_id parameter is accepted for interface compatibility but
    tokens are non-deterministic — each call produces a unique token.
    """
    return secrets.token_urlsafe(16)[:16]
