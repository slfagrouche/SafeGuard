import os
import sys
import django
from dotenv import load_dotenv

# Add project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flow_alerts.settings')
django.setup()

from incidents.dynamodb import dynamodb_manager
from incidents.notifications import sns_manager

def test_subscription():
    # Test data
    subscriber_data = {
        'email': 'test@inths.org',
        'name': 'Test User',
        'address': '123 Test St',
        'latitude': '40.7128',
        'longitude': '-74.0060'
    }
    
    try:
        # Create subscriber
        print("Creating subscriber...")
        email = dynamodb_manager.create_subscriber(subscriber_data)
        print(f"Subscriber created with email: {email}")
        
        # Get subscription status
        print("Checking subscription status...")
        status = sns_manager.get_subscription_status(email)
        print(f"Subscription status: {status}")
        
        # Send test notification
        print("Sending test notification...")
        success = sns_manager.send_notification(
            subject="Flow Alerts Test Notification",
            message="This is a test notification to verify your subscription to Flow Alerts.",
            email=email
        )
        print(f"Test notification sent: {'Success' if success else 'Failed'}")
        
        print("\nIMPORTANT: Check your email for the subscription confirmation link and click it to complete the setup.")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    test_subscription()
