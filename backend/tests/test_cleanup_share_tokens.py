"""Tests verifying share_tokens are included in cleanup."""

from app.core.cleanup import _RELATED_TABLES


class TestCleanupIncludesShareTokens:
    """Verify share_tokens table is cleaned up with expired sessions."""

    def test_share_tokens_in_related_tables(self):
        """share_tokens must be in the cleanup related tables list."""
        assert "share_tokens" in _RELATED_TABLES, (
            "share_tokens must be included in _RELATED_TABLES "
            "to prevent expired tokens from accumulating."
        )
