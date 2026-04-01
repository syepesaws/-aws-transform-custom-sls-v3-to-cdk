# Migrate Serverless Framework v3 to AWS CDK TypeScript

## Objective
Convert Serverless Framework v3 applications to AWS CDK TypeScript with native L2 constructs for better type safety, per-function IAM roles, and full AWS service integration.

## Entry Criteria
1. Valid `serverless.yml` (Serverless Framework v3) at the repository root or in a clearly identifiable subdirectory
2. AWS provider configuration (`provider.name: aws`)
3. Valid `package.json` with serverless dependencies
4. The repository must build/deploy successfully in its current Serverless Framework state
5. Node.js or TypeScript runtime for Lambda functions (Python/Go/Java runtimes are out of scope)
6. For monorepos with multiple `serverless.yml` files: each service is treated as a separate CDK stack

## Implementation Steps

### 1. Processing & Partitioning

Before making any changes, analyze the repository to understand its full scope:

1. Locate and parse `serverless.yml` — extract:
   - `provider` block (runtime, region, stage, memory, timeout, environment, IAM statements, VPC config)
   - All `functions` and their event sources (http, httpApi, sqs, sns, s3, dynamodb, schedule, eventBridge)
   - `resources.Resources` block (raw CloudFormation)
   - `plugins` list
   - `custom` block (plugin configurations, stage variables)
2. Analyze `package.json` — identify serverless-related dependencies and build tooling
3. Identify project variations and set conditional flags:
   - **[Has API Gateway]** — any function has `http` or `httpApi` events
   - **[Has Event Sources]** — any function has `sqs`, `sns`, `s3`, `dynamodb`, `schedule`, or `eventBridge` events
   - **[Has Custom Domain]** — `serverless-domain-manager` plugin present
   - **[Has VPC]** — `provider.vpc` or per-function `vpc` config present
   - **[Has Layers]** — `layers` defined at provider or function level
   - **[Has Custom Resources]** — `resources.Resources` block is non-empty
4. Count total functions, event sources, plugins, and CloudFormation resources to estimate scope
5. Create a prioritized migration order:
   1. Project scaffolding (CDK init, package.json, cdk.json)
   2. Shared infrastructure (VPC, DynamoDB tables, S3 buckets from `resources`)
   3. Lambda functions with IAM permissions
   4. **[Has API Gateway]** API Gateway configuration
   5. **[Has Event Sources]** Event source mappings
   6. **[Has Custom Domain]** Custom domain setup
   7. Outputs, cleanup, and documentation

### 2. Initialize CDK Project

1. Run `cdk init app --language typescript` (or scaffold manually if files already exist)
2. Create `cdk.json` with app entry point, feature flags, and exclude patterns
3. Update `package.json`:
   - Add `aws-cdk-lib`, `constructs`, `aws-cdk-lib/aws-lambda-nodejs` as dependencies
   - Update `scripts` to use CDK CLI (`cdk synth`, `cdk deploy`, `cdk diff`)
   - Remove serverless dependencies (`serverless`, all `serverless-*` plugins)
4. Run `npm install` to verify dependency resolution

**CRITICAL: Run `npx cdk synth` after this step to verify the empty stack compiles.**

### 3. Migrate Shared Infrastructure

Convert `resources.Resources` from `serverless.yml` to CDK constructs:

1. **[Has Custom Resources]** For each CloudFormation resource in `resources.Resources`:
   - Use L2 constructs where available (Table, Bucket, Queue, Topic, etc.)
   - Fall back to `CfnResource` only when no L2 construct exists
   - Preserve logical IDs where they are referenced by other resources
2. Migrate `provider.environment` variables that reference resources (use CDK references like `table.tableName`)

**CRITICAL: Run `npx cdk synth` after this step.**

### 4. Transform Lambda Functions and IAM

See `document_references/07-lambda-apigateway-events-transformation.md` for detailed patterns.

For each function in `serverless.yml`:

1. Create a `NodejsFunction` with:
   - `entry`: path to the handler file
   - `handler`: export name (default: `handler`)
   - `runtime`: from `provider.runtime` or per-function override
   - `memorySize`, `timeout`, `environment` from provider defaults + function overrides
   - `bundling`: configure based on original build tooling (see plugin migration below)
