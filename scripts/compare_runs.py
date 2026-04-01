#!/usr/bin/env python3
"""Compare two benchmark runs and report regressions/improvements.

Usage:
  python scripts/compare_runs.py --profile demo                          # compare latest vs previous
  python scripts/compare_runs.py --profile demo --baseline <id> --current <id>  # compare specific runs
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DEFAULT_BUCKET = os.environ.get("RESULTS_BUCKET", "benchmarkpipelinestack-resultsbucketa95a2103-gqapfsi09xnq")


def aws(cmd, profile=None):
    if profile:
        cmd = f"AWS_PROFILE={profile} {cmd}"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.returncode, r.stdout


def list_runs(bucket, profile):
    _, out = aws(f"aws s3 ls s3://{bucket}/runs/ --region us-east-1", profile)
    runs = []
    for line in out.strip().splitlines():
        line = line.strip()
        if line.startswith("PRE "):
            run_id = line[4:].rstrip("/")
            if run_id:
                runs.append(run_id)
    return sorted(runs)


def download_run(bucket, run_id, profile):
    """Download all result.json files for a run into a temp dir, return {repo: data}."""
    tmpdir = tempfile.mkdtemp()
    aws(f'aws s3 cp s3://{bucket}/runs/{run_id}/ {tmpdir}/ --recursive --exclude "*" --include "*/result.json" --region us-east-1', profile)
    results = {}
    for root, _, files in os.walk(tmpdir):
        for f in files:
            if f == "result.json":
                repo = os.path.basename(root)
                with open(os.path.join(root, f)) as fh:
                    results[repo] = json.load(fh)
    return results


def compare(baseline, current):
    """Compare two result dicts, return markdown report."""
    all_repos = sorted(set(list(baseline.keys()) + list(current.keys())))
    lines = ["# Run Comparison\n"]
    lines.append("| Repository | Metric | Baseline | Current | Delta |")
    lines.append("|------------|--------|----------|---------|-------|")

    improvements = 0
    regressions = 0

    for repo in all_repos:
        b = baseline.get(repo)
        c = current.get(repo)

        if not b:
            lines.append(f"| {repo} | | _(new)_ | {c.get('transformation_status', '?')} | ➕ added |")
            continue
        if not c:
            lines.append(f"| {repo} | | {b.get('transformation_status', '?')} | _(removed)_ | ➖ removed |")
            continue

        # Status change
        bs, cs = b.get("transformation_status"), c.get("transformation_status")
        if bs != cs:
            icon = "🟢" if cs == "success" else "🔴"
            lines.append(f"| {repo} | status | {bs} | {cs} | {icon} |")
            if cs == "success":
                improvements += 1
            else:
                regressions += 1

        # Build change
        bb, cb = b.get("build_status"), c.get("build_status")
        if bb != cb:
            icon = "🟢" if cb == "pass" else "🔴"
            lines.append(f"| {repo} | build | {bb} | {cb} | {icon} |")

        # Agent minutes
        try:
            bm = float(b.get("agent_minutes", 0))
            cm = float(c.get("agent_minutes", 0))
            if bm > 0:
                delta_pct = ((cm - bm) / bm) * 100
                icon = "🟢" if delta_pct < -5 else ("🔴" if delta_pct > 5 else "➖")
                lines.append(f"| {repo} | agent_min | {bm:.1f} | {cm:.1f} | {icon} {delta_pct:+.1f}% |")
        except (ValueError, TypeError):
            pass

        # Score change (criteria)
        def score(r):
            criteria = r.get("criteria", {})
            if not criteria:
                return None
            passed = sum(1 for v in criteria.values() if v.get("status") == "PASS")
            total = sum(1 for v in criteria.values() if v.get("status") in ("PASS", "FAIL"))
            return (passed, total) if total > 0 else None

        bscore, cscore = score(b), score(c)
        if bscore and cscore and bscore != cscore:
            icon = "🟢" if cscore[0] > bscore[0] else "🔴"
            lines.append(f"| {repo} | score | {bscore[0]}/{bscore[1]} | {cscore[0]}/{cscore[1]} | {icon} |")

    lines.append(f"\n**Summary**: {improvements} improvements, {regressions} regressions across {len(all_repos)} repos")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compare benchmark runs")
    parser.add_argument("--profile", help="AWS profile name")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--baseline", help="Baseline run ID")
    parser.add_argument("--current", help="Current run ID")
    parser.add_argument("--output", help="Write report to file")
    args = parser.parse_args()

    runs = list_runs(args.bucket, args.profile)
    if len(runs) < 2 and not (args.baseline and args.current):
        sys.exit("Need at least 2 runs to compare. Use --baseline and --current to specify.")

    baseline_id = args.baseline or runs[-2]
    current_id = args.current or runs[-1]

    print(f"Baseline: {baseline_id[:12]}...")
    print(f"Current:  {current_id[:12]}...")

    baseline = download_run(args.bucket, baseline_id, args.profile)
    current = download_run(args.bucket, current_id, args.profile)

    report = compare(baseline, current)
    print(report)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"\nWrote {args.output}")


if __name__ == "__main__":
    main()
