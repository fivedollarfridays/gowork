# T13.95 — SSRF Surface Full Sweep

**Sprint:** S13
**Method:** Grep `backend/app/` for `httpx.*`, `requests.*`, `urlopen`, `aiohttp`, `HTML(url=...)`; classify each fetch site by input source.
**Generated:** 2026-04-25
**Cross-reference:** T13.56 (PDF SSRF fuzz — 56 cases against `pdf_renderer._deny_all_url_fetcher`)

## URL-fetch site inventory

| # | Site | File:line | Input source | Worker-controllable? | Protection |
|---|------|-----------|--------------|---------------------|------------|
| 1 | WeasyPrint URL fetcher | `core/pdf_renderer.py:163-178` (`HTML(string=..., url_fetcher=_deny_all_url_fetcher)`) | none — uses `string=` not `url=` | indirect (markdown img refs) | **deny-all url_fetcher** (T13.56 fuzz: 51 vectors all rejected) |
| 2 | BrightData client | `integrations/brightdata/client.py:26` (`httpx.AsyncClient`) | env: `BRIGHTDATA_API_KEY` + hardcoded base URL | No | hardcoded URL — admin-only |
| 3 | USAJobs adapter | `integrations/adapters/usajobs_adapter.py:55` (`httpx.AsyncClient`) | hardcoded API URL | No | hardcoded URL — admin-only |
| 4 | TWC (Texas Workforce) adapter | `integrations/adapters/twc_adapter.py:33` (`httpx.AsyncClient`) | hardcoded API URL | No | hardcoded URL — admin-only |
| 5 | Credit microservice | `routes/credit.py:43` (`httpx.AsyncClient`) | env: `CREDIT_API_URL` | No | env-derived URL — admin-only |
| 6 | LLM providers (Anthropic, OpenAI, Gemini) | indirect via SDK | SDK-internal hardcoded endpoints | No | SDK abstracts; URL fixed |
| 7 | SendGrid | indirect via `sendgrid` SDK | SDK hardcoded `https://api.sendgrid.com/v3/...` | No | SDK fixed URL |
| 8 | Markdown image references | inside WeasyPrint pipeline | worker-supplied markdown body | **Yes** | covered by site 1 (deny-all) |

## Findings

**Zero P0/P1 findings.** No URL-fetch site found where a worker can influence the destination URL outside of WeasyPrint's already-hardened path.

### Verified clean

- WeasyPrint deny-all is robust against 51-vector fuzz corpus (T13.56). Worker markdown can include `<img src="http://169.254.169.254/">` — all rejected.
- BrightData / USAJobs / TWC / Credit endpoints are configuration-derived, not request-derived. Worker input never reaches the URL builder for these.
- LLM + SendGrid SDKs use fixed endpoints; we don't pass URL parameters.

### Worker-controllable inputs that flow into fetchers

- **WeasyPrint markdown:** worker writes resume / cover letter content; markdown may include `![](...)`. The deny-all fetcher catches every URL the worker could embed (T13.56 fuzz coverage).
- No other worker input reaches a URL-fetching primitive.

## Out of scope

- Frontend network calls (run in user's browser; different threat model)
- DNS rebinding at the SDK layer (Anthropic/OpenAI clients) — assumes SDK trust
- HTTP redirects in outbound calls — `httpx` follows redirects by default; worth confirming the integrations don't pass through worker-supplied redirect chains, but no such path was found

## Recommendation

- No changes required for hackathon scope.
- For production hardening (S14+), consider an "egress allowlist" pattern: a single helper `safe_outbound(url, allowed_hosts=...)` wrapping every `httpx.AsyncClient` call. Belt-and-suspenders.