2. Migrate IAM permissions:
   - Convert `provider.iam.role.statements` to `PolicyStatement` with `addToRolePolicy()`
   - Prefer grant methods (`table.grantReadWriteData(fn)`, `bucket.grantRead(fn)`) over raw policy statements
   - Each function gets its own IAM role by default in CDK (replaces `serverless-iam-roles-per-function`)
3. **[Has VPC]** Configure VPC: `vpc`, `vpcSubnets`, `securityGroups`
4. **[Has Layers]** Migrate layers to `LayerVersion` constructs
5. Configure observability: `tracing: Tracing.ACTIVE`, `logRetention: RetentionDays.ONE_MONTH`

**CRITICAL: Run `npx cdk synth` after this step.**

### 5. [Has API Gateway] Configure API Gateway

1. Create `RestApi` (for `http` events) or `HttpApi` (for `httpApi` events)
2. For each function with HTTP events:
   - Create resources for paths, add methods with `LambdaIntegration`
   - Configure CORS if specified in `serverless.yml`
3. Create `CfnOutput` for API endpoint URL

**CRITICAL: Run `npx cdk synth` after this step.**

### 6. [Has Event Sources] Migrate Event Source Mappings

For each non-HTTP event source:
- **SQS**: `SqsEventSource` with batch size, window, etc.
- **SNS**: `SnsEventSource` with filter policy
- **DynamoDB Streams**: `DynamoEventSource` with starting position, batch size
- **S3**: `S3EventSource` with event type and prefix/suffix filters
- **Schedule**: `Rule` with `Schedule.expression()` targeting the function
- **EventBridge**: `Rule` with event pattern targeting the function

**CRITICAL: Run `npx cdk synth` after this step.**

### 7. Replace Plugins

See `document_references/` for detailed mappings per plugin:

| Serverless Plugin | CDK Equivalent | Reference |
|------------------|----------------|-----------|
| `serverless-webpack` | NodejsFunction bundling (esbuild) | `01-serverless-webpack-to-cdk.md` |
| `serverless-esbuild` | NodejsFunction bundling (default) | Built-in |
| `serverless-bundle` | NodejsFunction bundling (default) | Built-in |
| `serverless-plugin-typescript` | NodejsFunction bundling (default) | Built-in |
| `serverless-domain-manager` | DomainName + Certificate + Route53 | `02-serverless-domain-manager-to-cdk.md` |
| `serverless-offline` | AWS SAM CLI | `03-serverless-offline-to-cdk.md` |
| `serverless-iam-roles-per-function` | Default CDK behavior | `04-serverless-iam-roles-per-function-to-cdk.md` |
| `serverless-plugin-tracing` | `tracing: Tracing.ACTIVE` | `05-serverless-plugin-tracing-to-cdk.md` |
| `serverless-plugin-log-retention` | `logRetention: RetentionDays.*` | `06-serverless-plugin-log-retention-to-cdk.md` |
| `serverless-pseudo-parameters` | Native CDK references (`this.account`, `this.region`) | Inline |
| `serverless-dotenv-plugin` | `dotenv` package or CDK context | Inline |
| `serverless-plugin-include-dependencies` | NodejsFunction bundling handles this | Built-in |
| `serverless-apigw-binary` | `binaryMediaTypes` on RestApi | Inline |
| `serverless-s3-deploy` | `BucketDeployment` from `aws-s3-deployment` | Inline |

For plugins not listed: document them in the validation report as unsupported and note what manual action is needed.

### 8. Migrate Stage Variables and Configuration

1. Convert `${self:custom.*}` and `${opt:stage}` references to CDK context or environment-based stack instantiation
2. Replace `${ssm:*}` references with `StringParameter.valueForStringParameter()`
3. Replace `${env:*}` references with `process.env.*`

### 9. Create Outputs and Update Documentation

1. Create `CfnOutput` for API endpoints, function ARNs, resource ARNs
2. Update `README.md` to reflect CDK commands (`cdk synth`, `cdk deploy`, `cdk diff`) instead of `serverless deploy`
3. **If CI/CD config exists**: Replace `serverless deploy` with `cdk synth && cdk deploy`

