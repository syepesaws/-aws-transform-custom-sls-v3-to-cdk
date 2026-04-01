#!/usr/bin/env python3
"""Analyze CDK code quality of transformed repos. Enriches result JSONs with quality metrics.

Usage:
  python scripts/analyze_cdk_quality.py                    # analyze all repos in .workdir/
  python scripts/analyze_cdk_quality.py --repo <name>      # analyze single repo
  python scripts/analyze_cdk_quality.py --path /some/dir   # analyze arbitrary directory
"""

import argparse
import glob
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
WORK_DIR = os.path.join(PROJECT_DIR, ".workdir")
RESULTS_DIR = os.path.join(PROJECT_DIR, "benchmark-results")


def analyze_directory(repo_dir):
    """Analyze CDK TypeScript code quality in a directory."""
    metrics = {
        "l2_constructs": 0,
        "cfn_escape_hatches": 0,
        "todo_comments": 0,
        "unused_imports": 0,
        "total_ts_files": 0,
        "total_ts_loc": 0,
        "cdk_stack_files": [],
        "constructs_used": [],
        "issues": [],
    }

    ts_files = glob.glob(os.path.join(repo_dir, "**", "*.ts"), recursive=True)
    ts_files = [f for f in ts_files if "/node_modules/" not in f and "/cdk.out/" not in f and "/.git/" not in f]
    metrics["total_ts_files"] = len(ts_files)

    l2_pattern = re.compile(r"new\s+([\w.]+)\.(Function|Bucket|Table|RestApi|HttpApi|Queue|Topic|Rule|Distribution|Cluster|DatabaseInstance|NodejsFunction|PythonFunction|GoFunction)\b")
    cfn_pattern = re.compile(r"\bCfn\w+\b|CfnResource|\.addOverride\(|\.addPropertyOverride\(")
    todo_pattern = re.compile(r"//\s*(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)
    import_pattern = re.compile(r"^import\s+.*from\s+['\"](.+)['\"];?\s*$")

    constructs_seen = set()

    for fpath in ts_files:
        try:
            with open(fpath) as f:
                content = f.read()
                lines = content.splitlines()
        except (UnicodeDecodeError, IOError):
            continue

        metrics["total_ts_loc"] += len(lines)

        # Detect stack files
        if "extends cdk.Stack" in content or "extends Stack" in content:
            metrics["cdk_stack_files"].append(os.path.relpath(fpath, repo_dir))

        # L2 constructs
        for m in l2_pattern.finditer(content):
            metrics["l2_constructs"] += 1
            constructs_seen.add(m.group(2))

        # Cfn escape hatches
        cfn_matches = cfn_pattern.findall(content)
        metrics["cfn_escape_hatches"] += len(cfn_matches)
        if cfn_matches:
            metrics["issues"].append(f"{os.path.relpath(fpath, repo_dir)}: {len(cfn_matches)} CfnResource/escape hatch(es)")

        # TODOs
        todo_matches = todo_pattern.findall(content)
        metrics["todo_comments"] += len(todo_matches)

    metrics["constructs_used"] = sorted(constructs_seen)

    # Quality rating
    total_constructs = metrics["l2_constructs"] + metrics["cfn_escape_hatches"]
    if total_constructs > 0:
        metrics["l2_ratio"] = round(metrics["l2_constructs"] / total_constructs, 2)
    else:
        metrics["l2_ratio"] = None

    return metrics


def enrich_result(repo_name, metrics):
    """Write quality metrics into the result JSON."""
    result_path = os.path.join(RESULTS_DIR, f"{repo_name}.json")
    if not os.path.exists(result_path):
        return
    with open(result_path) as f:
        result = json.load(f)
    result["cdk_quality"] = metrics
    if metrics["total_ts_loc"]:
        result["loc"] = metrics["total_ts_loc"]
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  Enriched {result_path}")


def print_metrics(name, m):
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    print(f"  TS files: {m['total_ts_files']}  |  TS LOC: {m['total_ts_loc']}")
    print(f"  L2 constructs: {m['l2_constructs']}  |  Cfn escape hatches: {m['cfn_escape_hatches']}  |  L2 ratio: {m['l2_ratio']}")
    print(f"  TODOs: {m['todo_comments']}")
    print(f"  Constructs: {', '.join(m['constructs_used']) or 'none detected'}")
    if m["issues"]:
        print(f"  Issues:")
        for i in m["issues"]:
            print(f"    - {i}")


def main():
    parser = argparse.ArgumentParser(description="Analyze CDK code quality")
    parser.add_argument("--repo", help="Single repo name to analyze")
    parser.add_argument("--path", help="Arbitrary directory to analyze (no result enrichment)")
    parser.add_argument("--no-enrich", action="store_true", help="Skip writing to result JSONs")
    args = parser.parse_args()

    if args.path:
        m = analyze_directory(args.path)
        print_metrics(os.path.basename(args.path), m)
        return

    if not os.path.isdir(WORK_DIR):
        sys.exit(f"No .workdir/ found. Run benchmarks locally first, or use --path.")

    repos = [args.repo] if args.repo else [d for d in os.listdir(WORK_DIR) if os.path.isdir(os.path.join(WORK_DIR, d))]

    for name in sorted(repos):
        repo_dir = os.path.join(WORK_DIR, name)
        if not os.path.isdir(repo_dir):
            print(f"Skipping {name}: not found in .workdir/")
            continue
        m = analyze_directory(repo_dir)
        print_metrics(name, m)
        if not args.no_enrich:
            enrich_result(name, m)


if __name__ == "__main__":
    main()
