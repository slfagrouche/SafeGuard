"""A Python Pulumi program to create AWS infrastructure for Safe Guard"""

import os
import pulumi
import pulumi_aws as aws

# Get configuration from environment variables
config = pulumi.Config()
env = config.require('env')  # e.g. 'dev', 'prod'
project_name = config.require('project_name')

# Resource name prefix
prefix = f"{project_name}-{env}"

# Create S3 bucket with secure presigned URL access
bucket = aws.s3.Bucket(f"{prefix}-storage",
    acl="private",
    versioning=aws.s3.BucketVersioningArgs(
        enabled=True,
    ),
    server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
        rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="AES256",
            ),
        ),
    ),
    # Configure for presigned URL access
    block_public_acls=True,
    block_public_policy=False,  # Allow bucket policies
    ignore_public_acls=True,
    restrict_public_buckets=False,  # Required for presigned URLs
    cors_rules=[aws.s3.BucketCorsRuleArgs(
        allowed_headers=["*"],
        allowed_methods=["GET"],
        allowed_origins=["*"],
        max_age_seconds=3000
    )]
)

# Add bucket policy to allow presigned URL access
bucket_policy = aws.s3.BucketPolicy(f"{prefix}-bucket-policy",
    bucket=bucket.id,
    policy=pulumi.Output.all(bucket_name=bucket.id).apply(
        lambda args: f"""{{
            "Version": "2012-10-17",
            "Statement": [
                {{
                    "Sid": "AllowPresignedURLAccess",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::{args['bucket_name']}/*",
                    "Condition": {{
                        "StringEquals": {{
                            "aws:ResourceAccount": "{aws.get_caller_identity().account_id}"
                        }}
                    }}
                }}
            ]
        }}"""
    )
)

# Create DynamoDB tables with streams enabled
incidents_table = aws.dynamodb.Table(f"{prefix}-incidents",
    attributes=[
        aws.dynamodb.TableAttributeArgs(
            name="id",
            type="S",
        ),
    ],
    hash_key="id",
    billing_mode="PAY_PER_REQUEST",
    stream_enabled=True,
    stream_view_type="NEW_IMAGE",
    point_in_time_recovery=aws.dynamodb.TablePointInTimeRecoveryArgs(
        enabled=True,
    ),
    tags={
        "Environment": env,
        "Project": project_name,
    },
)

subscribers_table = aws.dynamodb.Table(f"{prefix}-subscribers",
    attributes=[
        aws.dynamodb.TableAttributeArgs(
            name="email",
            type="S",
        ),
    ],
    hash_key="email",
    billing_mode="PAY_PER_REQUEST",
    stream_enabled=True,
    stream_view_type="NEW_IMAGE",
    point_in_time_recovery=aws.dynamodb.TablePointInTimeRecoveryArgs(
        enabled=True,
    ),
    tags={
        "Environment": env,
        "Project": project_name,
    },
)

