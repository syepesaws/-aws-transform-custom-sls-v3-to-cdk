#!/usr/bin/env python3
"""Search GitHub for Serverless Framework v3 repos with >100 stars and write candidates to config.yaml."""

import json
import os
import sys
import time
import requests
import yaml

GITHUB_API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    sys.exit("Error: GITHUB_TOKEN environment variable required")

HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
MIN_STARS = 100
MAX_CANDIDATES = 30  # fetch more than 5 so you can curate


def search_repos(page=1, per_page=30):
    """Search for repos containing serverless.yml with >100 stars."""
    resp = requests.get(
        f"{GITHUB_API}/search/code",
        headers=HEADERS,
        params={
            "q": f"filename:serverless.yml stars:>{MIN_STARS}",
            "per_page": per_page,
            "page": page,
        },
    )
    if resp.status_code == 403:
        reset = int(resp.headers.get("X-RateLimit-Reset", 0))
        wait = max(reset - int(time.time()), 10)
        print(f"Rate limited. Waiting {wait}s...")
        time.sleep(wait)
        return search_repos(page, per_page)
    resp.raise_for_status()
    return resp.json()


def get_repo_details(owner, repo):
    """Fetch repo metadata."""
    resp = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def detect_serverless_features(owner, repo):
    """Read serverless.yml and detect features/plugins."""
    resp = requests.get(
        f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/serverless.yml",
        headers=HEADERS,
    )
    if resp.status_code != 200:
        return {"plugins": [], "resources": [], "functions_count": 0}

    try:
        sls = yaml.safe_load(resp.text)
    except yaml.YAMLError:
        return {"plugins": [], "resources": [], "functions_count": 0}

    if not isinstance(sls, dict):
        return {"plugins": [], "resources": [], "functions_count": 0}

    plugins = sls.get("plugins") or []
    functions = sls.get("functions") or {}
    resources = list((sls.get("resources", {}) or {}).get("Resources", {}).keys()) if isinstance(sls.get("resources"), dict) else []

    return {
        "plugins": plugins if isinstance(plugins, list) else [],
        "resources": resources[:10],
        "functions_count": len(functions) if isinstance(functions, dict) else 0,
    }


def main():
    print(f"Searching GitHub for repos with serverless.yml (stars>{MIN_STARS})...")
    seen = set()
    candidates = []

    for page in range(1, 4):  # up to 3 pages
        data = search_repos(page=page)
        for item in data.get("items", []):
            full_name = item["repository"]["full_name"]
            if full_name in seen:
                continue
            seen.add(full_name)

            owner, repo = full_name.split("/")
            try:
                details = get_repo_details(owner, repo)
            except requests.HTTPError:
                continue

            if details.get("archived") or details.get("fork"):
                continue

            features = detect_serverless_features(owner, repo)

            candidates.append({
                "name": repo,
                "url": details["html_url"],
                "stars": details["stargazers_count"],
                "language": details.get("language"),
                "plugins": features["plugins"],
                "resources": features["resources"],
                "functions_count": features["functions_count"],
            })
            print(f"  ★ {details['stargazers_count']:>5}  {full_name} — {features['functions_count']} fns, {len(features['plugins'])} plugins")

            if len(candidates) >= MAX_CANDIDATES:
                break
            time.sleep(1)  # respect rate limits

        if len(candidates) >= MAX_CANDIDATES:
            break
        time.sleep(5)

    # Sort by stars descending
    candidates.sort(key=lambda c: c["stars"], reverse=True)

    # Write config
    config = {
        "transformation_name": "sls-v3-to-cdk",
        "build_command": "npx cdk synth",
        "repos": [
            {"url": c["url"], "name": c["name"], "stars": c["stars"], "plugins": c["plugins"]}
            for c in candidates
        ],
    }

    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"\nWrote {len(candidates)} candidates to {CONFIG_PATH}")
    print("Review and trim to your top 5 before running benchmarks.")


if __name__ == "__main__":
    main()
