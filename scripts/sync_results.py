#!/usr/bin/env python3
"""Download benchmark results from S3, regenerate BENCHMARKS.md, optionally sync back.

Usage:
  python scripts/sync_results.py                          # download latest, regenerate
  python scripts/sync_results.py --run-id <id>            # download specific run
  python scripts/sync_results.py --bucket <name>          # override bucket
  python scripts/sync_results.py --upload                 # also upload regenerated BENCHMARKS.md
  python scripts/sync_results.py --include-logs           # also download .log files
  python scripts/sync_results.py --list-runs              # list available runs
"""

import argparse
import json
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
RESULTS_DIR = os.path.join(PROJECT_DIR, "benchmark-results")
BENCHMARKS_MD = os.path.join(PROJECT_DIR, "BENCHMARKS.md")

# Default bucket from CDK stack output
DEFAULT_BUCKET = os.environ.get("RESULTS_BUCKET", "benchmarkpipelinestack-resultsbucketa95a2103-gqapfsi09xnq")


def aws(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"AWS CLI error: {r.stderr.strip()}", file=sys.stderr)
    return r.returncode, r.stdout


def list_runs(bucket):
    _, out = aws(f"aws s3 ls s3://{bucket}/runs/ --recursive --no-sign-request 2>/dev/null || aws s3 ls s3://{bucket}/runs/")
    runs = set()
    for line in out.strip().splitlines():
        parts = line.split("runs/")
        if len(parts) > 1:
            run_id = parts[1].split("/")[0]
            if run_id:
                runs.add(run_id)
    return sorted(runs)


def get_latest_run(bucket):
    runs = list_runs(bucket)
    return runs[-1] if runs else None


def download_results(bucket, run_id, include_logs):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    prefix = f"s3://{bucket}/runs/{run_id}/"

    # Download result.json files
    exclude = '--exclude "*" --include "*/result.json"'
    if include_logs:
        exclude = '--exclude "*" --include "*/result.json" --include "*/atx.log" --include "*/build.log"'

    _, out = aws(f"aws s3 cp {prefix} /tmp/bench-sync/ --recursive {exclude}")

    # Flatten into benchmark-results/
    count = 0
    for root, _, files in os.walk("/tmp/bench-sync"):
        for f in files:
            src = os.path.join(root, f)
            repo_name = os.path.basename(root)
            if f == "result.json":
                dest = os.path.join(RESULTS_DIR, f"{repo_name}.json")
            else:
                dest = os.path.join(RESULTS_DIR, f"{repo_name}_{f}")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            os.replace(src, dest)
            count += 1

    return count


def upload_benchmarks(bucket, run_id):
    aws(f"aws s3 cp {BENCHMARKS_MD} s3://{bucket}/runs/{run_id}/BENCHMARKS.md")
    aws(f"aws s3 cp {BENCHMARKS_MD} s3://{bucket}/latest/BENCHMARKS.md")
    print(f"Uploaded BENCHMARKS.md to s3://{bucket}/latest/")


def main():
    parser = argparse.ArgumentParser(description="Sync benchmark results from S3")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET, help="S3 bucket name")
    parser.add_argument("--run-id", help="Specific run ID (default: latest)")
    parser.add_argument("--upload", action="store_true", help="Upload regenerated BENCHMARKS.md back to S3")
    parser.add_argument("--include-logs", action="store_true", help="Also download ATX and build logs")
    parser.add_argument("--list-runs", action="store_true", help="List available runs and exit")
    args = parser.parse_args()

    if args.list_runs:
        runs = list_runs(args.bucket)
        if not runs:
            print("No runs found.")
        for r in runs:
            print(r)
        return

    run_id = args.run_id or get_latest_run(args.bucket)
    if not run_id:
        sys.exit("No runs found in bucket.")

    print(f"Downloading run: {run_id}")
    count = download_results(args.bucket, run_id, args.include_logs)
    print(f"Downloaded {count} files to benchmark-results/")

    # Regenerate BENCHMARKS.md
    subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "aggregate_results.py")])

    if args.upload:
        upload_benchmarks(args.bucket, run_id)


if __name__ == "__main__":
    main()