# Create IAM role for application
app_role = aws.iam.Role(f"{prefix}-app-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Effect": "Allow",
            "Sid": ""
        }]
    }""",
)

# Create policy for S3 access with enhanced presigned URL permissions
s3_policy = aws.iam.RolePolicy(f"{prefix}-s3-policy",
    role=app_role.id,
    policy=pulumi.Output.all(bucket_name=bucket.id).apply(
        lambda args: f"""{{
            "Version": "2012-10-17",
            "Statement": [
                {{
                    "Effect": "Allow",
                    "Action": [
                        "s3:PutObject",
                        "s3:GetObject",
                        "s3:DeleteObject",
                        "s3:GetObjectVersion",
                        "s3:PutObjectAcl",
                        "s3:GetObjectAcl"
                    ],
                    "Resource": [
                        "arn:aws:s3:::{args['bucket_name']}/*"
                    ]
                }},
                {{
                    "Effect": "Allow",
                    "Action": [
                        "s3:ListBucket",
                        "s3:GetBucketLocation",
                        "s3:GetBucketPolicy"
                    ],
                    "Resource": [
                        "arn:aws:s3:::{args['bucket_name']}"
                    ]
                }}
            ]
        }}"""
    ),
)

# Create policy for DynamoDB access
dynamodb_policy = aws.iam.RolePolicy(f"{prefix}-dynamodb-policy",
    role=app_role.id,
    policy=pulumi.Output.all(incidents_arn=incidents_table.arn, subscribers_arn=subscribers_table.arn).apply(
        lambda args: f"""{{
            "Version": "2012-10-17",
            "Statement": [
                {{
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Scan",
                        "dynamodb:Query"
                    ],
                    "Resource": [
                        "{args['incidents_arn']}",
                        "{args['subscribers_arn']}"
                    ]
                }}
            ]
        }}"""
    ),
)

# Create Origin Access Identity for CloudFront
origin_access_identity = aws.cloudfront.OriginAccessIdentity(
    f"{prefix}-origin-access-identity",
    comment=f"OAI for {prefix} S3 bucket"
)

# Add bucket policy to allow CloudFront access
bucket_policy = aws.s3.BucketPolicy(f"{prefix}-bucket-policy",
    bucket=bucket.id,
    policy=pulumi.Output.all(bucket_name=bucket.id, oai_id=origin_access_identity.id).apply(
        lambda args: f"""{{
            "Version": "2012-10-17",
            "Statement": [
                {{
                    "Sid": "AllowCloudFrontAccess",
                    "Effect": "Allow",
                    "Principal": {{
                        "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity {args['oai_id']}"
                    }},
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::{args['bucket_name']}/*"
                }}
            ]
        }}"""
    )
)

# Create SNS topic for incident notifications
incident_topic = aws.sns.Topic(f"{prefix}-incident-notifications",
    tags={
        "Environment": env,
        "Project": project_name,
    }
)

# Create Lambda role with enhanced permissions
lambda_role = aws.iam.Role(f"{prefix}-lambda-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Effect": "Allow",
            "Sid": ""
        }]
    }"""
)

# Attach policies to Lambda role with enhanced permissions
lambda_policy = aws.iam.RolePolicy(f"{prefix}-lambda-policy",
    role=lambda_role.id,
    policy=pulumi.Output.all(
        topic_arn=incident_topic.arn,
        incidents_arn=incidents_table.arn,
        subscribers_arn=subscribers_table.arn
    ).apply(
        lambda args: f"""{{
            "Version": "2012-10-17",
            "Statement": [
                {{
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetRecords",
                        "dynamodb:GetShardIterator",
                        "dynamodb:DescribeStream",
                        "dynamodb:ListStreams"
                    ],
                    "Resource": [
                        "{args['incidents_arn']}/stream/*",
                        "{args['subscribers_arn']}/stream/*"
                    ]
                }},
                {{
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:Scan",
                        "dynamodb:Query",
                        "dynamodb:UpdateItem",
                        "dynamodb:PutItem"
                    ],
                    "Resource": [
                        "{args['incidents_arn']}",
                        "{args['subscribers_arn']}"
                    ]
                }},
                {{
                    "Effect": "Allow",
                    "Action": [
                        "sns:Publish",
                        "sns:Subscribe"
                    ],
                    "Resource": "{args['topic_arn']}"
                }},
                {{
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }},
                {{
                    "Effect": "Allow",
                    "Action": [
                        "cloudwatch:PutMetricData"
                    ],
                    "Resource": "*"
                }}
            ]
        }}"""
    )
)

# Create Lambda function
incident_notifier = aws.lambda_.Function(f"{prefix}-incident-notifier",
    role=lambda_role.arn,
    runtime="python3.9",
    handler="index.handler",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./lambda")
    }),
    environment={
        "variables": {
            "SNS_TOPIC_ARN": incident_topic.arn,
            "SUBSCRIBERS_TABLE": subscribers_table.name,
        }
    },
    tags={
        "Environment": env,
        "Project": project_name,
    }
)

# Create DynamoDB Stream triggers for Lambda
incidents_stream_trigger = aws.lambda_.EventSourceMapping(f"{prefix}-incidents-stream-trigger",
    event_source_arn=incidents_table.stream_arn,
    function_name=incident_notifier.arn,
    starting_position="LATEST",
    batch_size=1
)

subscribers_stream_trigger = aws.lambda_.EventSourceMapping(f"{prefix}-subscribers-stream-trigger",
    event_source_arn=subscribers_table.stream_arn,
    function_name=incident_notifier.arn,
    starting_position="LATEST",
    batch_size=1
)

# Export the names of resources
pulumi.export('bucket_name', bucket.id)
pulumi.export('incidents_table_name', incidents_table.name)
pul
umi.export('subscribers_table_name', subscribers_table.name)
pulumi.export('app_role_arn', app_role.arn)
pulumi.export('sns_topic_arn', incident_topic.arn)
