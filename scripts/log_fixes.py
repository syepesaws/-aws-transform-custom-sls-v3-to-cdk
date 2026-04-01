#!/usr/bin/env python3
"""Log manual fixes for a benchmark result. Appends to the result JSON.

Usage:
  python scripts/log_fixes.py <repo-name> --fix "Description of manual fix"
  python scripts/log_fixes.py <repo-name> --issue "Description of issue encountered"
  python scripts/log_fixes.py <repo-name> --category iam --fix "Had to add missing DynamoDB permissions"
  python scripts/log_fixes.py <repo-name> --show
"""

import argparse
import json
import os
import sys

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "benchmark-results")

CATEGORIES = ["iam", "event-mapping", "plugin-translation", "handler", "dependencies", "config", "other"]


def load_result(name):
    path = os.path.join(RESULTS_DIR, f"{name}.json")
    if not os.path.exists(path):
        sys.exit(f"No result found for '{name}'. Available: {[f[:-5] for f in os.listdir(RESULTS_DIR) if f.endswith('.json')]}")
    with open(path) as f:
        return json.load(f), path


def main():
    parser = argparse.ArgumentParser(description="Log manual fixes for benchmark results")
    parser.add_argument("repo", help="Repository name (e.g. aws-lambda-typescript)")
    parser.add_argument("--fix", action="append", default=[], help="Manual fix description (repeatable)")
    parser.add_argument("--issue", action="append", default=[], help="Issue encountered (repeatable)")
    parser.add_argument("--category", choices=CATEGORIES, help="Fix category")
    parser.add_argument("--show", action="store_true", help="Show current fixes and issues")
    args = parser.parse_args()

    result, path = load_result(args.repo)

    if args.show:
        fixes = result.get("manual_fixes_needed", [])
        issues = result.get("issues_encountered", [])
        print(f"Manual fixes ({len(fixes)}):")
        for f in fixes:
            print(f"  - {f}")
        print(f"Issues ({len(issues)}):")
        for i in issues:
            print(f"  - {i}")
        return

    if not args.fix and not args.issue:
        parser.error("Provide --fix, --issue, or --show")

    result.setdefault("manual_fixes_needed", [])
    result.setdefault("issues_encountered", [])

    prefix = f"[{args.category}] " if args.category else ""
    for f in args.fix:
        result["manual_fixes_needed"].append(f"{prefix}{f}")
    for i in args.issue:
        result["issues_encountered"].append(f"{prefix}{i}")

    with open(path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Updated {path}")
    print(f"  Fixes: {len(result['manual_fixes_needed'])} | Issues: {len(result['issues_encountered'])}")


if __name__ == "__main__":
    main()
