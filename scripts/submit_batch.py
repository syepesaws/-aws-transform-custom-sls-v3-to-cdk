#!/usr/bin/env python3
"""Submit benchmark jobs to AWS Batch. One job per repo from config.yaml.

Usage:
  python scripts/submit_batch.py --profile demo                    # submit all repos
  python scripts/submit_batch.py --profile demo --repo <name>      # submit single repo
  python scripts/submit_batch.py --profile demo --status           # check job statuses
  python scripts/submit_batch.py --profile demo --status --wait    # wait until all complete
"""

import argparse
import json
import os
import subprocess
import sys
import time
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.yaml")
BATCH_STATE_FILE = os.path.join(PROJECT_DIR, ".workdir", "batch_jobs.json")

# Read from CDK outputs or override via env
REGION = os.environ.get("AWS_REGION", "us-east-1")


def aws(cmd, profile=None):
    if profile:
        cmd = f"AWS_PROFILE={profile} {cmd}"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"Error: {r.stderr.strip()}", file=sys.stderr)
    return r.returncode, r.stdout.strip()


def get_stack_outputs(profile):
    """Read CDK stack outputs."""
    _, out = aws(
        f"aws cloudformation describe-stacks --stack-name BatchBenchmarkStack --region {REGION} "
        f"--query 'Stacks[0].Outputs' --output json",
        profile,
    )
    outputs = {}
    for o in json.loads(out or "[]"):
        outputs[o["OutputKey"]] = o["OutputValue"]
    return outputs


def submit_job(profile, job_queue, job_def, results_bucket, repo, td_name, build_cmd, run_id):
    """Submit a single Batch job."""
    atx_cmd = f'atx custom def exec -n "{td_name}" -p /source/{repo["name"]} -c "{build_cmd}" -x -t'

    command = [
        "--source", repo["url"],
        "--output", f"runs/{run_id}/{repo['name']}/",
        "--command", atx_cmd,
    ]

    env = [
        {"name": "S3_BUCKET", "value": results_bucket},
        {"name": "ATX_SHELL_TIMEOUT", "value": "1800"},
    ]

    overrides = json.dumps({
        "command": command,
        "environment": env,
    })

    _, out = aws(
        f"aws batch submit-job "
        f"--job-name 'bench-{repo['name'][:100]}' "
        f"--job-queue '{job_queue}' "
        f"--job-definition '{job_def}' "
        f"--container-overrides '{overrides}' "
        f"--region {REGION} --output json",
        profile,
    )
    return json.loads(out) if out else None


def check_status(profile, jobs):
    """Check status of submitted jobs."""
    if not jobs:
        print("No jobs found.")
        return {}

    job_ids = [j["jobId"] for j in jobs.values()]
    _, out = aws(
        f"aws batch describe-jobs --jobs {' '.join(job_ids)} --region {REGION} --output json",
        profile,
    )
    statuses = {}
    for job in json.loads(out or '{"jobs":[]}')["jobs"]:
        name = job["jobName"].replace("bench-", "", 1)
        statuses[name] = {
            "status": job["status"],
            "reason": job.get("statusReason", ""),
            "started": job.get("startedAt", 0),
            "stopped": job.get("stoppedAt", 0),
        }
    return statuses


def print_status_table(statuses):
    icons = {"SUCCEEDED": "✅", "FAILED": "❌", "RUNNING": "⏳", "RUNNABLE": "⏸️", "SUBMITTED": "📤", "PENDING": "⏸️", "STARTING": "🔄"}
    print(f"\n{'Repo':<45} {'Status':<15} {'Duration'}")
    print("-" * 75)
    for name, s in sorted(statuses.items()):
        icon = icons.get(s["status"], "❓")
        duration = ""
        if s["started"] and s["stopped"]:
            dur_s = (s["stopped"] - s["started"]) // 1000
            duration = f"{dur_s // 60}m {dur_s % 60}s"
        elif s["started"]:
            duration = "running..."
        print(f"{icon} {name:<43} {s['status']:<15} {duration}")

    total = len(statuses)
    done = sum(1 for s in statuses.values() if s["status"] in ("SUCCEEDED", "FAILED"))
    print(f"\nProgress: {done}/{total}")


def save_state(jobs, run_id):
    os.makedirs(os.path.dirname(BATCH_STATE_FILE), exist_ok=True)
    with open(BATCH_STATE_FILE, "w") as f:
        json.dump({"run_id": run_id, "jobs": jobs}, f, indent=2)


def load_state():
    if not os.path.exists(BATCH_STATE_FILE):
        return None, {}
    with open(BATCH_STATE_FILE) as f:
        data = json.load(f)
    return data.get("run_id"), data.get("jobs", {})


def main():
    parser = argparse.ArgumentParser(description="Submit benchmark jobs to AWS Batch")
    parser.add_argument("--profile", help="AWS profile name")
    parser.add_argument("--repo", help="Submit single repo by name")
    parser.add_argument("--status", action="store_true", help="Check job statuses")
    parser.add_argument("--wait", action="store_true", help="Wait until all jobs complete")
    args = parser.parse_args()

    if args.status:
        run_id, jobs = load_state()
        if not jobs:
            sys.exit("No jobs found. Submit jobs first.")
        print(f"Run: {run_id}")
        while True:
            statuses = check_status(args.profile, jobs)
            print_status_table(statuses)
            all_done = all(s["status"] in ("SUCCEEDED", "FAILED") for s in statuses.values())
            if all_done or not args.wait:
                break
            print("\nRefreshing in 30s... (Ctrl+C to stop)")
            time.sleep(30)
        return

    # Load config
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    td_name = config["transformation_name"]
    build_cmd = config.get("build_command", "npx cdk synth")
    repos = config.get("repos", [])

    if args.repo:
        repos = [r for r in repos if r["name"] == args.repo]
        if not repos:
            sys.exit(f"Repo '{args.repo}' not found in config.yaml")

    # Get stack outputs
    outputs = get_stack_outputs(args.profile)
    job_queue = outputs.get("JobQueueArn")
    job_def = outputs.get("JobDefinitionArn")
    results_bucket = outputs.get("ResultsBucketName")

    if not all([job_queue, job_def, results_bucket]):
        sys.exit("Missing stack outputs. Deploy BatchBenchmarkStack first.")

    run_id = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())
    print(f"=== Submitting {len(repos)} jobs | Run: {run_id} ===\n")

    jobs = {}
    for repo in repos:
        result = submit_job(args.profile, job_queue, job_def, results_bucket, repo, td_name, build_cmd, run_id)
        if result:
            jobs[repo["name"]] = {"jobId": result["jobId"], "jobName": result["jobName"]}
            print(f"  ✅ {repo['name']} → {result['jobId']}")
        else:
            print(f"  ❌ {repo['name']} — failed to submit")

    save_state(jobs, run_id)
    print(f"\n=== Submitted {len(jobs)} jobs. Track with: python scripts/submit_batch.py --profile {args.profile or 'default'} --status ===")


if __name__ == "__main__":
    main()
