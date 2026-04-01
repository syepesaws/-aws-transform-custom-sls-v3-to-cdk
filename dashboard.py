#!/usr/bin/env python3
"""ATX Benchmark Dashboard — Streamlit app for monitoring and visualizing benchmark results.

Usage:
  streamlit run dashboard.py -- --profile demo
"""

import json
import glob
import os
import subprocess
import sys
import argparse

import streamlit as st
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(PROJECT_DIR, "benchmark-results")
WORK_DIR = os.path.join(PROJECT_DIR, ".workdir")
BATCH_STATE_FILE = os.path.join(WORK_DIR, "batch_jobs.json")
REGION = "us-east-1"

# Parse --profile from CLI args passed after --
PROFILE = None
for i, arg in enumerate(sys.argv):
    if arg == "--profile" and i + 1 < len(sys.argv):
        PROFILE = sys.argv[i + 1]
# Also check environment variable as fallback
if not PROFILE:
    PROFILE = os.environ.get("AWS_PROFILE")


def aws(cmd):
    if PROFILE:
        cmd = f"AWS_PROFILE={PROFILE} {cmd}"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


# --- Page config ---
st.set_page_config(page_title="ATX Benchmark Dashboard", page_icon="🚀", layout="wide")
st.title("🚀 ATX Benchmark Dashboard")
st.caption("Serverless Framework v3 → AWS CDK TypeScript")

# --- Tabs ---
tab_live, tab_results, tab_quality, tab_compare = st.tabs(["📡 Live Status", "📊 Results", "🔍 CDK Quality", "📈 Compare Runs"])

