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
  run_benchmark.py            # ATX execution wrapper with telemetry
  aggregate_results.py        # Parse results → BENCHMARKS.md
  analyze_cdk_quality.py      # Static analysis of generated CDK code
  log_fixes.py                # Track manual fixes per repo
  compare_runs.py             # Regression tracking across pipeline runs
  sync_results.py             # Download results from S3
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
python scripts/run_benchmark.py

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

## Post-Run Analysis

```bash
# CDK code quality analysis (L2 vs CfnResource, TODOs, construct usage)
python scripts/analyze_cdk_quality.py                     # all repos in .workdir/
python scripts/analyze_cdk_quality.py --repo <name>       # single repo

# Log manual fixes after reviewing a transformation
python scripts/log_fixes.py <repo> --fix "Description" --category iam
python scripts/log_fixes.py <repo> --issue "Description"
python scripts/log_fixes.py <repo> --show

# Compare runs for regression tracking (reads from S3)
python scripts/compare_runs.py --profile demo                              # latest vs previous
python scripts/compare_runs.py --profile demo --baseline <id> --current <id>
```

## Pipeline (CodeBuild / CodePipeline)

For parallelized remote execution, a CDK project is provided in `benchmark-pipeline/`.

### Architecture

```
CodePipeline
  ├─ Source: GitLab (CodeConnection)
  ├─ Benchmark: 5 parallel CodeBuild actions (one per repo)
  │   └─ Each: clone → atx exec → build validation → upload to S3
  └─ Aggregate: collect results → generate BENCHMARKS.md → upload to S3
```

### Deploy

```bash
# 1. Create a CodeConnection to GitLab in the AWS Console and note the ARN

# 2. Deploy the pipeline stack
cd benchmark-pipeline
npm install
npx cdk deploy --parameters ConnectionArn=arn:aws:codeconnections:REGION:ACCOUNT:connection/ID

# 3. Approve the CodeConnection in the AWS Console (pending status after first deploy)
```

### S3 Results Structure

```
s3://benchmark-bucket/
  runs/<timestamp>/
    <repo-name>/result.json    # benchmark metrics
    <repo-name>/atx.log        # full ATX output
    <repo-name>/build.log      # build validation output
    BENCHMARKS.md              # aggregated report
  latest/BENCHMARKS.md         # always points to most recent run
```

See [BENCHMARKS.md](BENCHMARKS.md) for latest results.
