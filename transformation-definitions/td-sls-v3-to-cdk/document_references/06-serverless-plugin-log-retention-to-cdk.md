# serverless-plugin-log-retention → CDK LogRetention

## Serverless Config → CDK Mapping

```yaml
# serverless.yml
plugins:
  - serverless-plugin-log-retention
provider:
  logRetentionInDays: 14
functions:
  myFunction:
    logRetentionInDays: 30
```

```typescript
// CDK
import { RetentionDays } from 'aws-cdk-lib/aws-logs';

const fn = new NodejsFunction(this, 'MyFunction', {
  entry: 'handlers/myHandler.ts',
  logRetention: RetentionDays.ONE_MONTH,  // 30 days
});
```

## Retention Period Values

```typescript
RetentionDays.ONE_DAY           // 1 day
RetentionDays.THREE_DAYS        // 3 days
RetentionDays.ONE_WEEK          // 7 days
RetentionDays.TWO_WEEKS         // 14 days
RetentionDays.ONE_MONTH         // 30 days
RetentionDays.TWO_MONTHS        // 60 days
RetentionDays.THREE_MONTHS      // 90 days
RetentionDays.SIX_MONTHS        // 180 days
RetentionDays.ONE_YEAR          // 365 days
RetentionDays.FIVE_YEARS        // 1827 days
RetentionDays.TEN_YEARS         // 3653 days
RetentionDays.INFINITE          // Never expire
```

## Environment-Based Retention

```typescript
const retention = {
  production: RetentionDays.ONE_YEAR,
  staging: RetentionDays.ONE_MONTH,
  development: RetentionDays.ONE_WEEK,
}[process.env.ENV || 'development'];

const fn = new NodejsFunction(this, 'MyFunction', {
  entry: 'handlers/myHandler.ts',
  logRetention: retention,
});
```

## Custom Log Group (Advanced)

```typescript
import { LogGroup } from 'aws-cdk-lib/aws-logs';

const logGroup = new LogGroup(this, 'MyFunctionLogGroup', {
  logGroupName: '/aws/lambda/my-function',
  retention: RetentionDays.ONE_MONTH,
  removalPolicy: cdk.RemovalPolicy.DESTROY,
});

const fn = new Function(this, 'MyFunction', {
  runtime: Runtime.NODEJS_20_X,
  handler: 'index.handler',
  code: Code.fromAsset('lambda'),
  functionName: 'my-function',
});

logGroup.grantWrite(fn);
```

## Log Group with KMS Encryption

```typescript
import { Key } from 'aws-cdk-lib/aws-kms';

const kmsKey = new Key(this, 'LogsKey', {
  enableKeyRotation: true,
});

const logGroup = new LogGroup(this, 'EncryptedLogGroup', {
  logGroupName: '/aws/lambda/my-secure-function',
  retention: RetentionDays.ONE_YEAR,
  encryptionKey: kmsKey,
});
```
