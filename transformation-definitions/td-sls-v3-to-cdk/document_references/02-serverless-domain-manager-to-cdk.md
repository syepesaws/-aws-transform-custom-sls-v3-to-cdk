# serverless-domain-manager → CDK DomainName

## Serverless Config → CDK Mapping

```yaml
# serverless.yml
plugins:
  - serverless-domain-manager
custom:
  customDomain:
    domainName: api.example.com
    basePath: v1
    certificateName: '*.example.com'
    createRoute53Record: true
    endpointType: regional
    securityPolicy: tls_1_2
```

```typescript
// CDK - Method 1: Inline (Simple)
const certificate = Certificate.fromCertificateArn(this, 'Cert', certArn);

const api = new RestApi(this, 'MyApi', {
  domainName: {
    domainName: 'api.example.com',
    certificate: certificate,
    endpointType: EndpointType.REGIONAL,
    securityPolicy: SecurityPolicy.TLS_1_2,
  },
});

const zone = HostedZone.fromLookup(this, 'Zone', { domainName: 'example.com' });
new ARecord(this, 'ApiRecord', {
  zone: zone,
  target: RecordTarget.fromAlias(new ApiGateway(api)),
  recordName: 'api',
});
```

## Method 2: Separate DomainName with Base Path

```typescript
const domainName = new DomainName(this, 'CustomDomain', {
  domainName: 'api.example.com',
  certificate: certificate,
  endpointType: EndpointType.REGIONAL,
  securityPolicy: SecurityPolicy.TLS_1_2,
});

const api = new RestApi(this, 'MyApi', { restApiName: 'My Service' });

new BasePathMapping(this, 'BasePathMapping', {
  domainName: domainName,
  restApi: api,
  basePath: 'v1',
  stage: api.deploymentStage,
});

new ARecord(this, 'ApiRecord', {
  zone: zone,
  target: RecordTarget.fromAlias(new ApiGatewayDomain(domainName)),
  recordName: 'api',
});
```

## Multi-Level Path (e.g., /orders/v1/api)

```typescript
const domainName = new DomainName(this, 'CustomDomain', {
  domainName: 'api.example.com',
  certificate: certificate,
  mapping: api,
  basePath: 'orders/v1/api',
  endpointType: EndpointType.REGIONAL,  // Required
  securityPolicy: SecurityPolicy.TLS_1_2, // Required
});
```

## Create Certificate in CDK

```typescript
const certificate = new Certificate(this, 'Certificate', {
  domainName: 'api.example.com',
  subjectAlternativeNames: ['*.example.com'],
  validation: CertificateValidation.fromDns(hostedZone),
});
```

## HTTP API (API Gateway v2)

```typescript
import { DomainName } from 'aws-cdk-lib/aws-apigatewayv2';

const domainName = new DomainName(this, 'HttpApiDomain', {
  domainName: 'api.example.com',
  certificate: certificate,
});

const httpApi = new HttpApi(this, 'HttpApi', {
  defaultDomainMapping: {
    domainName: domainName,
    mappingKey: 'v1',
  },
});
```
