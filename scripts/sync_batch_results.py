#!/usr/bin/env python3
"""Sync Batch results: download validation_report.json + metadata.json per repo.

Usage:
  python scripts/sync_batch_results.py --profile demo
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.yaml")
RESULTS_DIR = os.path.join(PROJECT_DIR, "benchmark-results")
WORK_DIR = os.path.join(PROJECT_DIR, ".workdir")
BATCH_STATE_FILE = os.path.join(WORK_DIR, "batch_jobs.json")
REGION = "us-east-1"
COST_PER_MINUTE = 0.035


def aws(cmd, profile=None):
    if profile:
        cmd = f"AWS_PROFILE={profile} {cmd}"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def load_config():
    with open(CONFIG_PATH) as f:
        return {r["name"]: r for r in yaml.safe_load(f).get("repos", [])}


def get_batch_state():
    if not os.path.exists(BATCH_STATE_FILE):
        return None, {}
    with open(BATCH_STATE_FILE) as f:
        data = json.load(f)
    return data.get("run_id"), data.get("jobs", {})


def get_stack_output(profile, key):
    _, out = aws(
        f"aws cloudformation describe-stacks --stack-name BatchBenchmarkStack --region {REGION} "
        f"--query 'Stacks[0].Outputs[?OutputKey==`{key}`].OutputValue' --output text", profile)
    return out


def get_job_details(profile, job_ids):
    _, out = aws(f"aws batch describe-jobs --jobs {' '.join(job_ids)} --region {REGION} --output json", profile)
    return {j["jobName"].replace("bench-", "", 1): j for j in json.loads(out or '{"jobs":[]}')["jobs"]}


def find_conv_id(profile, bucket, run_id, repo_name):
    """Find the conversation ID subdirectory in S3."""
    prefix = f"s3://{bucket}/runs/{run_id}/{repo_name}/"
    _, listing = aws(f"aws s3 ls {prefix} --region {REGION}", profile)
    for line in listing.splitlines():
        if line.strip().startswith("PRE "):
            return line.strip()[4:].rstrip("/")
    return None


def download_s3_file(profile, s3_path, local_path):
    """Download a single file from S3. Returns True on success."""
    rc, _ = aws(f"aws s3 cp {s3_path} {local_path} --region {REGION}", profile)
    return rc == 0 and os.path.exists(local_path)


def parse_agent_minutes(metadata):
    """Estimate agent minutes from conversation ID start time and end date."""
    conv_id = metadata.get("conversationId", "")
    end = metadata.get("conversationEndDate", "")
    if not conv_id or not end:
        return "N/A"
    try:
        # conversationId format: 20260401_203832_64414a4a → start at 20:38:32
        parts = conv_id.split("_")
        start_str = parts[0] + "T" + parts[1] + "Z"  # 20260401T203832Z
        fmt = "%Y%m%dT%H%M%SZ"
        dt_start = datetime.strptime(start_str, fmt)
        dt_end = datetime.strptime(end, fmt)
        delta = (dt_end - dt_start).total_seconds() / 60.0
        return f"{delta:.2f}" if delta > 0 else "N/A"
    except (ValueError, TypeError, IndexError):
        return "N/A"


def main():
    parser = argparse.ArgumentParser(description="Sync Batch benchmark results")
    parser.add_argument("--profile", help="AWS profile name")
    parser.add_argument("--run-id", help="Override run ID")
    args = parser.parse_args()

    run_id, jobs = get_batch_state()
    if args.run_id:
        run_id = args.run_id
    if not run_id or not jobs:
        sys.exit("No batch jobs found. Run submit_batch.py first.")

    bucket = get_stack_output(args.profile, "ResultsBucketName")
    if not bucket:
        sys.exit("Could not find ResultsBucketName from stack outputs.")

    repo_meta = load_config()
    job_ids = [j["jobId"] for j in jobs.values()]

    print(f"Run: {run_id}\nBucket: {bucket}\n")
    print("Fetching job details...")
    job_details = get_job_details(args.profile, job_ids)

    os.makedirs(RESULTS_DIR, exist_ok=True)

    for repo_name in sorted(jobs.keys()):
        job = job_details.get(repo_name, {})
        status = job.get("status", "UNKNOWN")
        started = job.get("startedAt", 0)
        stopped = job.get("stoppedAt", 0)
        duration = (stopped - started) // 1000 if started and stopped else 0

        print(f"  {repo_name} ({status}, {duration}s)")

        # Create per-repo workdir
        repo_dir = os.path.join(WORK_DIR, repo_name)
        os.makedirs(repo_dir, exist_ok=True)

        conv_id = find_conv_id(args.profile, bucket, run_id, repo_name)
        report = None
        metadata = None

        if conv_id:
            base = f"s3://{bucket}/runs/{run_id}/{repo_name}/{conv_id}"

            # Download validation_report.json
            vr_path = os.path.join(repo_dir, "validation_report.json")
            if download_s3_file(args.profile, f"{base}/code/{repo_name}/validation_report.json", vr_path):
                with open(vr_path) as f:
                    report = json.load(f)
                print(f"    ✅ validation_report.json: {report.get('transformation_status', '?')}")
            else:
                print(f"    ⚠️  No validation_report.json")

            # Download metadata.json
            md_path = os.path.join(repo_dir, "metadata.json")
            if download_s3_file(args.profile, f"{base}/logs/custom/{conv_id}/metadata.json", md_path):
                with open(md_path) as f:
                    metadata = json.load(f)
                print(f"    ✅ metadata.json: {metadata.get('conversationId', '?')}")
            else:
                print(f"    ⚠️  No metadata.json")

        # Extract metrics from metadata
        agent_minutes = parse_agent_minutes(metadata) if metadata else "N/A"
        cost = f"${float(agent_minutes) * COST_PER_MINUTE:.2f}" if agent_minutes != "N/A" else "N/A"
        git_diff = metadata.get("gitDiffMetrics", {}) if metadata else {}
        conv_id_val = metadata.get("conversationId", "") if metadata else ""

        meta = repo_meta.get(repo_name, {"url": "", "stars": "N/A"})
        effective_status = (report.get("transformation_status") if report else None) or ("success" if status == "SUCCEEDED" else "failure")

        result = {
            "repo": repo_name,
            "url": meta.get("url", ""),
            "stars": str(meta.get("stars", "N/A")),
            "transformation_status": effective_status,
            "atx_status": "success" if status == "SUCCEEDED" else "failure",
            "failure_reason": (report.get("failure_reason", "") if report else (job.get("statusReason", "") if status != "SUCCEEDED" else "")),
            "build_status": "pass" if status == "SUCCEEDED" else "fail",
            "duration_seconds": duration,
            "agent_minutes": agent_minutes,
            "cost": cost,
            "knowledge_items": "N/A",
            "conversation_id": conv_id_val,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "criteria": report.get("criteria", {}) if report else {},
            "issues_encountered": report.get("issues_encountered", []) if report else [],
            "manual_fixes_needed": report.get("manual_fixes_needed", []) if report else [],
            "plugins_migrated": report.get("plugins_migrated", meta.get("plugins", [])) if report else meta.get("plugins", []),
            "functions_count": report.get("functions_count", "N/A") if report else "N/A",
            "git_diff": {
                "files_changed": git_diff.get("filesChanged", 0),
                "lines_added": git_diff.get("linesAdded", 0),
                "lines_deleted": git_diff.get("linesDeleted", 0),
                "lines_modified": git_diff.get("linesModified", 0),
            },
        }

        if agent_minutes != "N/A":
            print(f"    📊 Agent min: {agent_minutes} | Cost: {cost}")
        if git_diff:
            print(f"    📝 Diff: {git_diff.get('filesChanged', 0)} files, +{git_diff.get('linesAdded', 0)} -{git_diff.get('linesDeleted', 0)} ~{git_diff.get('linesModified', 0)}")

        with open(os.path.join(RESULTS_DIR, f"{repo_name}.json"), "w") as f:
            json.dump(result, f, indent=2)

    # Aggregate
    print("\nAggregating results...")
    subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "aggregate_results.py")], cwd=PROJECT_DIR)


if __name__ == "__main__":
    main()
