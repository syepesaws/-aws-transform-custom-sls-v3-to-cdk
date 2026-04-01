## Reference Documentation

* **document_references/README.md**: Quick reference mapping of Serverless plugins to CDK equivalents with core transformation guides index and common code patterns (NodejsFunction, API Gateway with custom domain)

* **document_references/07-lambda-apigateway-events-transformation.md**: Comprehensive guide for transforming Lambda functions, API Gateway HTTP events, and event sources from Serverless to CDK. Covers NodejsFunction configuration, RestApi setup, path/method mapping, CORS, event source mappings (DynamoDB Streams, SQS, SNS, S3, EventBridge), environment variables, VPC, layers, DLQ, and reserved concurrency with complete code examples

* **document_references/01-serverless-webpack-to-cdk.md**: Migration from serverless-webpack to CDK NodejsFunction bundling with esbuild (default, 10-100x faster). Covers bundling configuration (minify, sourceMap, externalModules), custom webpack setup if needed, and AWS SDK v2→v3 migration

* **document_references/02-serverless-domain-manager-to-cdk.md**: Custom domain setup for API Gateway using DomainName construct, Certificate management, Route53 ARecord integration, base path mapping, and multi-level path support

* **document_references/03-serverless-offline-to-cdk.md**: Local development migration from serverless-offline to AWS SAM CLI (sam local start-api, sam local invoke), environment variables configuration, event JSON files, and LocalStack alternative

* **document_references/04-serverless-iam-roles-per-function-to-cdk.md**: IAM role management (native CDK behavior - each function gets own role). Covers grant methods (grantReadData, grantWrite), addToRolePolicy for custom permissions, and common permission patterns

* **document_references/05-serverless-plugin-tracing-to-cdk.md**: AWS X-Ray tracing configuration using tracing property (Tracing.ACTIVE), API Gateway tracing, X-Ray SDK integration with AWS SDK v3, custom subsegments, and annotations

* **document_references/06-serverless-plugin-log-retention-to-cdk.md**: CloudWatch Logs retention using logRetention property with RetentionDays enum, environment-based retention policies, custom log groups, and KMS encryption
