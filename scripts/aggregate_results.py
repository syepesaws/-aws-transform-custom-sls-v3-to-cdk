#!/usr/bin/env python3
"""Aggregate per-repo JSON results into BENCHMARKS.md."""

import json
import re
import glob
import os
from datetime import datetime, timezone

PROJECT_DIR = os.path.join(os.path.dirname(__file__), "..")
RESULTS_DIR = os.path.join(PROJECT_DIR, "benchmark-results")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.yaml")
OUTPUT = os.path.join(PROJECT_DIR, "BENCHMARKS.md")


def load_config():
    """Load config.yaml to enrich results with repo metadata."""
    if not os.path.exists(CONFIG_PATH):
        return {}
    import yaml
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    return {r["name"]: r for r in config.get("repos", [])}


def load_results():
    repo_meta = load_config()
    results = []
    for path in sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json"))):
        with open(path) as f:
            r = json.load(f)
        # Enrich from config.yaml when result JSON is missing metadata
        meta = repo_meta.get(r["repo"], {})
        if r.get("stars") in (None, "N/A"):
            r["stars"] = meta.get("stars", "N/A")
        if r.get("loc") in (None, "N/A"):
            r["loc"] = "N/A"
        if r.get("plugins_migrated") in (None, []) and meta.get("plugins"):
            r.setdefault("plugins_migrated", meta["plugins"])
        results.append(r)
    return results


def status_icon(s):
    return {"success": "✅", "partial": "⚠️", "failure": "❌"}.get(s, "❓")


def compute_criteria_score(r):
    """Return (passed, total_verifiable, effective_status) from criteria.

    When no criteria exist, derive a simple score from build_status + transformation_status
    so the summary table always shows something meaningful.
    """
    criteria = r.get("criteria", {})
    if not criteria:
        # Fallback: synthesize a score from the two booleans we always have
        passed = 0
        total = 2
        if r.get("transformation_status") == "success":
            passed += 1
        if r.get("build_status") == "pass":
            passed += 1
        status = "success" if passed == total else ("partial" if passed > 0 else "failure")
        return passed, total, status
    passed = sum(1 for v in criteria.values() if v.get("status") == "PASS")
    verifiable = sum(1 for v in criteria.values() if v.get("status") in ("PASS", "FAIL"))
    if verifiable == 0:
        return passed, verifiable, r.get("transformation_status", "unknown")
    if passed == verifiable:
        status = "success"
    elif passed > 0:
        status = "partial"
    else:
        status = "failure"
    return passed, verifiable, status


def build_icon(s):
    return {"pass": "✅", "fail": "❌"}.get(s, "⏭️")


