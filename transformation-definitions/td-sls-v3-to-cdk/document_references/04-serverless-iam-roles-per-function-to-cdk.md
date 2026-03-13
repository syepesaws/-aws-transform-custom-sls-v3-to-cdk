# serverless-iam-roles-per-function → CDK Default

## Serverless Config → CDK Mapping

```yaml
# serverless.yml
plugins:
  - serverless-iam-roles-per-function
functions:
  createUser:
    handler: handlers/createUser.handler
    iamRoleStatements:
      - Effect: Allow
        Action: [dynamodb:PutItem]
        Resource: !GetAtt UsersTable.Arn
      - Effect: Allow
        Action: [ses:SendEmail]
        Resource: '*'
```

```typescript
// CDK - Automatic separate roles, use grant methods
const createUserFn = new NodejsFunction(this, 'CreateUserFunction', {
  entry: 'handlers/createUser.ts',
});

usersTable.grantWriteData(createUserFn);  // PutItem, UpdateItem, DeleteItem

createUserFn.addToRolePolicy(new PolicyStatement({
  actions: ['ses:SendEmail'],
  resources: ['*'],
}));
```

## Grant Methods (Preferred)

```typescript
// DynamoDB
table.grantReadData(fn);           // GetItem, Query, Scan
table.grantWriteData(fn);          // PutItem, UpdateItem, DeleteItem
table.grantReadWriteData(fn);      // All operations
table.grantStreamRead(fn);         // Stream operations

// S3
bucket.grantRead(fn);              // GetObject, ListBucket
bucket.grantWrite(fn);             // PutObject, DeleteObject
bucket.grantReadWrite(fn);         // All operations
bucket.grantPut(fn);               // PutObject only

// SQS
queue.grantSendMessages(fn);       // SendMessage
queue.grantConsumeMessages(fn);    // ReceiveMessage, DeleteMessage

// SNS
topic.grantPublish(fn);            // Publish

// Secrets Manager
secret.grantRead(fn);              // GetSecretValue
```

## Custom Policies

```typescript
fn.addToRolePolicy(new PolicyStatement({
  effect: Effect.ALLOW,
  actions: ['dynamodb:PutItem', 'dynamodb:UpdateItem'],
  resources: [table.tableArn, `${table.tableArn}/index/*`],
}));
```

## Custom Role (Advanced)

```typescript
const customRole = new Role(this, 'CustomRole', {
  assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
  managedPolicies: [
    ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
  ],
});

customRole.addToPolicy(new PolicyStatement({
  actions: ['dynamodb:PutItem'],
  resources: [table.tableArn],
}));

const fn = new NodejsFunction(this, 'MyFunction', {
  entry: 'handlers/myHandler.ts',
  role: customRole,  // Override default
});
```
