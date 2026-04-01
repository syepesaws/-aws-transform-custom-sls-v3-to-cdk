# Benchmark Results

> Last updated: 2026-04-01 17:47 UTC

**5/5** succeeded | **0/5** partial | **5/5** builds passed | **5/5** ATX reported success

**Total agent minutes**: 250.93 | **Total cost**: $8.78 (@ $0.035/min)

## Summary

| Repository | Stars | LOC | Fns | Plugins | Status | Score | Build | Time (s) | Agent Min | Cost | KIs |
|------------|-------|-----|-----|---------|--------|-------|-------|----------|-----------|------|-----|
| [Serverless-Boilerplate-Express-TypeScript](https://github.com/ixartz/Serverless-Boilerplate-Express-TypeScript) | 571 | 263 | N/A | 0 | ✅ | 2/2 | ✅ | 1276 | 47.58 | $1.67 | 2 |
| [aws-lambda-typescript](https://github.com/balassy/aws-lambda-typescript) | 265 | 1469 | N/A | 0 | ✅ | 2/2 | ✅ | 1195 | 46.02 | $1.61 | 2 |
| [serverless-architecture-boilerplate](https://github.com/msfidelis/serverless-architecture-boilerplate) | 391 | 292 | N/A | 0 | ✅ | 2/2 | ✅ | 1443 | 67.83 | $2.37 | 2 |
| [serverless-puppeteer-layers](https://github.com/RafalWilinski/serverless-puppeteer-layers) | 272 | 93 | N/A | 0 | ✅ | 2/2 | ✅ | 1081 | 34.36 | $1.20 | 2 |
| [serverless-react-boilerplate](https://github.com/arabold/serverless-react-boilerplate) | 245 | 229 | N/A | 0 | ✅ | 2/2 | ✅ | 1364 | 55.14 | $1.93 | 2 |

## Detailed Results

### Serverless-Boilerplate-Express-TypeScript

- **URL**: https://github.com/ixartz/Serverless-Boilerplate-Express-TypeScript
- **Stars**: 571
- **LOC**: 263
- **Status**: ✅ success
- **Validation score**: 2/2 criteria passed → ✅ success
- **Build**: ✅ pass
- **Time taken**: 1276s
- **Agent minutes**: 47.58
- **Cost**: $1.67
- **Knowledge items**: 2

**CDK Quality**:
- L2 constructs: 0 | Cfn escape hatches: 3 | L2 ratio: 0.0
- TODO/FIXME comments: 0
- ⚠️ lib/serverless-boilerplate-stack.ts: 3 CfnResource/escape hatch(es)

### aws-lambda-typescript

- **URL**: https://github.com/balassy/aws-lambda-typescript
- **Stars**: 265
- **LOC**: 1469
- **Status**: ✅ success
- **Validation score**: 2/2 criteria passed → ✅ success
- **Build**: ✅ pass
- **Time taken**: 1195s
- **Agent minutes**: 46.02
- **Cost**: $1.61
- **Knowledge items**: 2

**CDK Quality**:
- L2 constructs: 0 | Cfn escape hatches: 5 | L2 ratio: 0.0
- TODO/FIXME comments: 1
- ⚠️ lib/serverless-sample-stack.ts: 5 CfnResource/escape hatch(es)

### serverless-architecture-boilerplate

- **URL**: https://github.com/msfidelis/serverless-architecture-boilerplate
- **Stars**: 391
- **LOC**: 292
- **Status**: ✅ success
- **Validation score**: 2/2 criteria passed → ✅ success
- **Build**: ✅ pass
- **Time taken**: 1443s
- **Agent minutes**: 67.83
- **Cost**: $2.37
- **Knowledge items**: 2

**CDK Quality**:
- L2 constructs: 0 | Cfn escape hatches: 3 | L2 ratio: 0.0
- TODO/FIXME comments: 0
- ⚠️ lib/serverless-boilerplate-stack.ts: 3 CfnResource/escape hatch(es)

### serverless-puppeteer-layers

- **URL**: https://github.com/RafalWilinski/serverless-puppeteer-layers
- **Stars**: 272
- **LOC**: 93
- **Status**: ✅ success
- **Validation score**: 2/2 criteria passed → ✅ success
- **Build**: ✅ pass
- **Time taken**: 1081s
- **Agent minutes**: 34.36
- **Cost**: $1.20
- **Knowledge items**: 2

**CDK Quality**:
- L2 constructs: 1 | Cfn escape hatches: 3 | L2 ratio: 0.25
- TODO/FIXME comments: 0
- Constructs used: RestApi
- ⚠️ lib/serverless-puppeteer-layers-stack.ts: 3 CfnResource/escape hatch(es)

### serverless-react-boilerplate

- **URL**: https://github.com/arabold/serverless-react-boilerplate
- **Stars**: 245
- **LOC**: 229
- **Status**: ✅ success
- **Validation score**: 2/2 criteria passed → ✅ success
- **Build**: ✅ pass
- **Time taken**: 1364s
- **Agent minutes**: 55.14
- **Cost**: $1.93
- **Knowledge items**: 2

**CDK Quality**:
- L2 constructs: 3 | Cfn escape hatches: 4 | L2 ratio: 0.43
- TODO/FIXME comments: 1
- Constructs used: Bucket, Function, RestApi
- ⚠️ lib/serverless-react-boilerplate-stack.ts: 4 CfnResource/escape hatch(es)
