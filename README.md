# AWS Transform Custom — Serverless Framework v3 to CDK Benchmark

Benchmarking suite for evaluating [AWS Transform Custom](https://docs.aws.amazon.com/transform/latest/userguide/custom.html) on real-world Serverless Framework v3 → AWS CDK TypeScript migrations.

## Project Structure

```
transformation-definitions/
  td-sls-v3-to-cdk/          # ATX transformation definition (publishable)
batch-infrastructure/         # CDK stack for AWS Batch + Fargate Spot
benchmark-results/            # Per-repo JSON results
scripts/
  scrape_repos.py             # GitHub search for candidate repos
  submit_batch.py             # Submit benchmark jobs to AWS Batch
  sync_batch_results.py       # Download validation reports from S3
  aggregate_results.py        # Parse results → BENCHMARKS.md
  analyze_cdk_quality.py      # Static analysis of generated CDK code
  compare_runs.py             # Regression tracking across runs
  log_fixes.py                # Track manual fixes per repo
config.yaml                   # Repo candidates + benchmark parameters
dashboard.py                  # Streamlit dashboard for monitoring
BENCHMARKS.md                 # Results summary
```

## Prerequisites

- AWS Transform CLI (`atx`) installed and configured
- Python 3.9+ with `pyyaml`, `streamlit`
- GitHub personal access token exported as `GITHUB_TOKEN` (for repo discovery)
- AWS CLI configured with a profile that has Batch + S3 access

## Quick Start

```bash
# 1. Discover candidate repos
python scripts/scrape_repos.py

# 2. Review/edit config.yaml with selected repos

# 3. Publish the transformation definition
atx custom def publish -n sls-v3-to-cdk \
  --description "Serverless Framework v3 to AWS CDK TypeScript" \
  --sd transformation-definitions/td-sls-v3-to-cdk

# 4. Deploy Batch infrastructure (first time only)
cd batch-infrastructure && npm install
npx cdk deploy

# 5. Submit benchmark jobs
python scripts/submit_batch.py --profile demo

# 6. Monitor progress
python scripts/submit_batch.py --profile demo --status --wait

# 7. Sync results and generate report
python scripts/sync_batch_results.py --profile demo
```

## Dashboard

```bash
AWS_PROFILE=demo streamlit run dashboard.py
```

Features:
- **Live Status** — real-time Batch job monitoring with auto-refresh
- **Results** — benchmark summary with criteria scores, plugins migrated, issues
- **CDK Quality** — L2 vs CfnResource analysis, construct inventory
- **Compare Runs** — regression tracking across executions
- **Log Viewer** — paginated CloudWatch logs per repo with live tail

## Architecture

```
AWS Batch (Fargate Spot)
  ├─ 1 job per repo (parallel)
  │   └─ Public ATX container: clone → atx exec → upload to S3
  └─ Results: validation_report.json per repo in S3
```

- **No pipeline** — submit jobs on demand, no infra changes when adding repos
- **Fargate Spot** — ~70% cheaper than on-demand
- **Per-repo retry** — resubmit individual repos without re-running everything

## Benchmark Metrics

Each execution captures (via `validation_report.json`):
- Transformation status and per-criterion pass/fail
- Functions count and plugins migrated
- Issues encountered and manual fixes needed
- Duration (from Batch job timestamps)

## Post-Run Analysis

```bash
# Sync results from latest Batch run
python scripts/sync_batch_results.py --profile demo

# Compare runs for regression tracking
python scripts/compare_runs.py --profile demo

# CDK code quality analysis (requires --download on sync)
python scripts/sync_batch_results.py --profile demo --download
python scripts/analyze_cdk_quality.py

# Log manual fixes after reviewing a transformation
python scripts/log_fixes.py <repo> --fix "Description" --category iam
```

See [BENCHMARKS.md](BENCHMARKS.md) for latest results.
