# Benchmark Results

> Last updated: 2026-04-01 21:20 UTC

**7/7** succeeded | **0/7** partial | **7/7** builds passed | **7/7** ATX reported success

**Total agent minutes**: 0.00 | **Total cost**: $0.00 (@ $0.035/min)

## Summary

| Repository | Stars | LOC | Fns | Plugins | Status | Score | Build | Time (s) | Agent Min | Cost | KIs |
|------------|-------|-----|-----|---------|--------|-------|-------|----------|-----------|------|-----|
| [Serverless-Boilerplate-Express-TypeScript](https://github.com/ixartz/Serverless-Boilerplate-Express-TypeScript) | 571 | N/A | 1 | 3 | ✅ | 8/8 | ✅ | 1566 | N/A | N/A | N/A |
| [aws-lambda-typescript](https://github.com/balassy/aws-lambda-typescript) | 265 | N/A | 4 | 5 | ✅ | 8/8 | ✅ | 1814 | N/A | N/A | N/A |
| [serverless-architecture-boilerplate](https://github.com/msfidelis/serverless-architecture-boilerplate) | 391 | N/A | 8 | 3 | ✅ | 9/9 | ✅ | 1794 | N/A | N/A | N/A |
| [serverless-http](https://github.com/dougmoscrop/serverless-http) | 1781 | N/A | 9 | 4 | ✅ | 8/8 | ✅ | 1895 | N/A | N/A | N/A |
| [serverless-nodejs-starter](https://github.com/AnomalyInnovations/serverless-nodejs-starter) | 756 | N/A | 1 | 3 | ✅ | 7/7 | ✅ | 1193 | N/A | N/A | N/A |
| [serverless-puppeteer-layers](https://github.com/RafalWilinski/serverless-puppeteer-layers) | 272 | N/A | 1 | 2 | ✅ | 7/7 | ✅ | 1326 | N/A | N/A | N/A |
| [serverless-react-boilerplate](https://github.com/arabold/serverless-react-boilerplate) | 245 | N/A | 1 | 4 | ✅ | 8/8 | ✅ | 2127 | N/A | N/A | N/A |

## Detailed Results

### Serverless-Boilerplate-Express-TypeScript

- **URL**: https://github.com/ixartz/Serverless-Boilerplate-Express-TypeScript
- **Stars**: 571
- **LOC**: N/A
- **Status**: ✅ success
- **Validation score**: 8/8 criteria passed → ✅ success
- **Build**: ✅ pass
- **Time taken**: 1566s
- **Agent minutes**: N/A
- **Cost**: N/A
- **Knowledge items**: N/A

| Criterion | Status | Detail |
|-----------|--------|--------|
| cdk_synth | ✅ PASS | npx cdk synth succeeds from clean install state. Generates CloudFormation template with all expected resources: Lambda function, IAM roles, HTTP API Gateway v2, routes, log groups. |
| lambda_functions | ✅ PASS | 1 Lambda function (app) migrated with NodejsFunction construct. Config: entry=src/handler.ts, handler=handler, runtime=nodejs18.x, memorySize=512, timeout=10s, functionName=serverless-boilerplate-${stage}-app. Prisma Client bundled via nodeModules and commandHooks. |
| api_gateway | ✅ PASS | HTTP API (API Gateway v2) created with HttpApi construct. CORS enabled (allowOrigins=*, allowMethods=ANY, allowHeaders=*). Routes: /{proxy+} ANY and / ANY with HttpLambdaIntegration. Access logging configured with LogGroup. |
| iam_permissions | ✅ PASS | Per-function IAM role created by CDK default behavior (replaces serverless-iam-roles-per-function). X-Ray tracing permissions automatically added. Lambda execution role with AWSLambdaBasicExecutionRole managed policy. |
| environment_variables | ✅ PASS | NODE_ENV set based on stage (prod=production, otherwise=development). DATABASE_URL passed through from process.env at deploy time (replaces serverless-dotenv-plugin). |
| event_sources | ➖ N/A | No non-HTTP event sources in the original serverless.yml. Only httpApi events which are covered by the api_gateway criterion. |
| no_serverless_deps | ✅ PASS | All Serverless Framework dependencies removed: serverless, serverless-esbuild, serverless-offline, serverless-dotenv-plugin. Only serverless-http remains as a runtime dependency (used by Lambda handler code, not a Serverless Framework plugin). |
| cdk_json | ✅ PASS | cdk.json created with app entry point (ts-node with commonjs compiler option), CDK feature flags, context values for stage and region. |
| clean_install | ✅ PASS | Clean install (rm node_modules + package-lock.json, npm install) succeeded. npx cdk synth verified from clean state. |

**Issues encountered**: 3
- ts-node failed with ERR_UNKNOWN_FILE_EXTENSION because tsconfig.json uses module:esnext. Fixed by adding --compiler-options '{"module":"commonjs"}' to ts-node command in cdk.json.
- Docker not available in build environment. Used forceDockerBundling:false and installed esbuild as devDependency for local bundling.
- logRetention property deprecated in CDK (use logGroup instead). Kept logRetention as it still works in current CDK version.

**Manual fixes needed**: 3
- DATABASE_URL environment variable must be set at deploy time (e.g., via CDK context or CI/CD pipeline env vars)
- AWS SAM CLI must be installed for local development (npm run dev:server)
- CDK bootstrap may be needed for first deployment: npx cdk bootstrap aws://ACCOUNT-NUMBER/REGION

**Plugins migrated**: serverless-esbuild -> NodejsFunction bundling (esbuild built-in), serverless-offline -> AWS SAM CLI (sam local start-api), serverless-dotenv-plugin -> process.env at CDK synth/deploy time

### aws-lambda-typescript

- **URL**: https://github.com/balassy/aws-lambda-typescript
- **Stars**: 265
- **LOC**: N/A
- **Status**: ✅ success
- **Validation score**: 8/8 criteria passed → ✅ success
- **Build**: ✅ pass
- **Time taken**: 1814s
- **Agent minutes**: N/A
- **Cost**: N/A
- **Knowledge items**: N/A

| Criterion | Status | Detail |
|-----------|--------|--------|
| cdk_synth | ✅ PASS | npx cdk synth completes successfully after clean install, generating valid CloudFormation template with all resources |
| lambda_functions | ✅ PASS | All 4 functions migrated: getSwaggerJson, getHealthCheck, getHealthCheckDetailed, getCity. Each uses NodejsFunction with esbuild bundling, Runtime.NODEJS_18_X, Tracing.ACTIVE, and logRetention ONE_MONTH |
| api_gateway | ✅ PASS | RestApi created with CORS (ALL_ORIGINS, ALL_METHODS). Routes: GET /swagger.json, GET /health/check, GET /health/detailed, GET /cities/{id}. All use LambdaIntegration |
| iam_permissions | ✅ PASS | Each function gets its own IAM role (CDK default). getSwaggerJson has additional apigateway:GET policy. X-Ray tracing permissions auto-added |
| environment_variables | ✅ PASS | getSwaggerJson: REGION_NAME, REST_API_NAME, STAGE_NAME, API_INFO_VERSION, API_INFO_TITLE. getCity: DEFAULT_COUNTRY=Hungary. All serverless variable references (${self:*}) replaced with CDK equivalents |
| event_sources | ➖ N/A | No non-HTTP event sources in the original serverless.yml. All events are HTTP (API Gateway REST API) |
| no_serverless_deps | ✅ PASS | No serverless or serverless-* dependencies remain in package.json. Removed: serverless-plugin-typescript, serverless-offline, serverless-aws-documentation, serverless-domain-manager, serverless-stack-output |
| cdk_json | ✅ PASS | cdk.json exists with correct app entry point (npx ts-node --prefer-ts-exts bin/app.ts), CDK feature flags, and watch configuration |
| clean_install | ✅ PASS | rm -rf node_modules package-lock.json && npm install && npx cdk synth all pass without errors |

**Issues encountered**: 4
- TypeScript noUnusedLocals caused TS6133 errors for Lambda function variables before API Gateway step - resolved by making functions public class properties
- Docker not available in build environment - resolved with forceDockerBundling: false and esbuild as local devDependency
- AWS SDK v2 not included in Node 18 Lambda runtime - changed externalModules from ['aws-sdk'] to ['@aws-sdk/*'] so aws-sdk v2 gets bundled for swagger handler
- logRetention property deprecated in aws-cdk-lib - generates deprecation warning but still functional

**Manual fixes needed**: 2
- Custom domain setup requires manual configuration: ACM certificate ARN and Route53 hosted zone ID must be provided in lib/serverless-sample-stack.ts (commented-out code section)
- serverless-aws-documentation plugin has no CDK equivalent - Swagger documentation via API Gateway annotations is not available. The /swagger.json endpoint still works via the Lambda function

**Plugins migrated**: serverless-plugin-typescript (replaced by NodejsFunction esbuild bundling), serverless-domain-manager (commented-out CDK equivalent with DomainName, Certificate, Route53 ARecord), serverless-offline (replaced by AWS SAM CLI - sam local start-api), serverless-iam-roles-per-function (implicit - CDK creates per-function IAM roles by default), serverless-stack-output (replaced by CDK CfnOutput)

### serverless-architecture-boilerplate

- **URL**: https://github.com/msfidelis/serverless-architecture-boilerplate
- **Stars**: 391
- **LOC**: N/A
- **Status**: ✅ success
- **Validation score**: 9/9 criteria passed → ✅ success
- **Build**: ✅ pass
- **Time taken**: 1794s
- **Agent minutes**: N/A
- **Cost**: N/A
- **Knowledge items**: N/A

| Criterion | Status | Detail |
|-----------|--------|--------|
| cdk_synth | ✅ PASS | npx cdk synth completes successfully with zero errors after clean install. Generates valid CloudFormation template with all expected resources. |
| lambda_functions | ✅ PASS | All 8 Lambda functions created as NodejsFunction constructs: notFound, books-register, books-list, books-detail, books-update, books-delete, books-consumer, envs-temp. Runtime upgraded from nodejs12.x (EOL) to nodejs18.x. AWS SDK v2 bundled correctly via externalModules:[]. |
| api_gateway | ✅ PASS | RestApi created with 7 HTTP routes: GET/POST /services/books, GET/PUT/DELETE /services/books/{hashkey}, GET /services/envs, ANY /{proxy+}. CORS enabled with ALL_ORIGINS and ALL_METHODS. CfnOutput for API endpoint URL. |
| iam_permissions | ✅ PASS | Per-function IAM roles (8 roles for 8 functions). DynamoDB grantReadWriteData for 6 book-related functions. SQS grant for booksRegister and booksConsumer. Lambda invoke policy for all functions. |
| environment_variables | ✅ PASS | All 5 environment variables configured: ENV (stage), MESSAGE (static), DYNAMO_TABLE_BOOKS (table.tableName CDK ref), SQS_QUEUE_URL (queue.queueUrl CDK ref), REGION (this.region CDK ref). Serverless pseudo-parameters replaced with native CDK references. |
| event_sources | ✅ PASS | EventBridge Rule created with Schedule.rate(Duration.minutes(1)) targeting books-consumer function. Rule enabled matching original configuration. |
| no_serverless_deps | ✅ PASS | No serverless framework dependencies in package.json. Removed: serverless-pseudo-parameters, yamljs, serverless-dynamodb-local, serverless-offline, serverless-offline-scheduler, serverless-offline-sqs-esmq, serverless-plugin-split-stacks. |
| cdk_json | ✅ PASS | cdk.json properly configured with app entry point (npx ts-node --prefer-ts-exts bin/app.ts), CDK v2 feature flags, and stage context variable. |
| clean_install | ✅ PASS | Clean install (rm -rf node_modules package-lock.json; npm install) succeeds followed by npx cdk synth with zero errors. |

**Issues encountered**: 4
- nodejs12.x runtime is EOL - upgraded to nodejs18.x for CDK compatibility
- AWS SDK v2 (aws-sdk) not included in nodejs18.x Lambda runtime - configured bundling with externalModules:[] to include it in bundle
- read.js handler file does not export 'envs' function referenced by envs-temp serverless function - pre-existing issue in original codebase, preserved as-is
- esbuild required as devDependency for local bundling without Docker

**Manual fixes needed**: 2
- The envs-temp function handler (read.envs) does not exist in modules/books/endpoints/read.js - this was a pre-existing issue in the original codebase
- aws-sdk v2 is end-of-support - consider migrating handler code to AWS SDK v3 (@aws-sdk/*) for long-term support

**Plugins migrated**: serverless-pseudo-parameters -> Native CDK references (this.account, this.region), serverless-plugin-split-stacks -> Not needed (CDK handles CloudFormation natively), serverless-offline -> Documented SAM CLI alternative in README

### serverless-http

- **URL**: https://github.com/dougmoscrop/serverless-http
- **Stars**: 1781
- **LOC**: N/A
- **Status**: ✅ success
- **Validation score**: 8/8 criteria passed → ✅ success
- **Build**: ✅ pass
- **Time taken**: 1895s
- **Agent minutes**: N/A
- **Cost**: N/A
- **Knowledge items**: N/A

| Criterion | Status | Detail |
|-----------|--------|--------|
| cdk_synth | ✅ PASS | npx cdk synth succeeds with exit code 0 from clean install. Generates valid CloudFormation template with 10 Lambda functions (9 + LogRetention), 14 API Gateway methods, and 13 API Gateway resources. |
| lambda_functions | ✅ PASS | All 9 Lambda functions migrated: compare, echo, timer, express, koa, cookies, binary, pino, root. Each uses NodejsFunction with Runtime.NODEJS_20_X, Tracing.ACTIVE, logRetention ONE_MONTH. Static assets (test.xlsx, image.png) properly bundled via afterBundling hooks. |
| api_gateway | ✅ PASS | RestApi created with binaryMediaTypes=['image/png']. 14 routes configured: standard proxy integrations, async invocation (X-Amz-Invocation-Type: Event), and non-proxy Lambda integrations. Resource tree correctly handles nested paths (echo/async, echo/sync). CfnOutput for API URL. |
| iam_permissions | ✅ PASS | Each Lambda function gets its own IAM role by default in CDK (replaces serverless-iam-roles-per-function). No custom IAM statements were in the original serverless.yml, so no additional policy statements needed. |
| environment_variables | ✅ PASS | The original serverless.yml had no environment variables defined at provider or function level. No environment variable migration was needed. |
| event_sources | ➖ N/A | No non-HTTP event sources (SQS, SNS, DynamoDB Streams, S3, Schedule, EventBridge) in the original serverless.yml. All events are HTTP API Gateway events. |
| no_serverless_deps | ✅ PASS | Removed serverless@^3.10.2, serverless-offline@^12.0.4, serverless-plugin-common-excludes@^4.0.0, serverless-plugin-custom-binary@^2.0.0, serverless-plugin-include-dependencies@^5.0.0. No serverless-* dependencies remain in package.json. |
| cdk_json | ✅ PASS | cdk.json created with app entry point (npx ts-node --prefer-ts-exts bin/app.ts), feature flags, and context values. Properly configured and validated. |
| clean_install | ✅ PASS | Clean install (rm -rf node_modules package-lock.json && npm install --legacy-peer-deps) followed by npx cdk synth succeeds. The --legacy-peer-deps flag is needed due to pre-existing inversify/reflect-metadata peer dependency conflict (unrelated to migration). |

**Issues encountered**: 4
- ERESOLVE peer dependency conflict between inversify@^6.0.1 and reflect-metadata@^0.1.13 (pre-existing). Resolved with --legacy-peer-deps flag and .npmrc configuration.
- Docker not available for CDK bundling. Resolved by installing esbuild locally and setting forceDockerBundling: false.
- TypeScript template literals with VTL (Velocity Template Language) $ syntax caused compilation errors. Resolved by using string array joined with newlines instead of template literals.
- logRetention property triggers deprecation warning (use logGroup instead) - kept as-is since it still works and matches the plan specification.

**Plugins migrated**: serverless-plugin-custom-binary → binaryMediaTypes on RestApi construct, serverless-plugin-include-dependencies → NodejsFunction esbuild bundling (built-in), serverless-offline → SAM CLI (sam local start-api), serverless-plugin-common-excludes → NodejsFunction bundling handles exclusions automatically

### serverless-nodejs-starter

- **URL**: https://github.com/AnomalyInnovations/serverless-nodejs-starter
- **Stars**: 756
- **LOC**: N/A
- **Status**: ✅ success
- **Validation score**: 7/7 criteria passed → ✅ success
- **Build**: ✅ pass
- **Time taken**: 1193s
- **Agent minutes**: N/A
- **Cost**: N/A
- **Knowledge items**: N/A

| Criterion | Status | Detail |
|-----------|--------|--------|
| cdk_synth | ✅ PASS | npx cdk synth completes successfully with zero errors. CloudFormation template generated with Lambda function, API Gateway, IAM roles, and outputs. |
| lambda_functions | ✅ PASS | 1 function migrated: hello (NodejsFunction with esbuild bundling, Runtime.NODEJS_18_X, minify+sourceMap, X-Ray tracing, 1 month log retention) |
| api_gateway | ✅ PASS | RestApi created with GET /hello endpoint using LambdaIntegration. CfnOutput for API endpoint URL. |
| iam_permissions | ✅ PASS | Default CDK per-function IAM role created automatically. No custom IAM statements needed (original serverless.yml had no custom IAM). X-Ray tracing permissions added automatically. |
| environment_variables | ➖ N/A | Environment variables were commented out in original serverless.yml. Pattern for adding env vars documented in CDK stack comments. |
| event_sources | ➖ N/A | No non-HTTP event sources in original serverless.yml. Only HTTP GET /hello event migrated as API Gateway endpoint. |
| no_serverless_deps | ✅ PASS | No serverless framework dependencies remain in package.json. Removed: serverless-bundle, serverless-offline, serverless-dotenv-plugin. |
| cdk_json | ✅ PASS | cdk.json properly configured with app entry point (npx ts-node --prefer-ts-exts bin/app.ts), feature flags, and watch configuration. |
| clean_install | ✅ PASS | Clean npm install (deleted node_modules and package-lock.json first) completed successfully followed by successful cdk synth. |

**Issues encountered**: 4
- Runtime upgraded from nodejs10.x (deprecated/EOL) to NODEJS_18_X
- Added forceDockerBundling: false to NodejsFunction bundling config since Docker may not be available in all environments
- Added esbuild as explicit devDependency for local bundling without Docker
- logRetention property shows deprecation warning (use logGroup instead) but still functions correctly in aws-cdk-lib v2

**Plugins migrated**: serverless-bundle → NodejsFunction with built-in esbuild bundling, serverless-offline → SAM CLI local development commands (npm run local:api), serverless-dotenv-plugin → process.env pattern (env vars were commented out in original)

### serverless-puppeteer-layers

- **URL**: https://github.com/RafalWilinski/serverless-puppeteer-layers
- **Stars**: 272
- **LOC**: N/A
- **Status**: ✅ success
- **Validation score**: 7/7 criteria passed → ✅ success
- **Build**: ✅ pass
- **Time taken**: 1326s
- **Agent minutes**: N/A
- **Cost**: N/A
- **Knowledge items**: N/A

| Criterion | Status | Detail |
|-----------|--------|--------|
| cdk_synth | ✅ PASS | npx cdk synth completes successfully with exit code 0. CloudFormation template includes Lambda function, Lambda layer, API Gateway REST API with binary media types, and all supporting resources. |
| lambda_functions | ✅ PASS | 1 Lambda function (puppeteer-orchestrator) migrated using NodejsFunction with esbuild bundling. Configured with NODEJS_18_X runtime, 2048MB memory, 30s timeout, Chrome layer attached, X-Ray tracing enabled, 1 month log retention. |
| api_gateway | ✅ PASS | REST API Gateway created with binaryMediaTypes: ['*/*'] (replacing serverless-apigw-binary and serverless-apigwy-binary plugins). GET /screenshot endpoint configured with LambdaIntegration and ContentHandling.CONVERT_TO_BINARY. |
| iam_permissions | ✅ PASS | Default Lambda execution role created by CDK (AWSLambdaBasicExecutionRole). No custom IAM statements in original serverless.yml, so no additional permissions needed. X-Ray write policy added for tracing. |
| environment_variables | ➖ N/A | No environment variables defined in original serverless.yml provider or function configuration. |
| event_sources | ➖ N/A | Only HTTP events present (GET /screenshot). No SQS, SNS, DynamoDB Streams, S3, Schedule, or EventBridge event sources in original configuration. |
| no_serverless_deps | ✅ PASS | No serverless framework dependencies in package.json. Removed serverless-apigw-binary (0.4.4) and serverless-apigwy-binary (0.1.0). No 'serverless' CLI dependency present. |
| cdk_json | ✅ PASS | cdk.json properly configured with app entry point (npx ts-node --prefer-ts-exts bin/app.ts), CDK feature flags, and exclude patterns. |
| clean_install | ✅ PASS | Clean npm install (rm -rf node_modules package-lock.json && npm install) succeeds. All dependencies resolve correctly from standard npm registry. |

**Issues encountered**: 4
- Docker not available in build environment - configured forceDockerBundling: false to use local esbuild instead
- nodejs10.x runtime is EOL - upgraded to nodejs18.x as specified in plan
- chrome-aws-lambda and puppeteer-core must be externalized from esbuild bundling since they are provided by the Lambda layer at runtime
- logRetention property shows deprecation warning in CDK - cosmetic only, does not affect functionality

**Plugins migrated**: serverless-apigw-binary (replaced by binaryMediaTypes property on RestApi), serverless-apigwy-binary (replaced by binaryMediaTypes property on RestApi)

### serverless-react-boilerplate

- **URL**: https://github.com/arabold/serverless-react-boilerplate
- **Stars**: 245
- **LOC**: N/A
- **Status**: ✅ success
- **Validation score**: 8/8 criteria passed → ✅ success
- **Build**: ✅ pass
- **Time taken**: 2127s
- **Agent minutes**: N/A
- **Cost**: N/A
- **Knowledge items**: N/A

| Criterion | Status | Detail |
|-----------|--------|--------|
| cdk_synth | ✅ PASS | npx cdk synth completes successfully after clean install, producing 27 CloudFormation resources including Lambda function, API Gateway REST API, S3 bucket, bucket deployment, and supporting IAM roles. |
| lambda_functions | ✅ PASS | 1 serve function migrated using NodejsFunction with esbuild bundling. Configured with: runtime nodejs18.x (upgraded from EOL nodejs12.x), memorySize 512, timeout 6s, logRetention 7 days. Esbuild loaders handle CSS (empty) and images (dataurl). Browser webpack build runs in beforeBundling hook to generate dist/stats.json. |
| api_gateway | ✅ PASS | RestApi created with restApiName matching original, minimumCompressionSize 1000, CORS enabled. Routes: root / ANY and /{any+} ANY with LambdaIntegration, matching original serverless.yml configuration. |
| iam_permissions | ✅ PASS | CDK creates per-function IAM roles by default (no custom IAM statements needed as original serverless.yml had no provider.iam.role.statements). Lambda function has AWSLambdaBasicExecutionRole managed policy. |
| environment_variables | ✅ PASS | All 6 environment variables mapped: SERVERLESS_PROJECT (string), SERVERLESS_REGION (this.region), SERVERLESS_STAGE (stage context), APP_DIST_URL (bucket regional domain name), APP_PUBLIC_URL (bucket regional domain name), APIGATEWAY_URL (api.url with Fn::Join). |
| event_sources | ➖ N/A | No non-HTTP event sources in the original serverless.yml. Only HTTP events (/ ANY and /{any+} ANY) which are handled by API Gateway configuration. |
| no_serverless_deps | ✅ PASS | All serverless dependencies removed from package.json: serverless, serverless-webpack, serverless-offline, serverless-plugin-scripts, serverless-s3-deploy, @types/serverless. No serverless-related packages remain in dependencies or devDependencies. |
| cdk_json | ✅ PASS | cdk.json exists with valid JSON, app entry point set to 'npx ts-node --prefer-ts-exts lib/cdk-app.ts', CDK feature flags configured, watch configuration set. |
| clean_install | ✅ PASS | npm install --legacy-peer-deps succeeds from clean state (node_modules and package-lock.json deleted first). 854 packages installed. --legacy-peer-deps required due to @pmmmwh/react-refresh-webpack-plugin peer dependency conflicts. |

**Issues encountered**: 6
- Docker not available in build environment - resolved by installing esbuild locally as devDependency for NodejsFunction local bundling
- React SSR app imports .css files (via null-loader in webpack) and .svg files (via url-loader) - resolved using esbuild loaders: '.css': 'empty', '.svg': 'dataurl'
- src/server/render.tsx dynamically imports ../../dist/stats.json (browser webpack build artifact) - resolved by running browser webpack build in beforeBundling commandHook
- S3 bucket CORS needs to reference API Gateway URL but bucket is created first - resolved using CfnBucket escape hatch with Fn::Join for dynamic CORS origin
- npm install requires --legacy-peer-deps due to react-refresh-webpack-plugin peer dependency conflicts
- logRetention property is deprecated in favor of logGroup - noted as warning, still functional

**Manual fixes needed**: 3
- AWS CDK bootstrap required before first deployment: npx cdk bootstrap
- npm run build:browser must run before cdk synth (handled by package.json scripts and beforeBundling hook)
- Runtime upgraded from nodejs12.x to nodejs18.x - verify application compatibility

**Plugins migrated**: serverless-webpack → NodejsFunction with esbuild bundling (10-100x faster), serverless-plugin-scripts → esbuild commandHooks.beforeBundling (browser build), serverless-s3-deploy → BucketDeployment construct with CacheControl, serverless-offline → AWS SAM CLI (sam local start-api)