### 10. Final Validation and Cleanup

1. Remove `node_modules` and `package-lock.json`, run `npm install` from clean state
2. Run `npx cdk synth` — must succeed with zero errors
3. Verify no `serverless` dependencies remain in `package.json`
4. Verify `cdk.json` is properly configured
5. Write the `validation_report.json` (see below)
6. **CRITICAL: Clean up build artifacts** — after writing `validation_report.json`, delete the following directories to reduce upload size:
   - `node_modules/`
   - `cdk.out/`

## Constraints and Guardrails

1. Prefer L2 constructs over `CfnResource` escape hatches in all cases where an L2 exists
2. Preserve all existing code comments
3. Preserve original licensing information without modifications
4. Remove any temporary debugging code introduced during transformation
5. Do not modify Lambda handler business logic — only change infrastructure wiring
6. Run `npx cdk synth` after each major step (as marked with CRITICAL above) and fix errors before proceeding
7. If `npm install` fails with `ERESOLVE`, retry with `--legacy-peer-deps` and document the reason
8. Do not hardcode AWS account IDs or regions — use `this.account` and `this.region`
9. Use `RemovalPolicy.RETAIN` for stateful resources (DynamoDB tables, S3 buckets) to match Serverless Framework default behavior

## Known Debug Patterns & Troubleshooting

- **`cdk synth` fails with "Cannot find module"**: Ensure `entry` paths in `NodejsFunction` are correct relative to the project root, not relative to the stack file
- **Circular dependency between stacks**: Extract shared resources into a separate construct or use `CfnOutput`/`Fn.importValue`
- **"Maximum call stack size exceeded" during synth**: Usually caused by circular references in construct tree — check parent/child relationships
- **esbuild bundling fails**: Check that handler files exist at the specified `entry` path and that `tsconfig.json` is valid
- **Missing environment variables**: Ensure all `${self:custom.*}` references are resolved — CDK doesn't have Serverless variable resolution
- **API Gateway 403/Missing Authentication**: Check that methods are configured with `AuthorizationType.NONE` if the original had no authorizer

## CRITICAL: Validation Report Output

After completing all implementation steps and validation, you MUST write a file called `validation_report.json` in the root of the repository. This file is consumed by automated benchmarking and MUST follow this exact schema:

```json
{
  "transformation_status": "success | partial | failure",
  "summary": "Brief description of the transformation outcome",
  "criteria": {
    "cdk_synth": { "status": "PASS | FAIL | SKIP", "detail": "..." },
    "lambda_functions": { "status": "PASS | FAIL | SKIP", "detail": "..." },
    "api_gateway": { "status": "PASS | FAIL | SKIP | N/A", "detail": "..." },
    "iam_permissions": { "status": "PASS | FAIL | SKIP", "detail": "..." },
    "environment_variables": { "status": "PASS | FAIL | SKIP", "detail": "..." },
    "event_sources": { "status": "PASS | FAIL | SKIP | N/A", "detail": "..." },
    "no_serverless_deps": { "status": "PASS | FAIL | SKIP", "detail": "..." },
    "cdk_json": { "status": "PASS | FAIL | SKIP", "detail": "..." },
    "clean_install": { "status": "PASS | FAIL | SKIP", "detail": "..." }
  },
  "issues_encountered": ["list of issues found and how they were resolved"],
  "manual_fixes_needed": ["list of items that could not be automatically resolved"],
  "plugins_migrated": ["list of serverless plugins that were migrated"],
  "plugins_unsupported": ["list of plugins with no CDK equivalent"],
  "functions_count": 0,
  "resources_count": 0
}
```

Rules for the report:
- Use "PASS" only when the criterion was verified and passed
- Use "FAIL" when the criterion was verified and failed
- Use "SKIP" when the criterion cannot be verified locally
- Use "N/A" when the criterion does not apply (e.g., no API Gateway, no event sources)
- Set `transformation_status` to "success" if all applicable criteria pass, "partial" if some fail, "failure" if critical criteria (cdk_synth, lambda_functions, no_serverless_deps) fail
- IMPORTANT: Write this file even if the transformation encounters errors
