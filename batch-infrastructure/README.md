# Batch Benchmark Infrastructure

AWS Batch + Fargate Spot infrastructure for running ATX benchmarks at scale.

## Deploy

```bash
cd batch-infrastructure
npm install

# Set account/region
export AWS_PROFILE=demo
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION=us-east-1

# Bootstrap (first time only)
npx cdk bootstrap

# Deploy
npx cdk deploy
```

To reuse the existing pipeline S3 bucket:
```bash
npx cdk deploy -c existingResultsBucket=<bucket-name>
```

## Usage

```bash
# Submit all repos from config.yaml
python scripts/submit_batch.py --profile demo

# Submit single repo
python scripts/submit_batch.py --profile demo --repo aws-lambda-typescript

# Check status
python scripts/submit_batch.py --profile demo --status

# Wait until all complete
python scripts/submit_batch.py --profile demo --status --wait

# Sync results and regenerate BENCHMARKS.md
python scripts/sync_results.py --profile demo --bucket <batch-results-bucket>
```

## Architecture

- **Fargate Spot** — ~70% cheaper than on-demand, safe because ATX is resumable
- **One job per repo** — parallel execution, independent retries
- **Public ATX container** — `public.ecr.aws/b7y6j9m3/aws-transform-custom:latest`
- **No pipeline** — submit jobs on demand, no infra changes when adding repos

## Cleanup

```bash
npx cdk destroy
```
