# Fake-Clock Harness (`tests/_fake_clock.py`)

Deterministic wall-clock control for time-dependent tests. Wraps
[`freezegun`](https://github.com/spulec/freezegun) and adds APScheduler
trigger integration. Introduced in T13.5.

## When to use

Use the harness when:

- You need `datetime.now(timezone.utc)` to return a fixed instant across
  multiple call sites that the test does not directly invoke (token
  TTLs, cooldowns, retention sweeps, stall detection).
- You need an APScheduler job to fire deterministically — e.g. asserting
  "after 23:59 on Sunday, the weekly review job runs".
- A test was previously stabilized with a `_NOW = datetime.now(...)`
  module-level constant. That pattern hides drift bugs; this harness
  replaces it.

Prefer the existing `now=` keyword injection (e.g.
`tokens.sign(..., now=...)`) for narrow expiry tests where the call
already accepts an injected clock.

## Canonical pattern

```python
from datetime import timedelta
from tests._fake_clock import freeze_time

def test_token_expires_after_24h(migrated_db, secret_env):
    with freeze_time("2026-04-19T12:00:00+00:00") as clock:
        token = export.sign_export_token("sess-1", archive_id="arc-1")
        clock.advance(timedelta(hours=25))
        with pytest.raises(export.ComplianceTokenError):
            export.verify_export_token(token, db_path=migrated_db)
```

## APScheduler integration

```python
with freeze_time("2026-04-19T23:58:00+00:00") as clock:
    sched = BackgroundScheduler(timezone=timezone.utc)
    sched.add_job(my_handler, CronTrigger(day_of_week="sun", hour=23, minute=59))
    clock.advance(120, scheduler=sched)  # crosses 23:59 — job runs
```

The scheduler is **not** started — jobs fire synchronously inside
`clock.advance(...)`. This keeps tests single-threaded and deterministic.

## What NOT to do

- **Do not import `tests/_fake_clock.py` from production code.** It is
  a test-only helper. Production code reads wall-clock; the harness
  patches it from the outside.
- **Do not mix `_NOW = datetime.now(...)` with the harness.** The
  module-level constant captures real time at import; pick one approach.
- **Do not call `clock.advance` outside the `freeze_time` context.** The
  controller raises `RuntimeError`.

## Dependency

`freezegun==1.5.5` (test-only — see `requirements.txt`).
