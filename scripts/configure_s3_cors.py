import boto3
from django.conf import settings
import os
import sys
import django

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flow_alerts.settings')
django.setup()

def configure_s3_cors():
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        # Configure CORS
        cors_configuration = {
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'HEAD'],
                'AllowedOrigins': ['*'],  # In production, replace with specific domains
                'ExposeHeaders': ['ETag'],
                'MaxAgeSeconds': 3000
            }]
        }

        # Set the CORS configuration on the bucket
        s3.put_bucket_cors(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            CORSConfiguration=cors_configuration
        )

        print(f"Successfully configured CORS for bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
        
        # Verify the configuration
        response = s3.get_bucket_cors(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        print("Current CORS configuration:")
        print(response)
        
    except Exception as e:
        print(f"Error configuring CORS: {str(e)}")

if __name__ == '__main__':
    configure_s3_cors()
