#!/usr/bin/env python3
"""Aggregate per-repo JSON results into BENCHMARKS.md."""

import json
import glob
import os
from datetime import datetime, timezone

PROJECT_DIR = os.path.join(os.path.dirname(__file__), "..")
RESULTS_DIR = os.path.join(PROJECT_DIR, "benchmark-results")
OUTPUT = os.path.join(PROJECT_DIR, "BENCHMARKS.md")


def load_results():
    results = []
    for path in sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json"))):
        with open(path) as f:
            results.append(json.load(f))
    return results


def status_icon(s):
    return "✅" if s == "success" else "❌"


def build_icon(s):
    return {"pass": "✅", "fail": "❌"}.get(s, "⏭️")


def generate_markdown(results):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(results)
    success = sum(1 for r in results if r["transformation_status"] == "success")
    builds = sum(1 for r in results if r["build_status"] == "pass")

    lines = [
        "# Benchmark Results\n",
        f"> Last updated: {now}\n",
        f"**{success}/{total}** transformations succeeded | **{builds}/{total}** builds passed\n",
    ]

    # Total cost
    total_cost = sum(float(r["agent_minutes"]) * 0.035 for r in results if r.get("agent_minutes", "N/A") != "N/A")
    total_agent_min = sum(float(r["agent_minutes"]) for r in results if r.get("agent_minutes", "N/A") != "N/A")
    lines.append(f"**Total agent minutes**: {total_agent_min:.2f} | **Total cost**: ${total_cost:.2f} (@ $0.035/min)\n")

    lines.extend([
        "## Summary\n",
        "| Repository | Status | Build | Time (s) | Agent Min | Cost | Knowledge Items |",
        "|------------|--------|-------|----------|-----------|------|-----------------|",
    ])

    for r in results:
        cost = r.get("cost", "N/A")
        lines.append(
            f"| [{r['repo']}]({r['url']}) "
            f"| {status_icon(r['transformation_status'])} "
            f"| {build_icon(r['build_status'])} "
            f"| {r['duration_seconds']} "
            f"| {r['agent_minutes']} "
            f"| {cost} "
            f"| {r['knowledge_items']} |"
        )

    lines.append("\n## Detailed Results\n")

    for r in results:
        name = r["repo"]
        lines.append(f"### {name}\n")
        lines.append(f"- **URL**: {r['url']}")
        lines.append(f"- **Status**: {status_icon(r['transformation_status'])} {r['transformation_status']}")
        if r.get("failure_reason"):
            lines.append(f"- **Failure reason**: {r['failure_reason']}")
        lines.append(f"- **Build**: {build_icon(r['build_status'])} {r['build_status']}")
        lines.append(f"- **Time taken**: {r['duration_seconds']}s")
        lines.append(f"- **Agent minutes**: {r['agent_minutes']}")
        lines.append(f"- **Cost**: {r.get('cost', 'N/A')}")
        lines.append(f"- **Knowledge items**: {r['knowledge_items']}")

        # Include build log snippet if exists
        build_log = os.path.join(RESULTS_DIR, f"{name}_build.log")
        if os.path.exists(build_log) and r["build_status"] == "fail":
            with open(build_log) as f:
                tail = f.readlines()[-20:]
            lines.append(f"\n<details><summary>Build log (last 20 lines)</summary>\n")
            lines.append("```")
            lines.extend(l.rstrip() for l in tail)
            lines.append("```\n</details>\n")
        else:
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