# ============================================================
# TAB 1: Live Batch Job Status
# ============================================================
with tab_live:
    st.header("Batch Job Status")

    # Run selector — list all runs from S3 + current
    def list_s3_runs():
        _, out = aws(f"aws s3 ls s3://{get_batch_bucket()}/runs/ --region {REGION}")
        runs = []
        for line in out.splitlines():
            if line.strip().startswith("PRE "):
                runs.append(line.strip()[4:].rstrip("/"))
        return sorted(runs, reverse=True)

    def get_batch_bucket():
        _, out = aws(
            f"aws cloudformation describe-stacks --stack-name BatchBenchmarkStack --region {REGION} "
            f"--query 'Stacks[0].Outputs[?OutputKey==`ResultsBucketName`].OutputValue' --output text")
        return out

    # Load current run from state file
    current_run_id = None
    current_jobs = {}
    if os.path.exists(BATCH_STATE_FILE):
        with open(BATCH_STATE_FILE) as f:
            state = json.load(f)
        current_run_id = state.get("run_id", "unknown")
        current_jobs = state.get("jobs", {})

    # Run picker
    try:
        all_runs = list_s3_runs()
    except Exception:
        all_runs = []
    if current_run_id and current_run_id not in all_runs:
        all_runs.insert(0, current_run_id)
    if not all_runs:
        all_runs = [current_run_id] if current_run_id else []

    if not all_runs:
        st.warning("No runs found. Submit jobs first.")
    else:
        selected_run = st.selectbox("Select run", all_runs, index=0, format_func=lambda r: f"{'🟢 ' if r == current_run_id else ''}{r}", key="run_selector")
        is_current_run = selected_run == current_run_id

        st.metric("Run ID", selected_run)

        job_list = []

        if is_current_run and current_jobs:
            # Live: query Batch API
            if st.button("🔄 Refresh", key="refresh_status"):
                st.rerun()

            job_ids = [j["jobId"] for j in current_jobs.values()]
            _, out = aws(f"aws batch describe-jobs --jobs {' '.join(job_ids)} --region {REGION} --output json")
            try:
                job_list = json.loads(out or '{"jobs":[]}')["jobs"]
            except json.JSONDecodeError:
                job_list = []
        else:
            # Historical: list repos from S3 prefix
            bucket = get_batch_bucket()
            if bucket:
                _, listing = aws(f"aws s3 ls s3://{bucket}/runs/{selected_run}/ --region {REGION}")
                for line in listing.splitlines():
                    if line.strip().startswith("PRE "):
                        repo = line.strip()[4:].rstrip("/")
                        job_list.append({"jobName": f"bench-{repo}", "status": "COMPLETED", "startedAt": 0, "stoppedAt": 0})

        if job_list:
            status_map = {"SUCCEEDED": "✅", "FAILED": "❌", "RUNNING": "⏳", "RUNNABLE": "⏸️", "SUBMITTED": "📤", "PENDING": "⏸️", "STARTING": "🔄", "COMPLETED": "📦"}
            rows = []
            for job in sorted(job_list, key=lambda j: j["jobName"]):
                name = job["jobName"].replace("bench-", "", 1)
                status = job["status"]
                started = job.get("startedAt", 0)
                stopped = job.get("stoppedAt", 0)
                duration = (stopped - started) // 1000 if started and stopped else None
                rows.append({
                    "Repo": name,
                    "Status": f"{status_map.get(status, '❓')} {status}",
                    "Duration (s)": duration or ("running..." if status == "RUNNING" else "—"),
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

            total = len(rows)
            done = sum(1 for j in job_list if j["status"] in ("SUCCEEDED", "FAILED", "COMPLETED"))
            succeeded = sum(1 for j in job_list if j["status"] in ("SUCCEEDED", "COMPLETED"))
            failed = sum(1 for j in job_list if j["status"] == "FAILED")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total", total)
            col2.metric("Done", f"{done}/{total}")
            col3.metric("Succeeded", succeeded)
            col4.metric("Failed", failed)

            if is_current_run and done < total:
                st.info("Jobs still running. Click Refresh to update.")

            # --- Log Viewer ---
            st.subheader("📋 Job Logs")
            repo_names = sorted([job["jobName"].replace("bench-", "", 1) for job in job_list])
            selected_repo = st.selectbox("Select repo", repo_names, key="log_repo_select")

            if selected_repo:
                selected_job = next((j for j in job_list if j["jobName"] == f"bench-{selected_repo}"), None)
                log_stream = selected_job.get("container", {}).get("logStreamName", "") if selected_job else ""
                job_status = selected_job.get("status", "") if selected_job else ""

                if not log_stream:
                    st.warning("No log stream available yet — job may still be starting.")
                else:
                    import re

                    is_running = job_status in ("RUNNING", "STARTING")
                    LINES_PER_PAGE = 100

                    def fetch_all_logs(stream):
                        """Fetch all log lines, cleaning noise."""
                        all_lines = []
                        next_token = None
                        while True:
                            token_arg = f'--next-token "{next_token}"' if next_token else "--start-from-head"
                            _, out = aws(
                                f'aws logs get-log-events '
                                f'--log-group-name /aws/batch/atx-benchmark '
                                f'--log-stream-name "{stream}" '
                                f'--limit 500 {token_arg} '
                                f'--region {REGION} --output json'
                            )
                            try:
                                data = json.loads(out or '{"events":[],"nextForwardToken":null}')
                            except json.JSONDecodeError:
                                break
                            events = data.get("events", [])
                            if not events:
                                break
                            for e in events:
                                line = re.sub(r'\x1b\[[0-9;]*m', '', e.get("message", ""))
                                line = re.sub(r'\r[^\n]*', '', line).strip()
                                if line and 'Thinking...' not in line and 'ctrl + c' not in line:
                                    all_lines.append(line)
                            new_token = data.get("nextForwardToken")
                            if new_token == next_token:
                                break
                            next_token = new_token
                        return all_lines

                    # Controls row
                    col_mode, col_refresh = st.columns([2, 1])
                    if is_running:
                        refresh_interval = col_refresh.selectbox(
                            "Auto-refresh", [5, 10, 15, 30, 60], index=4,
                            format_func=lambda x: f"Every {x}s", key="log_refresh"
                        )
                        col_mode.caption(f"🔴 Live tail — auto-refreshing every {refresh_interval}s")

                    # Fetch logs on button click
                    if st.button("📥 Load / Refresh Logs", key="fetch_logs") or (is_running and f"logs_{selected_repo}" not in st.session_state):
                        with st.spinner("Fetching logs..."):
                            st.session_state[f"logs_{selected_repo}"] = fetch_all_logs(log_stream)

                    _cache_key = f"logs_{selected_repo}"
                    _page_key = f"page_{selected_repo}"
                    _is_running = is_running
                    _log_stream = log_stream
                    _refresh = refresh_interval if is_running else None

                    @st.fragment(run_every=_refresh)
                    def render_logs():
                        if _is_running or _cache_key not in st.session_state:
                            st.session_state[_cache_key] = fetch_all_logs(_log_stream)

                        lines = st.session_state.get(_cache_key, [])
                        if not lines:
                            st.info("No log entries yet.")
                            return

                        total_lines = len(lines)
                        total_pages = max(1, (total_lines + LINES_PER_PAGE - 1) // LINES_PER_PAGE)

                        if _page_key not in st.session_state:
                            st.session_state[_page_key] = total_pages
                        st.session_state[_page_key] = max(1, min(st.session_state[_page_key], total_pages))
                        page = st.session_state[_page_key]

                        # Pagination bar
                        cols = st.columns([1, 1, 1, 4, 1, 1])
                        with cols[0]:
                            if st.button("⏮ First", key="first_page", disabled=page <= 1):
                                st.session_state[_page_key] = 1
                                st.rerun(scope="fragment")
                        with cols[1]:
                            if st.button("◀", key="prev_page", disabled=page <= 1):
                                st.session_state[_page_key] = page - 1
                                st.rerun(scope="fragment")
                        with cols[2]:
                            st.markdown(f"**{page}** / {total_pages}")
                        with cols[3]:
                            st.caption(f"{total_lines} lines")
                        with cols[4]:
                            if st.button("▶", key="next_page", disabled=page >= total_pages):
                                st.session_state[_page_key] = page + 1
                                st.rerun(scope="fragment")
                        with cols[5]:
                            if st.button("Latest ⏭", key="latest_page", disabled=page == total_pages):
                                st.session_state[_page_key] = total_pages
                                st.rerun(scope="fragment")

                        start = (page - 1) * LINES_PER_PAGE
                        end = start + LINES_PER_PAGE
                        st.code("\n".join(lines[start:end]), language="log")

                    render_logs()

# ============================================================
# TAB 2: Benchmark Results
# ============================================================
with tab_results:
    st.header("Benchmark Results")

    col_sync, col_submit = st.columns(2)
    with col_sync:
        if st.button("🔄 Sync Latest Results", key="sync_results"):
            with st.spinner("Syncing results from S3..."):
                rc, out = aws(f"python3 {os.path.join(PROJECT_DIR, 'scripts', 'sync_batch_results.py')} --profile {PROFILE or 'default'}")
                if rc == 0:
                    st.success("Results synced!")
                    st.rerun()
                else:
                    st.error(f"Sync failed: {out}")
    with col_submit:
        if st.button("🚀 Submit New Batch Run", key="submit_new_run"):
            with st.spinner("Submitting jobs..."):
                rc, out = aws(f"python3 {os.path.join(PROJECT_DIR, 'scripts', 'submit_batch.py')} --profile {PROFILE or 'default'}")
                if rc == 0:
                    st.success(out)
                    st.rerun()
                else:
                    st.error(f"Submit failed: {out}")

    result_files = sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json")))
    if not result_files:
        st.warning("No results found. Run benchmarks and sync results first.")
    else:
        results = []
        for path in result_files:
            with open(path) as f:
                results.append(json.load(f))

        rows = []
        for r in results:
            agent_min = r.get("agent_minutes", "N/A")
            rows.append({
                "Repo": r["repo"],
                "Stars": r.get("stars", "N/A"),
                "Status": "✅" if r.get("transformation_status") == "success" else ("⚠️" if r.get("transformation_status") == "partial" else "❌"),
                "Build": "✅" if r.get("build_status") == "pass" else "❌",
                "Duration (s)": r.get("duration_seconds", "N/A"),
                "Agent Min": agent_min,
                "Cost": r.get("cost", "N/A"),
                "LOC": r.get("loc", "N/A"),
                "L2 Ratio": r.get("cdk_quality", {}).get("l2_ratio", "N/A"),
                "Plugins": len(r.get("plugins_migrated", [])),
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Summary metrics
        total = len(results)
        succeeded = sum(1 for r in results if r.get("transformation_status") == "success")
        builds_passed = sum(1 for r in results if r.get("build_status") == "pass")
        agent_mins = [float(r["agent_minutes"]) for r in results if r.get("agent_minutes") not in ("N/A", None)]
        total_cost = sum(m * 0.035 for m in agent_mins)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Success Rate", f"{succeeded}/{total}")
        col2.metric("Builds Passed", f"{builds_passed}/{total}")
        col3.metric("Total Agent Min", f"{sum(agent_mins):.1f}" if agent_mins else "N/A")
        col4.metric("Total Cost", f"${total_cost:.2f}" if agent_mins else "N/A")

        # Duration chart
        durations = [(r["repo"], r.get("duration_seconds", 0)) for r in results if r.get("duration_seconds")]
        if durations:
            st.subheader("Duration by Repo")
            chart_df = pd.DataFrame(durations, columns=["Repo", "Duration (s)"]).set_index("Repo")
            st.bar_chart(chart_df)

        # Agent minutes chart
        if agent_mins:
            st.subheader("Agent Minutes by Repo")
            am_data = [(r["repo"], float(r["agent_minutes"])) for r in results if r.get("agent_minutes") not in ("N/A", None)]
            am_df = pd.DataFrame(am_data, columns=["Repo", "Agent Minutes"]).set_index("Repo")
            st.bar_chart(am_df)

        # Detailed per-repo expandable sections
        st.subheader("Detailed Results")
        for r in results:
            with st.expander(f"{r['repo']} — {r.get('transformation_status', 'unknown')}"):
                col1, col2, col3 = st.columns(3)
                col1.write(f"**Stars:** {r.get('stars', 'N/A')}")
                col1.write(f"**LOC:** {r.get('loc', 'N/A')}")
                col2.write(f"**Agent Min:** {r.get('agent_minutes', 'N/A')}")
                col2.write(f"**Cost:** {r.get('cost', 'N/A')}")
                col3.write(f"**Duration:** {r.get('duration_seconds', 'N/A')}s")
                col3.write(f"**KIs:** {r.get('knowledge_items', 'N/A')}")

                if r.get("failure_reason"):
                    st.error(f"Failure: {r['failure_reason']}")

                criteria = r.get("criteria", {})
                if criteria:
                    st.write("**Validation Criteria:**")
                    crit_rows = [{"Criterion": k, "Status": v.get("status", ""), "Detail": v.get("detail", "")} for k, v in criteria.items()]
                    st.dataframe(pd.DataFrame(crit_rows), use_container_width=True, hide_index=True)

                issues = r.get("issues_encountered", [])
                if issues:
                    st.write(f"**Issues ({len(issues)}):**")
                    for i in issues:
                        st.write(f"- {i}")

                fixes = r.get("manual_fixes_needed", [])
                if fixes:
                    st.write(f"**Manual Fixes ({len(fixes)}):**")
                    for f in fixes:
                        st.write(f"- {f}")

                plugins = r.get("plugins_migrated", [])
                if plugins:
                    st.write(f"**Plugins Migrated:** {', '.join(plugins)}")

# ============================================================
# TAB 3: CDK Quality
# ============================================================
with tab_quality:
    st.header("CDK Code Quality")

    quality_data = []
    for path in sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json"))):
        with open(path) as f:
            r = json.load(f)
        q = r.get("cdk_quality", {})
        if q:
            quality_data.append({
                "Repo": r["repo"],
                "L2 Constructs": q.get("l2_constructs", 0),
                "Cfn Escape Hatches": q.get("cfn_escape_hatches", 0),
                "L2 Ratio": q.get("l2_ratio", 0) or 0,
                "TODOs": q.get("todo_comments", 0),
                "TS Files": q.get("total_ts_files", 0),
                "TS LOC": q.get("total_ts_loc", 0),
                "Constructs": ", ".join(q.get("constructs_used", [])) or "—",
            })

    if not quality_data:
        st.warning("No CDK quality data. Run `analyze_cdk_quality.py` or sync results with `--download`.")
    else:
        df = pd.DataFrame(quality_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # L2 ratio chart
        st.subheader("L2 Construct Ratio by Repo")
        ratio_df = df[["Repo", "L2 Ratio"]].set_index("Repo")
        st.bar_chart(ratio_df)

        # Stacked L2 vs Cfn
        st.subheader("L2 Constructs vs Cfn Escape Hatches")
        stacked_df = df[["Repo", "L2 Constructs", "Cfn Escape Hatches"]].set_index("Repo")
        st.bar_chart(stacked_df)

        # Averages
        avg_ratio = df["L2 Ratio"].mean()
        total_l2 = df["L2 Constructs"].sum()
        total_cfn = df["Cfn Escape Hatches"].sum()
        total_todos = df["TODOs"].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Avg L2 Ratio", f"{avg_ratio:.2f}")
        col2.metric("Total L2", total_l2)
        col3.metric("Total CfnResource", total_cfn)
        col4.metric("Total TODOs", total_todos)

# ============================================================
# TAB 4: Compare Runs
# ============================================================
with tab_compare:
    st.header("Compare Runs")
    st.info("Compare results across pipeline runs from S3. Requires `compare_runs.py`.")

    if st.button("Run Comparison (latest vs previous)"):
        with st.spinner("Comparing runs..."):
            rc, out = aws(f"python3 {os.path.join(PROJECT_DIR, 'scripts', 'compare_runs.py')} --profile {PROFILE or 'default'}")
            if rc == 0:
                st.markdown(out)
            else:
                st.error(f"Comparison failed: {out}")
