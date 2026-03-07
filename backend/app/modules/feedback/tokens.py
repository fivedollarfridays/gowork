"""Feedback token generation — cryptographically random URL-safe tokens."""

import secrets


def generate_token() -> str:
    """Generate a random URL-safe token (16 chars, 96 bits of entropy)."""
    return secrets.token_urlsafe(12)
