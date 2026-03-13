# Lambda Functions: Serverless → CDK

## Basic Function Transformation

### Serverless Config
```yaml
provider:
  runtime: nodejs18.x
  memorySize: 512
  timeout: 30
  environment:
    STAGE: ${self:provider.stage}
    TABLE_NAME: ${self:custom.tableName}

functions:
  myFunction:
    handler: src/handlers/myHandler.handler
    memorySize: 1024
    timeout: 60
    environment:
      FUNCTION_VAR: value
    events:
      - http:
          path: /items
          method: post
          cors: true
```

### CDK Equivalent
```typescript
const myFunction = new NodejsFunction(this, 'MyFunction', {
  entry: 'src/handlers/myHandler.ts',
  handler: 'handler',
  runtime: Runtime.NODEJS_18_X,
  memorySize: 1024,  // Function-level overrides provider
  timeout: Duration.seconds(60),
  functionName: `${serviceName}-${stage}-myFunction`,
  environment: {
    STAGE: stage,
    TABLE_NAME: table.tableName,
    FUNCTION_VAR: 'value',
  },
});
```

## API Gateway HTTP Events

### Serverless → CDK
```typescript
// Create API
const api = new RestApi(this, 'Api', {
  restApiName: `${serviceName}-${stage}`,
  defaultCorsPreflightOptions: {
    allowOrigins: Cors.ALL_ORIGINS,
    allowMethods: Cors.ALL_METHODS,
  },
});

// Add integration
const integration = new LambdaIntegration(myFunction);
api.root.addResource('items').addMethod('POST', integration);
```

### Path Parameters
```yaml
# Serverless
events:
  - http:
      path: /items/{id}
      method: get
```

```typescript
// CDK
const items = api.root.addResource('items');
const item = items.addResource('{id}');
item.addMethod('GET', new LambdaIntegration(getFunction));
```

### Multiple Methods
```typescript
const items = api.root.addResource('items');
items.addMethod('GET', new LambdaIntegration(listFn));
items.addMethod('POST', new LambdaIntegration(createFn));

const item = items.addResource('{id}');
item.addMethod('GET', new LambdaIntegration(getFn));
item.addMethod('PUT', new LambdaIntegration(updateFn));
item.addMethod('DELETE', new LambdaIntegration(deleteFn));
```

## Event Source Mappings

### DynamoDB Streams
```yaml
# Serverless
events:
  - stream:
      type: dynamodb
      arn: !GetAtt MyTable.StreamArn
      batchSize: 10
      startingPosition: LATEST
```

```typescript
// CDK
import { DynamoEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';

myFunction.addEventSource(new DynamoEventSource(table, {
  startingPosition: StartingPosition.LATEST,
  batchSize: 10,
}));
```

### SQS Queue
```yaml
# Serverless
events:
  - sqs:
      arn: !GetAtt MyQueue.Arn
      batchSize: 10
```

```typescript
// CDK
import { SqsEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';

myFunction.addEventSource(new SqsEventSource(queue, {
  batchSize: 10,
}));
```

### SNS Topic
```yaml
# Serverless
events:
  - sns:
      arn: !Ref MyTopic
      topicName: my-topic
```

```typescript
// CDK
import { SnsEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';

myFunction.addEventSource(new SnsEventSource(topic));
```

### S3 Bucket
```yaml
# Serverless
events:
  - s3:
      bucket: my-bucket
      event: s3:ObjectCreated:*
      rules:
        - prefix: uploads/
        - suffix: .jpg
```

```typescript
// CDK
import { S3EventSource } from 'aws-cdk-lib/aws-lambda-event-sources';
import { EventType } from 'aws-cdk-lib/aws-s3';

myFunction.addEventSource(new S3EventSource(bucket, {
  events: [EventType.OBJECT_CREATED],
  filters: [
    { prefix: 'uploads/' },
    { suffix: '.jpg' },
  ],
}));
```

### EventBridge (CloudWatch Events)
```yaml
# Serverless
events:
  - schedule:
      rate: rate(5 minutes)
      enabled: true
```

```typescript
// CDK
import { Rule, Schedule } from 'aws-cdk-lib/aws-events';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';

new Rule(this, 'ScheduleRule', {
  schedule: Schedule.rate(Duration.minutes(5)),
  targets: [new LambdaFunction(myFunction)],
});
```

## Environment Variables

### Merge Provider + Function Level
```typescript
// Provider-level environment
const providerEnv = {
  STAGE: stage,
  REGION: region,
};

// Function-level environment
const myFunction = new NodejsFunction(this, 'MyFunction', {
  entry: 'src/handlers/myHandler.ts',
  environment: {
    ...providerEnv,
    TABLE_NAME: table.tableName,
    FUNCTION_SPECIFIC: 'value',
  },
});
```

