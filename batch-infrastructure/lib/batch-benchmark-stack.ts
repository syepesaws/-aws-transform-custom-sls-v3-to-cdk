import * as cdk from 'aws-cdk-lib';
import * as batch from 'aws-cdk-lib/aws-batch';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

export class BatchBenchmarkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // --- S3 bucket for results (reuse existing or create new) ---
    const existingBucket = this.node.tryGetContext('existingResultsBucket');
    const resultsBucket = existingBucket
      ? s3.Bucket.fromBucketName(this, 'ResultsBucket', existingBucket)
      : new s3.Bucket(this, 'ResultsBucket', {
          removalPolicy: cdk.RemovalPolicy.RETAIN,
          versioned: true,
        });

    // --- VPC (use default) ---
    const vpc = ec2.Vpc.fromLookup(this, 'Vpc', { isDefault: true });

    // --- Security group ---
    const sg = new ec2.SecurityGroup(this, 'BatchSG', {
      vpc,
      description: 'ATX Batch benchmark jobs',
      allowAllOutbound: true,
    });

    // --- Fargate Spot compute environment ---
    const computeEnv = new batch.FargateComputeEnvironment(this, 'FargateSpotEnv', {
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      securityGroups: [sg],
      spot: true,
      maxvCpus: 64,
    });

    // --- Job queue ---
    const jobQueue = new batch.JobQueue(this, 'BenchmarkQueue', {
      priority: 1,
      computeEnvironments: [{ computeEnvironment: computeEnv, order: 1 }],
    });

    // --- Log group ---
    const logGroup = new logs.LogGroup(this, 'BenchmarkLogs', {
      logGroupName: '/aws/batch/atx-benchmark',
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // --- Job role (what the container can do) ---
    const jobRole = new iam.Role(this, 'JobRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
    });
    jobRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('AWSTransformCustomFullAccess')
    );
    if (resultsBucket instanceof s3.Bucket) {
      resultsBucket.grantReadWrite(jobRole);
    } else {
      jobRole.addToPolicy(new iam.PolicyStatement({
        actions: ['s3:PutObject', 's3:GetObject', 's3:ListBucket'],
        resources: [
          `arn:aws:s3:::${existingBucket}`,
          `arn:aws:s3:::${existingBucket}/*`,
        ],
      }));
    }

    // --- Execution role (Fargate needs this to pull images / send logs) ---
    const executionRole = new iam.Role(this, 'ExecutionRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy'),
      ],
    });

    // --- Job definition using public ATX container ---
    const jobDef = new batch.EcsJobDefinition(this, 'BenchmarkJobDef', {
      jobDefinitionName: 'atx-benchmark',
      container: new batch.EcsFargateContainerDefinition(this, 'Container', {
        image: ecs.ContainerImage.fromRegistry(
          'public.ecr.aws/b7y6j9m3/aws-transform-custom:latest'
        ),
        cpu: 2,
        memory: cdk.Size.gibibytes(4),
        assignPublicIp: true,
        jobRole,
        executionRole,
        logging: ecs.LogDrivers.awsLogs({
          streamPrefix: 'benchmark',
          logGroup,
        }),
        command: ['echo', 'Override me via submit_batch.py'],
      }),
      timeout: cdk.Duration.hours(2),
      retryAttempts: 1,
    });

    // --- Outputs ---
    new cdk.CfnOutput(this, 'JobQueueArn', { value: jobQueue.jobQueueArn });
    new cdk.CfnOutput(this, 'JobDefinitionArn', { value: jobDef.jobDefinitionArn });
    new cdk.CfnOutput(this, 'ResultsBucketName', {
      value: resultsBucket.bucketName,
    });
    new cdk.CfnOutput(this, 'LogGroupName', { value: logGroup.logGroupName });
  }
}
