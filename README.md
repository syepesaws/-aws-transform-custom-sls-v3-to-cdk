# AWS Transform Custom — Serverless Framework v3 to CDK Benchmark

Benchmarking suite for evaluating [AWS Transform Custom](https://docs.aws.amazon.com/transform/latest/userguide/custom.html) on real-world Serverless Framework v3 → AWS CDK TypeScript migrations.

## Project Structure

```
transformation-definitions/
  td-sls-v3-to-cdk/          # ATX transformation definition (publishable)
examples/                     # Sample repos for manual testing
benchmark-results/            # Per-repo JSON results + aggregated report
scripts/
  scrape_repos.py             # GitHub search for candidate repos
  run_benchmark.sh            # ATX execution wrapper with telemetry
  aggregate_results.py        # Parse results → BENCHMARKS.md
config.yaml                   # Repo candidates + benchmark parameters
BENCHMARKS.md                 # Results summary
```

## Prerequisites

- AWS Transform CLI (`atx`) installed and configured
- Python 3.9+ with `requests` (`pip install requests`)
- GitHub personal access token (for API search) exported as `GITHUB_TOKEN`
- `jq`, `git`

## Quick Start

```bash
# 1. Discover candidate repos
python scripts/scrape_repos.py

# 2. Review/edit config.yaml with selected repos

# 3. Publish the transformation definition (or use a draft)
atx custom def publish -n sls-v3-to-cdk \
  --description "Serverless Framework v3 to AWS CDK TypeScript" \
  --sd transformation-definitions/td-sls-v3-to-cdk

# 4. Run benchmarks
bash scripts/run_benchmark.sh

# 5. Aggregate results
python scripts/aggregate_results.py
```

## Benchmark Metrics

Each execution captures:
- Transformation success/failure status
- Build/validation command output (`cdk synth`)
- Time taken (wall clock)
- Agent minutes consumed
- Knowledge items generated
- Manual fixes required
- Code quality observations

See [BENCHMARKS.md](BENCHMARKS.md) for latest results.