def generate_markdown(results):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(results)
    scores = [compute_criteria_score(r) for r in results]
    success = sum(1 for _, _, s in scores if s == "success")
    partial = sum(1 for _, _, s in scores if s == "partial")
    builds = sum(1 for r in results if r["build_status"] == "pass")
    atx_success = sum(1 for r in results if r.get("atx_status") == "success")

    lines = [
        "# Benchmark Results\n",
        f"> Last updated: {now}\n",
        f"**{success}/{total}** succeeded | **{partial}/{total}** partial | **{builds}/{total}** builds passed | **{atx_success}/{total}** ATX reported success\n",
    ]

    # Total cost
    total_cost = sum(float(r["agent_minutes"]) * 0.035 for r in results if r.get("agent_minutes", "N/A") != "N/A")
    total_agent_min = sum(float(r["agent_minutes"]) for r in results if r.get("agent_minutes", "N/A") != "N/A")
    lines.append(f"**Total agent minutes**: {total_agent_min:.2f} | **Total cost**: ${total_cost:.2f} (@ $0.035/min)\n")

    lines.extend([
        "## Summary\n",
        "| Repository | Stars | Fns | Plugins | Status | Score | Build | Time (s) | Agent Min | Cost | Files Δ | Lines +/- |",
        "|------------|-------|-----|---------|--------|-------|-------|----------|-----------|------|---------|-----------|",
    ])

    for r in results:
        cost = r.get("cost", "N/A")
        stars = r.get("stars", "N/A")
        fns = r.get("functions_count", "N/A")
        plugins = r.get("plugins_migrated", [])
        plugin_count = len(plugins) if isinstance(plugins, list) else "N/A"
        passed, verifiable, effective_status = compute_criteria_score(r)
        score = f"{passed}/{verifiable}"
        gd = r.get("git_diff", {})
        files_changed = gd.get("files_changed", "N/A")
        lines_plus_minus = f"+{gd['lines_added']}/-{gd['lines_deleted']}" if gd.get("lines_added") is not None else "N/A"
        lines.append(
            f"| [{r['repo']}]({r['url']}) "
            f"| {stars} "
            f"| {fns} "
            f"| {plugin_count} "
            f"| {status_icon(effective_status)} "
            f"| {score} "
            f"| {build_icon(r['build_status'])} "
            f"| {r['duration_seconds']} "
            f"| {r['agent_minutes']} "
            f"| {cost} "
            f"| {files_changed} "
            f"| {lines_plus_minus} |"
        )

    lines.append("\n## Detailed Results\n")

    for r in results:
        name = r["repo"]
        lines.append(f"### {name}\n")
        lines.append(f"- **URL**: {r['url']}")
        lines.append(f"- **Stars**: {r.get('stars', 'N/A')}")
        lines.append(f"- **LOC**: {r.get('loc', 'N/A')}")
        lines.append(f"- **Status**: {status_icon(r['transformation_status'])} {r['transformation_status']}")
        passed, verifiable, effective_status = compute_criteria_score(r)
        if verifiable is not None:
            lines.append(f"- **Validation score**: {passed}/{verifiable} criteria passed → {status_icon(effective_status)} {effective_status}")
        if r.get("failure_reason"):
            clean_reason = re.sub(r"\x1b\[[0-9;]*m", "", r["failure_reason"])
            lines.append(f"- **Failure reason**: {clean_reason}")
        lines.append(f"- **Build**: {build_icon(r['build_status'])} {r['build_status']}")
        lines.append(f"- **Time taken**: {r['duration_seconds']}s")
        lines.append(f"- **Agent minutes**: {r['agent_minutes']}")
        lines.append(f"- **Cost**: {r.get('cost', 'N/A')}")

        gd = r.get("git_diff", {})
        if gd and gd.get("files_changed"):
            lines.append(f"- **Git diff**: {gd['files_changed']} files changed, +{gd.get('lines_added', 0)} -{gd.get('lines_deleted', 0)} ~{gd.get('lines_modified', 0)}")

        # Build log snippet on failure
        build_log = os.path.join(RESULTS_DIR, f"{name}_build.log")
        if os.path.exists(build_log) and r["build_status"] == "fail":
            with open(build_log) as f:
                tail = f.readlines()[-20:]
            lines.append(f"\n<details><summary>Build log (last 20 lines)</summary>\n")
            lines.append("```")
            lines.extend(l.rstrip() for l in tail)
            lines.append("```\n</details>\n")

        # Validation criteria
        criteria = r.get("criteria", {})
        if criteria:
            lines.append("")
            lines.append("| Criterion | Status | Detail |")
            lines.append("|-----------|--------|--------|")
            for key, val in criteria.items():
                icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "N/A": "➖"}.get(val.get("status", ""), "❓")
                lines.append(f"| {key} | {icon} {val.get('status', '')} | {val.get('detail', '')} |")

        # Issues and manual fixes
        issues = r.get("issues_encountered", [])
        if issues:
            lines.append(f"\n**Issues encountered**: {len(issues)}")
            for issue in issues:
                lines.append(f"- {issue}")

        fixes = r.get("manual_fixes_needed", [])
        if fixes:
            lines.append(f"\n**Manual fixes needed**: {len(fixes)}")
            for fix in fixes:
                lines.append(f"- {fix}")

        plugins = r.get("plugins_migrated", [])
        if plugins:
            lines.append(f"\n**Plugins migrated**: {', '.join(plugins)}")

        # CDK quality metrics
        q = r.get("cdk_quality", {})
        if q:
            lines.append(f"\n**CDK Quality**:")
            lines.append(f"- L2 constructs: {q.get('l2_constructs', 0)} | Cfn escape hatches: {q.get('cfn_escape_hatches', 0)} | L2 ratio: {q.get('l2_ratio', 'N/A')}")
            lines.append(f"- TODO/FIXME comments: {q.get('todo_comments', 0)}")
            if q.get("constructs_used"):
                lines.append(f"- Constructs used: {', '.join(q['constructs_used'])}")
            if q.get("issues"):
                for qi in q["issues"]:
                    lines.append(f"- ⚠️ {qi}")

        lines.append("")

    return "\n".join(lines)


def main():
    results = load_results()
    if not results:
        print("No results found in benchmark-results/. Run run_benchmark.sh first.")
        return

    md = generate_markdown(results)
    with open(OUTPUT, "w") as f:
        f.write(md)

    print(f"Wrote {OUTPUT} with {len(results)} results.")


if __name__ == "__main__":
    main()
