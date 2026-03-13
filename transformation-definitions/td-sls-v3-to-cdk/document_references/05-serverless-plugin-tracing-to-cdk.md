# serverless-plugin-tracing → CDK Tracing

## Serverless Config → CDK Mapping

```yaml
# serverless.yml
plugins:
  - serverless-plugin-tracing
provider:
  tracing:
    lambda: true
    apiGateway: true
functions:
  myFunction:
    tracing: Active
```

```typescript
// CDK - Lambda tracing
const fn = new NodejsFunction(this, 'MyFunction', {
  entry: 'handlers/myHandler.ts',
  tracing: Tracing.ACTIVE,  // or Tracing.PASS_THROUGH, Tracing.DISABLED
});

// API Gateway tracing
const api = new RestApi(this, 'MyApi', {
  deployOptions: {
    tracingEnabled: true,
  },
});
```

## X-Ray SDK Integration (TypeScript)

```typescript
import AWSXRay from 'aws-xray-sdk-core';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand } from '@aws-sdk/lib-dynamodb';

// Wrap AWS SDK v3 client
const ddbClient = AWSXRay.captureAWSv3Client(new DynamoDBClient({}));
const docClient = DynamoDBDocumentClient.from(ddbClient);

export const handler = async (event: any) => {
  const segment = AWSXRay.getSegment();
  const subsegment = segment?.addNewSubsegment('custom-operation');
  
  try {
    const result = await docClient.send(new GetCommand({
      TableName: 'MyTable',
      Key: { id: '123' },
    }));
    
    subsegment?.addAnnotation('userId', '123');  // Indexed
    subsegment?.addMetadata('result', result);   // Not indexed
    subsegment?.close();
    
    return result;
  } catch (error) {
    subsegment?.addError(error as Error);
    subsegment?.close();
    throw error;
  }
};
```

## Environment-Specific Tracing

```typescript
const tracing = process.env.ENV === 'production' ? Tracing.ACTIVE : Tracing.DISABLED;

const fn = new NodejsFunction(this, 'MyFunction', {
  entry: 'handlers/myHandler.ts',
  tracing: tracing,
});
```
