#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BatchBenchmarkStack } from '../lib/batch-benchmark-stack';

const app = new cdk.App();
new BatchBenchmarkStack(app, 'BatchBenchmarkStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? 'us-east-1',
  },
});
