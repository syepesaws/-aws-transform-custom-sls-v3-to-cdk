#!/usr/bin/env python3
"""Run ATX transformation on repos from config.yaml or a single repo via env vars. Writes per-repo JSON results."""

import json
import os
import re
import shutil
import subprocess
import sys
import time
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
RESULTS_DIR = os.path.join(PROJECT_DIR, "benchmark-results")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.yaml")
WORK_DIR = os.path.join(PROJECT_DIR, ".workdir")


def run(cmd, cwd=None, capture=True):
    """Run a shell command, return (exit_code, stdout)."""
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=capture, text=True)
    return r.returncode, (r.stdout + r.stderr) if capture else ""


def run_single_repo(name, url, td_name, build_cmd, results_dir, work_dir):
    """Run benchmark for a single repo. Returns result dict."""
    repo_dir = os.path.join(work_dir, name)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(work_dir, exist_ok=True)

    # Clone
    if os.path.isdir(repo_dir):
        print("  Using cached clone")
    else:
        run(f"git clone --depth 1 {url} {repo_dir}")

    # Run ATX
    start = time.time()
    atx_cmd = f'atx custom def exec -n "{td_name}" -p "{repo_dir}" -c "{build_cmd}" -x -t'
    exit_code, output = run(atx_cmd)
    duration = int(time.time() - start)

    atx_log = os.path.join(results_dir, f"{name}_atx.log")
    with open(atx_log, "w") as f:
        f.write(output)

    # Parse agent minutes (case-insensitive)
    m = re.findall(r"Agent [Mm]inutes used: ([0-9.]+)", output)
    agent_minutes = m[-1] if m else "N/A"

    # Parse conversation ID from log path
    c = re.findall(r"atx/custom/([^/]+)/logs/", output)
    conv_id = c[-1] if c else ""

    # Check if ATX reported failure in output (even if exit code is 0)
    atx_failed = "FAILURE status" in output or exit_code != 0

    # Extract failure reason
    failure_reason = ""
    if atx_failed:
        for pattern in [r"Fatal error: (.+)", r"Error executing transformation: (.+)", r"(Execution was not successful[^\n]+)"]:
            fm = re.findall(pattern, output)
            if fm:
                failure_reason = fm[-1].strip()
                break
        if not failure_reason and exit_code != 0:
            failure_reason = f"Exit code {exit_code}"

    # Build validation
    b_exit, b_output = run(build_cmd, cwd=repo_dir)
    build_status = "pass" if b_exit == 0 else "fail"
    build_log = os.path.join(results_dir, f"{name}_build.log")
    with open(build_log, "w") as f:
        f.write(b_output)

    # Knowledge items count
    ki_count = "N/A"
    if conv_id:
        ki_exit, ki_out = run(f'atx custom def list-ki -n "{td_name}" --json')
        if ki_exit == 0:
            try:
                ki_count = str(len(json.loads(ki_out)))
            except json.JSONDecodeError:
                pass

    # Cost calculation ($0.035 per agent minute)
    COST_PER_MINUTE = 0.035
    cost = f"${float(agent_minutes) * COST_PER_MINUTE:.2f}" if agent_minutes != "N/A" else "N/A"

    result = {
        "repo": name,
        "url": url,
        "transformation_status": "failure" if atx_failed else "success",
        "failure_reason": failure_reason,
        "build_status": build_status,
        "duration_seconds": duration,
        "agent_minutes": agent_minutes,
        "cost": cost,
        "knowledge_items": ki_count,
        "conversation_id": conv_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    result_file = os.path.join(results_dir, f"{name}.json")
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)

    return result


def main():
    for tool in ["git", "atx"]:
        if not shutil.which(tool):
            sys.exit(f"Error: {tool} not found")

    # Single-repo mode (for CodeBuild): set REPO_NAME + REPO_URL + TD_NAME env vars
    if os.environ.get("REPO_NAME") and os.environ.get("REPO_URL"):
        name = os.environ["REPO_NAME"]
        url = os.environ["REPO_URL"]
        td_name = os.environ.get("TD_NAME", "sls-v3-to-cdk")
        build_cmd = os.environ.get("BUILD_CMD", "npx cdk synth")
        print(f"--- Single-repo mode: {name} ---")
        result = run_single_repo(name, url, td_name, build_cmd, RESULTS_DIR, WORK_DIR)
        status = "✅" if result["transformation_status"] == "success" else "❌"
        print(f"  Status: {status} | Build: {result['build_status']} | Time: {result['duration_seconds']}s | Agent min: {result['agent_minutes']}")
        return

    # Batch mode: read from config.yaml
    if not os.path.exists(CONFIG_PATH):
        sys.exit("Error: config.yaml not found. Run scrape_repos.py first.")

    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    td_name = config["transformation_name"]
    build_cmd = config.get("build_command", "npx cdk synth")
    repos = config.get("repos", [])

    if not repos:
        sys.exit("Error: no repos in config.yaml")

    print(f"=== ATX Benchmark: {td_name} ===")
    print(f"Repos: {len(repos)} | Build: {build_cmd}\n")

    for i, repo in enumerate(repos):
        print(f"--- [{i+1}/{len(repos)}] {repo['name']} ---")
        result = run_single_repo(repo["name"], repo["url"], td_name, build_cmd, RESULTS_DIR, WORK_DIR)
        status = "✅" if result["transformation_status"] == "success" else "❌"
        print(f"  Status: {status} | Build: {result['build_status']} | Time: {result['duration_seconds']}s | Agent min: {result['agent_minutes']}\n")

    print(f"=== Done. Results in {RESULTS_DIR} ===")


if __name__ == "__main__":
    main()
