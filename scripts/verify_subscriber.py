import os
import django
from dotenv import load_dotenv
import json
from datetime import datetime

# Add project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flow_alerts.settings')
django.setup()

from incidents.dynamodb import dynamodb_manager
from incidents.notifications import sns_manager

def verify_subscriber():
    email = 'test@inths.org'
    
    # Get subscriber from DynamoDB
    print("\nChecking DynamoDB subscriber data...")
    subscriber = dynamodb_manager.get_subscriber(email)
    if subscriber:
        print("\nSubscriber Data in DynamoDB:")
        print(json.dumps(subscriber, indent=2, default=str))
    else:
        print(f"No subscriber found with email: {email}")
        return
    
    # Verify SNS subscription
    print("\nChecking SNS subscription status...")
    sns_status = sns_manager.get_subscription_status(email)
    if sns_status:
        print("\nSNS Subscription Status:")
        print(json.dumps(sns_status, indent=2))
    else:
        print(f"No SNS subscription found for email: {email}")
    
    # Verify required fields
    required_fields = ['email', 'name', 'address', 'latitude', 'longitude', 'subscription_status']
    missing_fields = [field for field in required_fields if field not in subscriber]
    if missing_fields:
        print(f"\nWARNING: Missing required fields: {', '.join(missing_fields)}")
    else:
        print("\nAll required fields are present")
    
    # Verify data types
    try:
        float(subscriber['latitude'])
        float(subscriber['longitude'])
        print("\nCoordinates are valid numbers")
    except (ValueError, KeyError):
        print("\nWARNING: Invalid coordinate values")
    
    # Verify subscription status matches between DynamoDB and SNS
    if sns_status and 'status' in sns_status:
        dynamo_status = subscriber.get('subscription_status', '')
        sns_confirmed = sns_status['status'] == 'CONFIRMED'
        dynamo_confirmed = dynamo_status == 'CONFIRMED'
        
        if sns_confirmed == dynamo_confirmed:
            print("\nSubscription status is consistent between DynamoDB and SNS")
        else:
            print("\nWARNING: Subscription status mismatch between DynamoDB and SNS")
            print(f"DynamoDB status: {dynamo_status}")
            print(f"SNS status: {sns_status['status']}")

if __name__ == "__main__":
    load_dotenv()
    verify_subscriber()
