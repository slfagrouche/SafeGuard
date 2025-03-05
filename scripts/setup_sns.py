import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def setup_sns():
    # Initialize SNS client
    sns = boto3.client(
        'sns',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    
    try:
        # Create SNS topic
        topic = sns.create_topic(Name='flow-alerts-notifications')
        topic_arn = topic['TopicArn']
        print(f"Created SNS topic: {topic_arn}")
        
        # Add topic ARN to .env file
        with open('.env', 'a') as f:
            f.write(f"\nSNS_TOPIC_ARN={topic_arn}")
        
        print("Added SNS_TOPIC_ARN to .env file")
        return topic_arn
        
    except Exception as e:
        print(f"Error setting up SNS: {str(e)}")
        return None

if __name__ == "__main__":
    setup_sns()
