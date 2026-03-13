import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import * as codepipeline from 'aws-cdk-lib/aws-codepipeline';
import * as codepipeline_actions from 'aws-cdk-lib/aws-codepipeline-actions';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

interface RepoConfig {
  name: string;
  url: string;
  stars?: number;
}

interface BenchmarkConfig {
  transformation_name: string;
  build_command: string;
  repos: RepoConfig[];
}

function loadConfig(): BenchmarkConfig {
  const configPath = path.resolve(__dirname, '../../config.yaml');
  return yaml.parse(fs.readFileSync(configPath, 'utf8'));
}

export class BenchmarkPipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const config = loadConfig();

    // --- S3 bucket for results ---
    const resultsBucket = new s3.Bucket(this, 'ResultsBucket', {
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      versioned: true,
    });

    // --- CodeConnection (GitLab) — must be completed in console after deploy ---
    const connectionArn = new cdk.CfnParameter(this, 'ConnectionArn', {
      type: 'String',
      description: 'ARN of the CodeConnection to GitLab (create in console first)',
    });

    // --- Pipeline artifacts ---
    const sourceOutput = new codepipeline.Artifact('SourceOutput');

    // --- ATX policy for CodeBuild roles ---
    const atxPolicy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['transform-custom:*'],
      resources: ['*'],
    });

    // --- Per-repo CodeBuild projects (parallel benchmark execution) ---
    const benchmarkActions: codepipeline_actions.CodeBuildAction[] = [];

    for (const repo of config.repos) {
      const project = new codebuild.PipelineProject(this, `Bench-${repo.name}`, {
        buildSpec: codebuild.BuildSpec.fromSourceFilename('benchmark-pipeline/buildspecs/benchmark.yml'),
        environment: {
          buildImage: codebuild.LinuxBuildImage.STANDARD_7_0,
          computeType: codebuild.ComputeType.MEDIUM,
        },
        environmentVariables: {
          REPO_NAME: { value: repo.name },
          REPO_URL: { value: repo.url },
          REPO_STARS: { value: String(repo.stars ?? 'N/A') },
          TD_NAME: { value: config.transformation_name },
          BUILD_CMD: { value: config.build_command },
          RESULTS_BUCKET: { value: resultsBucket.bucketName },
        },
        timeout: cdk.Duration.hours(1),
      });

      project.addToRolePolicy(atxPolicy);
      resultsBucket.grantWrite(project);

      benchmarkActions.push(new codepipeline_actions.CodeBuildAction({
        actionName: repo.name,
        project,
        input: sourceOutput,
      }));
    }

    // --- Aggregator CodeBuild project ---
    const aggregator = new codebuild.PipelineProject(this, 'Aggregator', {
      buildSpec: codebuild.BuildSpec.fromSourceFilename('benchmark-pipeline/buildspecs/aggregate.yml'),
      environment: {
        buildImage: codebuild.LinuxBuildImage.STANDARD_7_0,
        computeType: codebuild.ComputeType.SMALL,
      },
      environmentVariables: {
        RESULTS_BUCKET: { value: resultsBucket.bucketName },
      },
      timeout: cdk.Duration.minutes(10),
    });

    resultsBucket.grantReadWrite(aggregator);

    // --- CodePipeline ---
    new codepipeline.Pipeline(this, 'BenchmarkPipeline', {
      pipelineName: 'atx-sls-v3-to-cdk-benchmark',
      stages: [
        {
          stageName: 'Source',
          actions: [
            new codepipeline_actions.CodeStarConnectionsSourceAction({
              actionName: 'GitHub',
              connectionArn: connectionArn.valueAsString,
              owner: 'syepesaws',
              repo: '-aws-transform-custom-sls-v3-to-cdk',
              branch: 'main',
              output: sourceOutput,
            }),
          ],
        },
        {
          stageName: 'Benchmark',
          actions: benchmarkActions,
        },
        {
          stageName: 'Aggregate',
          actions: [
            new codepipeline_actions.CodeBuildAction({
              actionName: 'AggregateResults',
              project: aggregator,
              input: sourceOutput,
            }),
          ],
        },
      ],
    });

    // --- Outputs ---
    new cdk.CfnOutput(this, 'ResultsBucketName', { value: resultsBucket.bucketName });
  }
}
