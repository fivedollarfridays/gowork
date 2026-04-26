# T13.96 — XSS Audit (Every Render)

**Sprint:** S13
**Method:** Catalog every site that renders worker-supplied content; verify escape/sanitize discipline.
**Generated:** 2026-04-25

## Render-site inventory

| Site | File | Mechanism | Worker-supplied input | Escape discipline |
|------|------|-----------|-----------------------|-------------------|
| PDF body (resume + cover letter) | `core/pdf_renderer.py:154` (`markdown.markdown`) → WeasyPrint | Markdown → HTML → PDF | resume body, cover letter body | Output renders to PDF (no JS execution); inline HTML in markdown produces gibberish, not XSS |
| PDF template chrome | `core/pdf_renderer.py:107-115` Jinja2 `Environment(autoescape=select_autoescape(html))` | Jinja2 with autoescape ON | title, body | autoescape ON for `.html`/`.htm`/`.xml` |
| Appointment email body | `modules/appointments/_email_rendering.py:133-186` | Manual `html.escape(..., quote=True)` for every interpolation | name, title, location, URLs | every variable wrapped in `html.escape(..., quote=True)` — explicit |
| Engagement digest email | `modules/engagement/digest_composer.py` | Same escape pattern (per docstring on line 23: "every worker-controlled field flows through html.escape at the template") | role, notes, barrier IDs | confirmed in docstring |
| Frontend pages | `frontend/src/app/**/*.tsx` | React | every t() call | React intrinsically escapes; no `dangerouslySetInnerHTML` found in `src/` |

## Findings

**Zero XSS findings.**

### Verified clean

- **Frontend (Next.js + React):** zero `dangerouslySetInnerHTML` usages in `frontend/src/`. React escapes every `{value}` interpolation by default. Translation values from `t()` follow the same rule.
- **PDF rendering:** worker markdown is converted to HTML via `markdown.markdown(...)` with `extensions=["extra"]`. The "extra" set does NOT include the `markdown.extensions.attr_list` HTML-stripping or the `markdown.extensions.smarty` quote-mangling. Inline `<script>` tags in worker markdown WOULD pass through to HTML — BUT the consumer is WeasyPrint producing a PDF. No JavaScript execution context exists in the output medium. Worst case: a `<script>` tag renders as visible literal text in the PDF (ugly, not exploitable).
- **Email rendering:** `_email_rendering.py` explicitly calls `html.escape(value, quote=True)` for every interpolated variable (10+ call sites verified). Even if a worker writes `<script>alert(1)</script>` in their name field, the email contains `&lt;script&gt;alert(1)&lt;/script&gt;`.
- **Jinja2 templates:** `pdf_renderer._build_jinja_env` constructs `Environment(autoescape=select_autoescape(enabled_extensions=("html","htm","xml"), default_for_string=True))`. Both extension-based and string-based autoescape are ON.
- **API JSON responses:** FastAPI serializes via Pydantic; no manual HTML rendering returns JSON-as-HTML anywhere.

### Edge case worth noting (not a finding)

If a future feature adds an HTML-rendering email frontend (web mail preview) or HTML notifications, the markdown→HTML path bypasses Jinja2 autoescape (the markdown output is interpolated as `{{ body|safe }}` — the `|safe` filter explicitly disables escape for the already-rendered HTML). This is correct for PDF but would be unsafe if reused in a browser context. Worth documenting in the renderer's docstring if such reuse becomes plausible.

## Recommendation

- No code changes required.
- One-line addition to `pdf_renderer.py` docstring: "Output is intended for PDF rendering only. Do NOT reuse the rendered HTML in a browser context — markdown inline HTML is not sanitized."

## Out of scope

- DOM-based XSS in browser extensions / dev tools (out of app threat model)
- CSP header configuration (frontend deploys via Fly; could add `Content-Security-Policy` headers — separate hardening task)
- Email-client rendering quirks (different MUAs render HTML differently; covered by SendGrid's deliverability tooling)
