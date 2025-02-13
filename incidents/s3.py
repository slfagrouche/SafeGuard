import boto3
from django.conf import settings
import uuid
from botocore.exceptions import ClientError
import mimetypes

class S3Manager:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def upload_image(self, image_data, content_type=None, custom_key=None):
        """
        Upload an image to S3 and return its URL
        
        Args:
            image_data: Base64 encoded image data
            content_type: MIME type of the image (optional)
            custom_key: Custom S3 key/path for the file (optional)
        
        Returns:
            str: The URL of the uploaded image
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

            # Generate the URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
            return url

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

    def delete_image(self, image_url):
        """
        Delete an image from S3
        
        Args:
            image_url: The URL of the image to delete
        """
        try:
            # Extract the key from the URL
            key = image_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
            
            self.s3.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError as e:
            print(f"Error deleting from S3: {str(e)}")
            return False

    def generate_presigned_url(self, image_url, expiration=3600):
        """
        Generate a presigned URL for an image
        
        Args:
            image_url: The URL of the image
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            str: Presigned URL for the image
        """
        try:
            # Extract the key from the URL
            key = image_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
            
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {str(e)}")
            return None

# Create a singleton instance
s3_manager = S3Manager()
