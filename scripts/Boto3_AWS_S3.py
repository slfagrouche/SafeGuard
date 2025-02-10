import boto3
from dotenv import load_dotenv
import os
load_dotenv()

bucket_name = os.getenv('BUCKET_NAME')


s3 = boto3.client('s3')

try: 
    # s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'us-west-1'})
    # print(f"Bucket '{bucket_name}' created successfully.")

    response = s3.head_bucket(Bucket=bucket_name)
    print(f"Bucket really exist and its created at: {response['ResponseMetadata']['HTTPHeaders']['date']}")

except Exception as e:
    print(f"An error occurred: {e}")



# s3.upload_file('/Users/saidlfagrouche/Downloads/christian-wiediger-1XGlbRjt92Q-unsplash.jpg',bucket_name ,"unsplash.jpg" )


response = s3.list_buckets()
print('Existing buckets:')
for bucket in response['Buckets']:
    print(bucket['Name'])

s3.delete_object(Bucket=bucket_name, Key="/Users/saidlfagrouche/Downloads/christian-wiediger-1XGlbRjt92Q-unsplash.jpg")






# List all objects in the bucket
response = s3.list_objects_v2(Bucket=bucket_name)

if 'Contents' in response:
    for obj in response['Contents']:
        print(obj['Key'])
else:
    print(f"No objects found in bucket {bucket_name}.")

s3.delete_object(Bucket=bucket_name, Key='/Users/saidlfagrouche/Downloads/christian-wiediger-1XGlbRjt92Q-unsplash.jpg')
print("File deleted successfully!")

# s3 = boto3.resource('s3')
# print("You successfully connected to S3 Said!")

# bucket_exists = any(bucket.name == bucket_name for bucket in s3.buckets.all())

# if bucket_exists:
#     print(f"Bucket '{bucket_name}' exists.")
# else:
#     print(f"Bucket '{bucket_name}' does not exist. So we make new one!")
#     s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'us-west-1'}) 


# s3.Bucket(bucket_name).upload_file('/Users/saidlfagrouche/Downloads/christian-wiediger-1XGlbRjt92Q-unsplash.jpg', '/Users/saidlfagrouche/Downloads/heather-wilde-JiRMoK6AIQM-unsplash.jpg')

# response = s3.head('


# import boto3
# from botocore.exceptions import ClientError

# # Initialize S3 resource
# s3 = boto3.resource('s3')

# # Define bucket and file details
# bucket_name = 'my-bucket'
# file_key = 'file.txt'

# try:
#     # Attempt to load the object
#     obj = s3.Object(bucket_name, file_key)
#     obj.load()  # Tries to load metadata for the object
#     print(f"File '{file_key}' exists in bucket '{bucket_name}'.")
# except ClientError as e:
#     if e.response['Error']['Code'] == "404":
#         print(f"File '{file_key}' does not exist in bucket '{bucket_name}'.")
#     else:
#         raise