### Dynamic References
```typescript
environment: {
  TABLE_NAME: table.tableName,           // DynamoDB table name
  BUCKET_NAME: bucket.bucketName,        // S3 bucket name
  QUEUE_URL: queue.queueUrl,             // SQS queue URL
  TOPIC_ARN: topic.topicArn,             // SNS topic ARN
  SECRET_ARN: secret.secretArn,          // Secrets Manager ARN
  API_ENDPOINT: api.url,                 // API Gateway URL
}
```

## Function Naming Convention

```typescript
// Pattern: {service}-{stage}-{functionName}
const functionName = `${serviceName}-${stage}-${logicalName}`;

const myFunction = new NodejsFunction(this, 'MyFunction', {
  entry: 'src/handlers/myHandler.ts',
  functionName: functionName,
});
```

## Reserved Concurrent Executions

```yaml
# Serverless
functions:
  myFunction:
    reservedConcurrency: 5
```

```typescript
// CDK
const myFunction = new NodejsFunction(this, 'MyFunction', {
  entry: 'src/handlers/myHandler.ts',
  reservedConcurrentExecutions: 5,
});
```

## VPC Configuration

```yaml
# Serverless
provider:
  vpc:
    securityGroupIds:
      - sg-12345
    subnetIds:
      - subnet-12345
      - subnet-67890
```

```typescript
// CDK
import { Vpc, SecurityGroup } from 'aws-cdk-lib/aws-ec2';

const vpc = Vpc.fromLookup(this, 'Vpc', { vpcId: 'vpc-12345' });
const sg = SecurityGroup.fromSecurityGroupId(this, 'SG', 'sg-12345');

const myFunction = new NodejsFunction(this, 'MyFunction', {
  entry: 'src/handlers/myHandler.ts',
  vpc: vpc,
  vpcSubnets: { subnetType: SubnetType.PRIVATE_WITH_EGRESS },
  securityGroups: [sg],
});
```

## Layers

```yaml
# Serverless
functions:
  myFunction:
    layers:
      - arn:aws:lambda:us-east-1:123456789012:layer:my-layer:1
```

```typescript
// CDK
import { LayerVersion } from 'aws-cdk-lib/aws-lambda';

const layer = LayerVersion.fromLayerVersionArn(
  this,
  'Layer',
  'arn:aws:lambda:us-east-1:123456789012:layer:my-layer:1'
);

const myFunction = new NodejsFunction(this, 'MyFunction', {
  entry: 'src/handlers/myHandler.ts',
  layers: [layer],
});
```

## Dead Letter Queue

```yaml
# Serverless
functions:
  myFunction:
    onError: arn:aws:sns:us-east-1:123456789012:my-dlq
```

```typescript
// CDK
import { Topic } from 'aws-cdk-lib/aws-sns';

const dlqTopic = Topic.fromTopicArn(
  this,
  'DLQ',
  'arn:aws:sns:us-east-1:123456789012:my-dlq'
);

const myFunction = new NodejsFunction(this, 'MyFunction', {
  entry: 'src/handlers/myHandler.ts',
  deadLetterTopic: dlqTopic,
});
```

## Complete Example

```typescript
import * as cdk from 'aws-cdk-lib';
import { NodejsFunction } from 'aws-cdk-lib/aws-lambda-nodejs';
import { Runtime, Tracing } from 'aws-cdk-lib/aws-lambda';
import { RestApi, LambdaIntegration, Cors } from 'aws-cdk-lib/aws-apigateway';
import { RetentionDays } from 'aws-cdk-lib/aws-logs';
import { Table } from 'aws-cdk-lib/aws-dynamodb';

export class MyStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const stage = process.env.STAGE || 'dev';
    const serviceName = 'my-service';

    // DynamoDB Table
    const table = Table.fromTableName(this, 'Table', `${serviceName}-table-${stage}`);

    // Lambda Function
    const myFunction = new NodejsFunction(this, 'MyFunction', {
      entry: 'src/handlers/myHandler.ts',
      handler: 'handler',
      runtime: Runtime.NODEJS_18_X,
      functionName: `${serviceName}-${stage}-myFunction`,
      memorySize: 1024,
      timeout: cdk.Duration.seconds(30),
      environment: {
        STAGE: stage,
        TABLE_NAME: table.tableName,
      },
      tracing: Tracing.ACTIVE,
      logRetention: RetentionDays.TWO_WEEKS,
    });

    // Grant permissions
    table.grantReadWriteData(myFunction);

    // API Gateway
    const api = new RestApi(this, 'Api', {
      restApiName: `${serviceName}-${stage}`,
      defaultCorsPreflightOptions: {
        allowOrigins: Cors.ALL_ORIGINS,
        allowMethods: Cors.ALL_METHODS,
      },
    });

    const integration = new LambdaIntegration(myFunction);
    api.root.addResource('items').addMethod('POST', integration);

    // Outputs
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url,
      exportName: `${serviceName}-${stage}-ApiUrl`,
    });

    new cdk.CfnOutput(this, 'FunctionArn', {
      value: myFunction.functionArn,
      exportName: `${serviceName}-${stage}-FunctionArn`,
    });
  }
}
```
