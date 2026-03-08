#!/usr/bin/env python3
"""Offline evaluation runner for barrier intelligence responses.

Usage:
    python scripts/run_eval.py --queries data/eval/golden_queries.json --dry-run
    python scripts/run_eval.py --queries data/eval/golden_queries.json --output eval_results.json
"""

import argparse
import json
import re
import sys
from pathlib import Path


def check_mentions_barriers(text: str, expected: list[str]) -> bool:
    """Check if response mentions at least one expected barrier keyword."""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in expected)


def check_no_disallowed(text: str, disallowed: list[str]) -> bool:
    """Check that response contains no disallowed keywords."""
    text_lower = text.lower()
    return all(kw.lower() not in text_lower for kw in disallowed)


def count_steps(text: str) -> int:
    """Count numbered steps (e.g., '1.', '2.') in response."""
    return len(re.findall(r"^\d+\.", text, re.MULTILINE))


def evaluate_response(response: str, expected: dict) -> dict:
    """Evaluate a single response against expected properties."""
    results = {}

    if "must_mention_barriers" in expected:
        results["mentions_barriers"] = check_mentions_barriers(
            response, expected["must_mention_barriers"]
        )

    if "must_not_mention" in expected:
        results["no_disallowed"] = check_no_disallowed(
            response, expected["must_not_mention"]
        )

    if expected.get("must_have_steps"):
        steps = count_steps(response)
        results["has_steps"] = steps >= expected.get("min_steps", 1)
        if "max_steps" in expected:
            results["steps_in_range"] = steps <= expected["max_steps"]

    results["passed"] = all(results.values())
    return results


def run_dry(queries: list[dict]) -> dict:
    """Dry run: validate query schema without calling API."""
    results = []
    for q in queries:
        results.append({
            "id": q["id"],
            "question": q["question"],
            "mode": q["mode"],
            "barriers": q["situation"]["barriers"],
            "status": "dry_run",
            "checks": list(q["expected_properties"].keys()),
        })
    return {
        "total": len(results),
        "mode": "dry_run",
        "queries": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Barrier Intel Eval Runner")
    parser.add_argument("--queries", required=True, help="Path to golden_queries.json")
    parser.add_argument("--output", default=None, help="Output results JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Validate schema only")
    args = parser.parse_args()

    queries_path = Path(args.queries)
    if not queries_path.exists():
        print(f"Error: {queries_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(queries_path) as f:
        queries = json.load(f)

    print(f"Loaded {len(queries)} golden queries")

    if args.dry_run:
        results = run_dry(queries)
        print(f"Dry run complete: {results['total']} queries validated")
    else:
        print("Live eval requires ANTHROPIC_API_KEY. Use --dry-run for schema validation.")
        results = run_dry(queries)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results written to {args.output}")


if __name__ == "__main__":
    main()
