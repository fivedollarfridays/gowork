"""Unit tests for `scripts.qc_diff.compare_screenshots`.

Covers the divona-bound visual-diff helper added under T13.6. The helper
backs the future `screenshot:` step type in `_template.qc.yaml`; Playwright
has its own built-in `expect(page).toHaveScreenshot()` and does NOT use this
helper. See `docs/adr/qc-visual-regression.md` for the split.

Test axes:
    - Identical images → 0 diff, match.
    - One-pixel change → diff_ratio > 0 but below default threshold → match.
    - Large change → above threshold → mismatch + diff image written.
    - Custom `max_diff_ratio` honored (tighter / looser).
    - Missing baseline / candidate → FileNotFoundError with a usable message.
    - Size mismatch → mismatch (does not raise; reports it).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from scripts.qc_diff import compare_screenshots


def _solid_image(path: Path, *, size: tuple[int, int], color: tuple[int, int, int]) -> Path:
    """Write a solid-color RGB PNG at `path`. Returns `path` for chaining."""
    img = Image.new("RGB", size, color)
    img.save(path, format="PNG")
    return path


def test_identical_images_match_with_zero_diff(tmp_path: Path) -> None:
    baseline = _solid_image(tmp_path / "baseline.png", size=(100, 100), color=(50, 100, 200))
    candidate = _solid_image(tmp_path / "candidate.png", size=(100, 100), color=(50, 100, 200))

    result = compare_screenshots(baseline, candidate)

    assert result["match"] is True
    assert result["diff_ratio"] == 0.0
    assert result["diff_image"] is None


def test_single_pixel_difference_under_default_threshold_matches(tmp_path: Path) -> None:
    """One pixel out of 10,000 → 0.01% diff, well under the 0.1% default."""
    baseline = _solid_image(tmp_path / "baseline.png", size=(100, 100), color=(255, 255, 255))
    candidate_img = Image.new("RGB", (100, 100), (255, 255, 255))
    candidate_img.putpixel((0, 0), (0, 0, 0))
    candidate_path = tmp_path / "candidate.png"
    candidate_img.save(candidate_path, format="PNG")

    result = compare_screenshots(baseline, candidate_path)

    assert result["match"] is True
    assert 0.0 < result["diff_ratio"] < 0.001
    assert result["diff_image"] is None


def test_large_difference_above_threshold_mismatches_and_writes_diff(tmp_path: Path) -> None:
    """Half-and-half color split → 50% diff, far above any sane threshold."""
    baseline = _solid_image(tmp_path / "baseline.png", size=(100, 100), color=(0, 0, 0))
    candidate_img = Image.new("RGB", (100, 100), (0, 0, 0))
    for x in range(50, 100):
        for y in range(100):
            candidate_img.putpixel((x, y), (255, 255, 255))
    candidate_path = tmp_path / "candidate.png"
    candidate_img.save(candidate_path, format="PNG")

    result = compare_screenshots(baseline, candidate_path)

    assert result["match"] is False
    assert result["diff_ratio"] > 0.4
    assert result["diff_image"] is not None
    assert Path(result["diff_image"]).exists()


def test_custom_threshold_tighter_than_diff_flags_mismatch(tmp_path: Path) -> None:
    """A 1-pixel diff (~0.01%) should mismatch when threshold is 0 (any diff fails)."""
    baseline = _solid_image(tmp_path / "baseline.png", size=(100, 100), color=(255, 255, 255))
    candidate_img = Image.new("RGB", (100, 100), (255, 255, 255))
    candidate_img.putpixel((0, 0), (0, 0, 0))
    candidate_path = tmp_path / "candidate.png"
    candidate_img.save(candidate_path, format="PNG")

    result = compare_screenshots(baseline, candidate_path, max_diff_ratio=0.0)

    assert result["match"] is False
    assert result["diff_ratio"] > 0.0


def test_missing_baseline_raises_file_not_found(tmp_path: Path) -> None:
    candidate = _solid_image(tmp_path / "candidate.png", size=(10, 10), color=(0, 0, 0))
    missing_baseline = tmp_path / "missing.png"

    with pytest.raises(FileNotFoundError, match="baseline"):
        compare_screenshots(missing_baseline, candidate)


def test_missing_candidate_raises_file_not_found(tmp_path: Path) -> None:
    baseline = _solid_image(tmp_path / "baseline.png", size=(10, 10), color=(0, 0, 0))
    missing_candidate = tmp_path / "missing.png"

    with pytest.raises(FileNotFoundError, match="candidate"):
        compare_screenshots(baseline, missing_candidate)


def test_size_mismatch_reports_mismatch_without_raising(tmp_path: Path) -> None:
    """Different dimensions → mismatch (the helper must not crash)."""
    baseline = _solid_image(tmp_path / "baseline.png", size=(100, 100), color=(0, 0, 0))
    candidate = _solid_image(tmp_path / "candidate.png", size=(120, 100), color=(0, 0, 0))

    result = compare_screenshots(baseline, candidate)

    assert result["match"] is False
    assert result["diff_ratio"] == 1.0  # Convention: any size mismatch == 100% diff.
    assert result["diff_image"] is None  # No pixel-level diff possible.
