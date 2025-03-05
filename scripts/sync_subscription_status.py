import os
import django
from dotenv import load_dotenv

# Add project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flow_alerts.settings')
django.setup()

from incidents.dynamodb import dynamodb_manager
from incidents.notifications import sns_manager

def sync_subscription_status():
    email = 'test@inths.org'
    
    # Get current statuses
    print("\nGetting current status...")
    subscriber = dynamodb_manager.get_subscriber(email)
    sns_status = sns_manager.get_subscription_status(email)
    
    if not subscriber or not sns_status:
        print("Could not find subscriber or SNS subscription")
        return
    
    print(f"DynamoDB status: {subscriber.get('subscription_status')}")
    print(f"SNS status: {sns_status['status']}")
    
    # Update DynamoDB if statuses don't match
    if subscriber.get('subscription_status') != sns_status['status']:
        print("\nUpdating DynamoDB subscription status...")
        dynamodb_manager.update_subscriber(email, {
            'subscription_status': sns_status['status'],
            'subscription_arn': sns_status['subscription_arn']
        })
        print("Status updated successfully")
    else:
        print("\nStatuses are already in sync")

if __name__ == "__main__":
    load_dotenv()
    sync_subscription_status()
