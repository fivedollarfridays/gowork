#!/usr/bin/env python3
"""Bridge Claude Code hook stdin-JSON to bpsai-pair commands.

WHY THIS EXISTS
---------------
Current Claude Code delivers hook event data as a JSON object on **stdin**,
not as environment variables. The legacy ``bpsai-pair init`` settings.json
template was written against an older contract and references shell vars like
``$CLAUDE_AGENT_ID``, ``$CLAUDE_TOOL_INPUT_file_path``, ``$CLAUDE_STOP_REASON``
and ``$CLAUDE_COMPACT_TRIGGER`` that no longer exist — they silently expand to
empty strings, so every wired hook fires with a hollow payload.

This script reads the stdin JSON, extracts the fields each bpsai-pair hook
command needs, and execs the command with them populated. It uses only the
Python standard library (no ``jq``), so it runs on machines that lack jq.

USAGE (from settings.json):
    python3 "$CLAUDE_PROJECT_DIR/scripts/cc_hook.py" <handler>

Set ``CC_HOOK_DRY_RUN=1`` to print the resolved argv as JSON instead of
executing it (used by the test suite).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# Handlers whose exit code must propagate (PreToolUse enforcement gates).
# Logging/telemetry handlers always exit 0 so they can never break a session.
_GATE_HANDLERS = {"containment-read", "containment-write", "task-edit", "state-edit"}


def _get(data: dict, path: str) -> str:
    """Return ``data`` at dotted ``path`` as a string, or "" if absent."""
    cur = data
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return ""
        cur = cur[key]
    if cur is None:
        return ""
    return cur if isinstance(cur, str) else str(cur)


def is_gate(handler: str) -> bool:
    """True if the handler is an enforcement gate (exit code must propagate)."""
    return handler in _GATE_HANDLERS


def build(handler: str, data: dict) -> list[str]:
    """Build the bpsai-pair argv for ``handler`` from the hook ``data``."""
    if handler in ("containment-read", "containment-write"):
        op = "read" if handler.endswith("read") else "write"
        return ["bpsai-pair", "enforce", "containment",
                "--file", _get(data, "tool_input.file_path"), "--operation", op]
    if handler in ("task-edit", "state-edit"):
        # Edit delivers tool_input.new_string; Write delivers tool_input.content.
        content = _get(data, "tool_input.new_string") + _get(data, "tool_input.content")
        return ["bpsai-pair", "enforce", handler,
                "--file", _get(data, "tool_input.file_path"), "--new-content", content]
    if handler == "compact":
        return ["bpsai-pair", "compaction", "snapshot", "save",
                "--trigger", _get(data, "trigger"), "--quiet"]
    if handler in ("teammate-idle", "task-completed"):
        event = "teammate_idle" if handler == "teammate-idle" else "task_completed"
        return ["bpsai-pair", "orchestrate", "evaluate", event,
                "--agent-id", _get(data, "agent_id"),
                "--agent-type", _get(data, "agent_type"), "--quiet"]
    if handler == "stop-failure":
        return ["bpsai-pair", "telemetry", "log-failure",
                "--trigger", _get(data, "error_type"), "--quiet"]
    if handler == "session-end":
        return ["bpsai-pair", "telemetry", "log-session-end",
                "--stop-reason", _get(data, "stop_reason"), "--quiet"]
    if handler == "subagent-stop":
        return ["bpsai-pair", "telemetry", "log-subagent-outcome",
                "--stop-reason", _get(data, "stop_reason"),
                "--agent-id", _get(data, "agent_id"),
                "--agent-type", _get(data, "agent_type"), "--quiet"]
    raise SystemExit(f"cc_hook: unknown handler '{handler}'")


def _load_stdin() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit("usage: cc_hook.py <handler>")
    handler = argv[1]
    cmd = build(handler, _load_stdin())

    if os.environ.get("CC_HOOK_DRY_RUN"):
        print(json.dumps(cmd))
        return 0

    try:
        result = subprocess.run(cmd)
    except OSError:
        # bpsai-pair not on PATH: never break the session on a telemetry hook,
        # and fail open on gates too (a missing CLI must not block all edits).
        return 0
    return result.returncode if is_gate(handler) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
