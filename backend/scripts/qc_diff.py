"""Pixel-diff helper for divona QC `screenshot:` step assertions (T13.6).

Compares two PNG screenshots and reports a pass/fail verdict against a
configurable threshold. Used by divona once the `screenshot:` step type
documented in `.paircoder/qc/suites/_template.qc.yaml` is wired up.

**Out of scope:** Playwright. Playwright has its own built-in
`expect(page).toHaveScreenshot()` which uses pixelmatch internally and
stores baselines next to specs (`frontend/e2e/__screenshots__/`). The two
systems do NOT share baselines — see `docs/adr/qc-visual-regression.md`
for the rationale (different browsers, different formats, different
maintenance cycles).

Runs in the backend venv (`backend/.venv`) where Pillow is already
available as a transitive dep of WeasyPrint. Invoke with:

    cd backend && .venv/bin/python -m scripts.qc_diff <baseline> <candidate>

Or import `compare_screenshots` directly from divona's Python harness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

DEFAULT_MAX_DIFF_RATIO = 0.001  # 0.1 %; tunable per call or per scenario.


def _load_rgb(path: Path, *, label: str) -> Image.Image:
    """Open `path` as an RGB image; raise FileNotFoundError mentioning `label`."""
    if not path.exists():
        raise FileNotFoundError(
            f"qc_diff: {label} screenshot not found at {path}. "
            f"On first run divona writes the baseline; on subsequent runs the "
            f"candidate must exist for the diff to be meaningful."
        )
    return Image.open(path).convert("RGB")


def _count_diff_pixels(baseline: Image.Image, candidate: Image.Image) -> int:
    """Count pixels that differ in any channel between two same-size RGB images."""
    diff = ImageChops.difference(baseline, candidate)
    # `getbbox` returns None when the diff is entirely zero — fast path.
    if diff.getbbox() is None:
        return 0
    # Reduce to a single max-channel grayscale, then count nonzero entries via
    # the histogram (Pillow 13 deprecates getdata()).
    histogram = diff.convert("L").histogram()
    return sum(histogram[1:])  # bucket 0 = unchanged pixels.


def _write_diff_image(
    baseline: Image.Image,
    candidate: Image.Image,
    out_path: Path,
) -> Path:
    """Write a high-contrast diff visualization next to the candidate."""
    diff = ImageChops.difference(baseline, candidate)
    # Amplify so even tiny diffs are visible to a reviewer.
    amplified = diff.point(lambda v: min(255, v * 8))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    amplified.save(out_path, format="PNG")
    return out_path


def _compute_diff_ratio(base_img: Image.Image, cand_img: Image.Image) -> float:
    """Return differing-pixel fraction in [0, 1]; 1.0 when sizes mismatch."""
    if base_img.size != cand_img.size:
        return 1.0
    differing = _count_diff_pixels(base_img, cand_img)
    total = base_img.size[0] * base_img.size[1]
    return differing / total if total else 0.0


def compare_screenshots(
    baseline_path: Path | str,
    candidate_path: Path | str,
    *,
    max_diff_ratio: float = DEFAULT_MAX_DIFF_RATIO,
) -> dict[str, Any]:
    """Compare two PNG screenshots and report a pass/fail verdict.

    Returns ``{"match": bool, "diff_ratio": float, "diff_image": Path | None}``.
    ``diff_image`` is written next to the candidate as ``<stem>.diff.png`` only
    on a pixel-level mismatch (sizes equal, ratio above threshold).
    Raises ``FileNotFoundError`` if either path is missing.
    """
    baseline = Path(baseline_path)
    candidate = Path(candidate_path)
    base_img = _load_rgb(baseline, label="baseline")
    cand_img = _load_rgb(candidate, label="candidate")

    diff_ratio = _compute_diff_ratio(base_img, cand_img)
    match = diff_ratio <= max_diff_ratio

    diff_image: Path | None = None
    if not match and base_img.size == cand_img.size:
        diff_image = _write_diff_image(
            base_img, cand_img, candidate.with_name(f"{candidate.stem}.diff.png")
        )

    return {"match": match, "diff_ratio": diff_ratio, "diff_image": diff_image}


__all__ = ["compare_screenshots", "DEFAULT_MAX_DIFF_RATIO"]
