---
name: MontGoWork project security profile
description: Key security-relevant facts about the montgowork codebase — stack, patterns, and standing risk areas
type: project
---

Python/FastAPI backend with SQLAlchemy async ORM, Pydantic settings, React frontend.

Key security posture facts:
- `.env` is gitignored; secrets consumed via `pydantic_settings` / env vars — correct pattern.
- `backend/app/core/config.py` has production-time validators for weak salt, short admin key, localhost CORS, and private-IP credit URLs. These guards are well-implemented.
- `.paircoder/license.json` is gitignored (added 2026-04-11 during S1 review pass). Prior to that, it was tracked on the `engage/backlog-sprint-s1-city-framework-scaffold` branch — removed via `git filter-branch` before merge.
- `deploy.sh` is gitignored (added 2026-04-11). Previously leaked `/home/kmasty/` WSL paths; removed via same filter-branch rewrite.
- YAML loading in `backend/app/cities/config.py` uses `yaml.safe_load` — safe against deserialization attacks.
- `load_city_config(city)` validates `city` against `^[a-z][a-z0-9-]{0,49}$` and applies `is_relative_to(CITIES_DIR)` before opening the file. `Settings.city` has a matching `@field_validator` so the env var cannot hold an unsafe value. Path traversal fully mitigated as of S1 review pass (2026-04-11).
- Adapter registry in `backend/app/integrations/adapters/base.py` uses a hardcoded allow-list dict for `importlib` imports — the lazy-import pattern is safe; no user-controlled import paths.
- SQL in `brightdata_adapter.py` uses SQLAlchemy `text()` with named bind parameters — no string interpolation, no SQL injection risk.
- `bypass_log.jsonl` is tracked in git and contains task IDs and `--allow-dirty` bypass reasons — no secrets, but audit trail is in version control.

**Why:** First full audit of this branch. Useful for future audits of same codebase.
**How to apply:** Use as baseline when auditing future branches. Check whether .gitignore has been updated for license.json and deploy.sh.
