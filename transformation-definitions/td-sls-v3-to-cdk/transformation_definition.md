# Migrate Serverless Framework v3 to AWS CDK TypeScript

## Objective
Convert Serverless Framework v3 applications to AWS CDK TypeScript with native constructs for better type safety and AWS service integration.

## Entry Criteria
1. Valid serverless.yml (Serverless Framework v3)
2. Node.js runtime for Lambda functions
3. AWS provider configuration
4. Valid package.json with serverless dependencies

## Implementation Steps

1. **Initialize CDK project**: Run `cdk init app --language typescript`

2. **Parse serverless.yml**: Extract provider config (runtime, region, stage, memory, timeout, environment, IAM)

3. **Create CDK Stack**: Extend `cdk.Stack`, set stack name from service+stage

4. **Transform Lambda functions, API Gateway, and event sources**: See `document_references/07-lambda-apigateway-events-transformation.md` for:
   - Lambda function conversion (NodejsFunction with entry, handler, runtime, memory, timeout, environment)
   - API Gateway HTTP events (RestApi, LambdaIntegration, paths, methods, CORS)
   - Event source mappings (DynamoDB Streams, SQS, SNS, S3, EventBridge)
   - VPC configuration, layers, DLQ, reserved concurrency

5. **Migrate IAM**: Convert `provider.iam.role.statements` to `PolicyStatement`, use `addToRolePolicy()` or grant methods (grantReadData, grantWrite)

6. **Convert CloudFormation resources**: Use L2 constructs or `CfnResource`

7. **Replace plugins** (see document_references/ for detailed mappings):
   - `serverless-webpack` → NodejsFunction bundling (esbuild default)
   - `serverless-iam-roles-per-function` → Default CDK behavior (each function gets own role)
   - `serverless-plugin-tracing` → `tracing: Tracing.ACTIVE`
   - `serverless-plugin-log-retention` → `logRetention: RetentionDays.ONE_MONTH`
   - `serverless-offline` → AWS SAM CLI (`sam local start-api`)
   - `serverless-domain-manager` → DomainName + Certificate + Route53 ARecord
   - Other plugins: See document_references/ directory

8. **Create outputs**: Use `CfnOutput` for API endpoints, function ARNs

9. **Update package.json**: Replace serverless deps with `aws-cdk-lib`, `constructs`, `aws-lambda-nodejs`; update scripts to use CDK CLI

10. **Create cdk.json**: Set app entry point, feature flags, exclude patterns

11. **Migrate stage variables**: Use CDK context or environment-specific stack instantiation

12. **Update CI/CD**: Replace `serverless deploy` with `cdk synth && cdk deploy`

## Validation Criteria

1. `cdk synth` succeeds without errors
2. All Lambda functions converted with correct handlers
3. API Gateway endpoints configured correctly
4. IAM permissions equivalent to original
5. Environment variables propagated correctly
6. `cdk deploy` succeeds and creates all resources
7. Lambda functions execute with same behavior
8. API endpoints return correct responses
9. Event sources trigger correctly
10. No serverless dependencies in package.json
11. cdk.json properly configured
