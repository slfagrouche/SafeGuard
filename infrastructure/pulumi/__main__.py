"""A Python Pulumi program to create AWS infrastructure for Flow Alerts"""

import os
import pulumi
import pulumi_aws as aws

# Get configuration from environment variables
config = pulumi.Config()
env = config.require('env')  # e.g. 'dev', 'prod'
project_name = config.require('project_name')

# Resource name prefix
prefix = f"{project_name}-{env}"

# Create S3 bucket with private access
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
    # Block all public access
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# Create DynamoDB tables
incidents_table = aws.dynamodb.Table(f"{prefix}-incident1-{suffix}",
    attributes=[
        aws.dynamodb.TableAttributeArgs(
            name="id",
            type="S",
        ),
    ],
    hash_key="id",
    billing_mode="PAY_PER_REQUEST",
    point_in_time_recovery=aws.dynamodb.TablePointInTimeRecoveryArgs(
        enabled=True,
    ),
    tags={
        "Environment": env,
        "Project": project_name,
    },
)

subscribers_table = aws.dynamodb.Table(f"{prefix}-subscriber1-{suffix}",
    attributes=[
        aws.dynamodb.TableAttributeArgs(
            name="email",
            type="S",
        ),
    ],
    hash_key="email",
    billing_mode="PAY_PER_REQUEST",
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

# Create policy for S3 access
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
                        "s3:DeleteObject"
                    ],
                    "Resource": [
                        "arn:aws:s3:::{args['bucket_name']}/*"
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

# Export the names of resources
pulumi.export('bucket_name', bucket.id)
pulumi.export('incidents_table_name', incidents_table.name)
pulumi.export('subscribers_table_name', subscribers_table.name)
pulumi.export('app_role_arn', app_role.arn)
