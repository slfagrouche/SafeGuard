import boto3
from django.conf import settings
import uuid
from botocore.exceptions import ClientError
from botocore.config import Config
import mimetypes

class S3Manager:
    def __init__(self):
        # Validate AWS credentials and settings
        if not settings.AWS_ACCESS_KEY_ID:
            print("WARNING: AWS_ACCESS_KEY_ID is not set")
        if not settings.AWS_SECRET_ACCESS_KEY:
            print("WARNING: AWS_SECRET_ACCESS_KEY is not set")
        if not settings.AWS_STORAGE_BUCKET_NAME:
            print("WARNING: AWS_STORAGE_BUCKET_NAME is not set")
        if not settings.AWS_REGION:
            print("WARNING: AWS_REGION is not set")

        print(f"Initializing S3Manager with bucket: {settings.AWS_STORAGE_BUCKET_NAME}, region: {settings.AWS_REGION}")
        
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            config=Config(signature_version='s3v4')  # Use SigV4 for better security
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        
        # Verify bucket exists and is accessible
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            print(f"Successfully connected to S3 bucket: {self.bucket_name}")
        except Exception as e:
            print(f"Error accessing S3 bucket {self.bucket_name}: {str(e)}")

    def upload_image(self, image_data, content_type=None, custom_key=None):
        """
        Upload an image to S3 and return its object key
        
        Args:
            image_data: Base64 encoded image data
            content_type: MIME type of the image (optional)
            custom_key: Custom S3 key/path for the file (optional)
        
        Returns:
            str: The S3 object key of the uploaded image
        """
        try:
            if custom_key:
                filename = custom_key
            else:
                # Generate a unique filename
                file_extension = mimetypes.guess_extension(content_type) if content_type else '.jpg'
                filename = f"incidents/{uuid.uuid4()}{file_extension}"

            # Upload to S3
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=image_data,
                ContentType=content_type or 'image/jpeg'
            )

            return filename

        except ClientError as e:
            print(f"Error uploading to S3: {str(e)}")
            if e.response['Error']['Code'] == 'NoSuchBucket':
                try:
                    # Try to create the bucket
                    self.s3.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': settings.AWS_REGION}
                    )
                    # Try upload again
                    return self.upload_image(image_data, content_type)
                except ClientError as create_error:
                    print(f"Error creating bucket: {str(create_error)}")
            return None

    def delete_image(self, object_key):
        """
        Delete an image from S3
        
        Args:
            object_key: The S3 object key of the image to delete
        """
        try:
            self.s3.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
        except ClientError as e:
            print(f"Error deleting from S3: {str(e)}")
            return False

    def generate_presigned_url(self, object_key, expiration=3600):  # Default 1 hour
        """
        Generate a secure presigned URL for an image with short expiration
        
        Args:
            object_key: The S3 object key of the image
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            str: Presigned URL for the image, or None if generation fails
        """
        if not object_key:
            print("No object key provided to generate_presigned_url")
            return None
            
        try:
            print(f"Attempting to generate presigned URL for bucket: {self.bucket_name}, key: {object_key}")
            
            # Check if the object exists and get its metadata
            try:
                response = self.s3.head_object(Bucket=self.bucket_name, Key=object_key)
                content_type = response.get('ContentType', 'image/jpeg')
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    print(f"Object does not exist in S3: {object_key}")
                    # Only return placeholder for incident images
                    if object_key.startswith('incidents/'):
                        return '/static/incidents/images/placeholder.svg'
                    return None
                else:
                    print(f"Error checking object existence: {str(e)}")
                    return None
            
            # Generate the presigned URL with enhanced parameters
            try:
                params = {
                    'Bucket': self.bucket_name,
                    'Key': object_key,
                    'ResponseContentDisposition': 'inline',
                    'ResponseContentType': content_type,
                    'ResponseCacheControl': 'public, max-age=300',  # 5 min cache
                }
                
                url = self.s3.generate_presigned_url(
                    'get_object',
                    Params=params,
                    ExpiresIn=expiration,
                    HttpMethod='GET'
                )
                print(f"Successfully generated presigned URL for {object_key}")
                return url
            except ClientError as e:
                print(f"Error generating presigned URL: {str(e)}")
                return None
                
        except Exception as e:
            print(f"Unexpected error generating presigned URL: {str(e)}")
            return None

# Create a singleton instance
s3_manager = S3Manager()
