import os
import django
from datetime import datetime
from dotenv import load_dotenv
import math

# Add project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flow_alerts.settings')
django.setup()

from incidents.dynamodb import dynamodb_manager
from incidents.notifications import sns_manager

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers"""
    R = 6371  # Earth's radius in km
    
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def test_incident_notification():
    # Get subscriber info
    subscriber_email = 'slfagrouche@inths.org'
    subscriber = dynamodb_manager.get_subscriber(subscriber_email)
    
    if not subscriber:
        print(f"Subscriber {subscriber_email} not found")
        return
    
    print(f"Subscriber location: {subscriber['latitude']}, {subscriber['longitude']}")
    
    # Create a test incident 1km away from subscriber
    subscriber_lat = float(subscriber['latitude'])
    subscriber_lon = float(subscriber['longitude'])
    
    # Approximate 1km offset
    incident_lat = subscriber_lat + 0.009  # ~1km north
    incident_lon = subscriber_lon
    
    incident_data = {
        'datetime': datetime.now(),
        'latitude': incident_lat,
        'longitude': incident_lon,
        'description': 'Test incident near subscriber location',
        'type': 'Test',
        'verified': True
    }
    
    try:
        # Create incident
        print("Creating test incident...")
        incident_id = dynamodb_manager.create_incident(incident_data)
        print(f"Created incident with ID: {incident_id}")
        
        # Calculate actual distance
        distance = calculate_distance(
            subscriber_lat, subscriber_lon,
            incident_lat, incident_lon
        )
        print(f"Distance from subscriber: {distance:.2f}km")
        
        # Send notification
        print("Sending notification...")
        message = (
            f"New incident reported {distance:.2f}km from your location.\n"
            f"Description: {incident_data['description']}\n"
            f"Type: {incident_data['type']}\n"
            f"Time: {incident_data['datetime'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        success = sns_manager.send_notification(
            subject="New Nearby Incident Alert",
            message=message,
            email=subscriber_email
        )
        print(f"Notification sent: {'Success' if success else 'Failed'}")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    test_incident_notification()
