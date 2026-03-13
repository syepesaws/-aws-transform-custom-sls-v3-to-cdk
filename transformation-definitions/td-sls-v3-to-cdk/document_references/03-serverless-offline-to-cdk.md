# serverless-offline → SAM CLI

## Serverless Config → CDK Mapping

```yaml
# serverless.yml
plugins:
  - serverless-offline
custom:
  serverless-offline:
    httpPort: 3000
```

```bash
# CDK - Use AWS SAM CLI
cdk synth --no-staging > template.yaml
sam local start-api -t template.yaml --port 3000

# Invoke individual function
sam local invoke MyFunction -t template.yaml -e events/event.json

# With environment variables
sam local start-api -t template.yaml --env-vars env.json
```

## Environment Variables (env.json)

```json
{
  "MyFunction": {
    "TABLE_NAME": "local-table",
    "API_KEY": "test-key"
  }
}
```

## Sample Event (events/api-event.json)

```json
{
  "httpMethod": "GET",
  "path": "/users/123",
  "pathParameters": { "id": "123" },
  "queryStringParameters": { "filter": "active" },
  "headers": { "Content-Type": "application/json" },
  "body": null
}
```

## NPM Scripts

```json
{
  "scripts": {
    "synth": "cdk synth --no-staging > template.yaml",
    "local:api": "npm run synth && sam local start-api -t template.yaml",
    "local:invoke": "npm run synth && sam local invoke"
  }
}
```

## Alternative: LocalStack (Full AWS Emulation)

```bash
pip install localstack
localstack start
cdklocal deploy
```

## Alternative: CDK Watch (Rapid Development)

```bash
cdk watch  # Auto-deploys changes to AWS
```
