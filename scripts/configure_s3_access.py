import boto3
from django.conf import settings
import os
import sys
import django

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flow_alerts.settings')
django.setup()

def configure_s3_access():
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        # Get current public access block configuration
        try:
            current_config = s3.get_public_access_block(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME
            )
            print("Current public access block configuration:")
            print(current_config)
        except s3.exceptions.NoSuchPublicAccessBlockConfiguration:
            print("No public access block configuration found")

        # Configure public access block to allow presigned URLs while maintaining security
        s3.put_public_access_block(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': False,  # Allow bucket policies
                'RestrictPublicBuckets': False  # Allow presigned URL access
            }
        )
        print("\nUpdated public access block configuration")

        # Update bucket policy to allow GetObject through presigned URLs
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowPresignedURLs",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{settings.AWS_STORAGE_BUCKET_NAME}/incidents/*"
                }
            ]
        }

        s3.put_bucket_policy(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Policy=str(bucket_policy).replace("'", '"')
        )
        print("\nUpdated bucket policy to allow presigned URL access")

        # Verify the configurations
        new_public_access = s3.get_public_access_block(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME
        )
        print("\nNew public access block configuration:")
        print(new_public_access)

        bucket_policy = s3.get_bucket_policy(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME
        )
        print("\nCurrent bucket policy:")
        print(bucket_policy)

    except Exception as e:
        print(f"Error configuring S3 access: {str(e)}")

if __name__ == '__main__':
    configure_s3_access()
