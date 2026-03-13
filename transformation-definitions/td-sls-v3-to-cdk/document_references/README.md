# Serverless Plugins to CDK Quick Reference

## Core Transformation Guides

**Lambda, API Gateway & Events**: `07-lambda-apigateway-events-transformation.md`
- Lambda function conversion (NodejsFunction)
- API Gateway HTTP events (RestApi, paths, methods, CORS)
- Event sources (DynamoDB, SQS, SNS, S3, EventBridge)
- VPC, layers, DLQ, reserved concurrency

## Plugin Mapping

| Serverless Plugin | CDK Equivalent | Method |
|------------------|----------------|--------|
| serverless-webpack | NodejsFunction bundling | Use bundling.minify, bundling.sourceMap, bundling.externalModules |
| serverless-esbuild | NodejsFunction bundling | Default behavior, configure via bundling props |
| serverless-domain-manager | DomainName + Route53 | Create DomainName, Certificate, ARecord |
| serverless-offline | SAM CLI | Run `cdk synth > template.yaml && sam local start-api` |
| serverless-iam-roles-per-function | Default behavior | Use table.grantReadData(fn) or fn.addToRolePolicy() |
| serverless-plugin-tracing | tracing property | Set tracing: Tracing.ACTIVE |
| serverless-plugin-log-retention | logRetention property | Set logRetention: RetentionDays.ONE_MONTH |
| serverless-plugin-split-stacks | NestedStack | Create separate NestedStack constructs |
| serverless-plugin-canary-deployments | Alias + CodeDeploy | Use Alias with LambdaDeploymentGroup |

## Common Patterns

### Function Definition Pattern
```typescript
const myFunction = new NodejsFunction(this, 'MyFunction', {
  entry: 'handlers/myHandler.ts',
  handler: 'handler',
  runtime: Runtime.NODEJS_20_X,
  
  // Bundling (serverless-webpack)
  bundling: {
    minify: true,
    sourceMap: true,
    externalModules: ['@aws-sdk/*'],
  },
  
  // Observability (serverless-plugin-tracing, serverless-plugin-log-retention)
  tracing: Tracing.ACTIVE,
  logRetention: RetentionDays.ONE_MONTH,
  
  // Environment
  environment: {
    TABLE_NAME: table.tableName,
  },
});

// Permissions (serverless-iam-roles-per-function)
table.grantReadWriteData(myFunction);
```


### API with Custom Domain Pattern
```typescript
const certificate = Certificate.fromCertificateArn(this, 'Cert', certArn);

const api = new RestApi(this, 'MyApi', {
  domainName: {
    domainName: 'api.example.com',
    certificate: certificate,
  },
  deployOptions: {
    tracingEnabled: true,
  },
});

const zone = HostedZone.fromLookup(this, 'Zone', { domainName: 'example.com' });
new ARecord(this, 'ApiRecord', {
  zone: zone,
  target: RecordTarget.fromAlias(new ApiGateway(api)),
  recordName: 'api',
});
```
