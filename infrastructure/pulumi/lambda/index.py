import json
import os
import boto3
import time
from decimal import Decimal
from math import radians, sin, cos, sqrt, atan2
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
SUBSCRIBERS_TABLE = os.environ['SUBSCRIBERS_TABLE']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
NOTIFICATION_RADIUS_KM = 5  # Notify subscribers within 5km
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

def format_notification_message(incident_data):
    """Format the notification message in a user-friendly way"""
    html_message = f"""
    <html>
    <body>
        <h2>⚠️ Emergency Alert: {incident_data['type']}</h2>
        <p><strong>Location:</strong> Near {incident_data.get('address', 'your location')}</p>
        <p><strong>Description:</strong> {incident_data['description']}</p>
        <p><strong>Distance:</strong> {incident_data.get('distance', 'Within')} {NOTIFICATION_RADIUS_KM}km radius</p>
        <p><strong>Time:</strong> {incident_data.get('timestamp', 'Just now')}</p>
        <br>
        <p>View on map: <a href="https://www.google.com/maps?q={incident_data['latitude']},{incident_data['longitude']}">Open in Google Maps</a></p>
        <hr>
        <p style="color: #666; font-size: 12px;">This is an automated alert from Flow Alerts Incident Notification System.</p>
    </body>
    </html>
    """
    return html_message

def put_metric(metric_name, value, unit='Count'):
    """Send custom metric to CloudWatch"""
    try:
        cloudwatch.put_metric_data(
            Namespace='IncidentNotifier',
            MetricData=[{
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }]
        )
    except Exception as e:
        print(f"Error publishing metric {metric_name}: {str(e)}")

def update_subscriber_status(email, subscription_arn, status):
    """Update subscriber's SNS subscription status in DynamoDB"""
    try:
        subscribers_table = dynamodb.Table(SUBSCRIBERS_TABLE)
        subscribers_table.update_item(
            Key={'email': email},
            UpdateExpression='SET subscription_arn = :arn, subscription_status = :status',
            ExpressionAttributeValues={
                ':arn': subscription_arn,
                ':status': status
            }
        )
        return True
    except Exception as e:
        print(f"Error updating subscriber status for {email}: {str(e)}")
        return False

def subscribe_user_to_sns(email):
    """Subscribe a user to SNS notifications with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            # Subscribe the email to the SNS topic and auto-confirm
            response = sns.subscribe(
                TopicArn=SNS_TOPIC_ARN,
                Protocol='email',
                Endpoint=email,
                ReturnSubscriptionArn=True,  # Get the ARN immediately
                Attributes={
                    'FilterPolicy': json.dumps({
                        'subscriber_email': [email]
                    }),
                    'RawMessageDelivery': 'false'  # Enable HTML formatting
                }
            )
            
            subscription_arn = response['SubscriptionArn']
            
            # Auto-confirm the subscription
            sns.set_subscription_attributes(
                SubscriptionArn=subscription_arn,
                AttributeName='DeliveryPolicy',
                AttributeValue=json.dumps({
                    'healthyRetryPolicy': {
                        'numRetries': 3,
                        'minDelayTarget': 20,
                        'maxDelayTarget': 20
                    }
                })
            )
            
            # Update subscriber status in DynamoDB
            if update_subscriber_status(email, subscription_arn, 'CONFIRMED'):
                put_metric('SuccessfulSubscriptions', 1)
                print(f"Successfully subscribed and confirmed {email} to SNS topic: {subscription_arn}")
                
                # Create sample incident for new subscriber
                try:
                    incidents_table = dynamodb.Table('Incidents')
                    incidents_table.put_item(
                        Item={
                            'id': 'test-incident-8',
                            'type': '🔥 Fire',
                            'description': 'Large fire reported in a residential building at Bay Parkway. Emergency services are en route. Please avoid the area and follow evacuation instructions if given.',
                            'latitude': Decimal('40.6140'),
                            'longitude': Decimal('-73.9842'),
                            'timestamp': '2024-02-14T23:46:00Z'
                        }
                    )
                    print(f"Created sample incident for new subscriber {email}")
                except Exception as e:
                    print(f"Error creating sample incident for {email}: {str(e)}")
                
                return True
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidParameter':
                print(f"Invalid email address: {email}")
                put_metric('InvalidEmailAddresses', 1)
                return False
            elif error_code == 'Throttling':
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
            else:
                print(f"AWS error subscribing {email} to SNS: {str(e)}")
                put_metric('FailedSubscriptions', 1)
                return False
        except Exception as e:
            print(f"Error subscribing {email} to SNS: {str(e)}")
            put_metric('FailedSubscriptions', 1)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return False
    
    return False

def validate_dynamodb_record(record):
    """Validate DynamoDB Stream record structure"""
    required_fields = ['eventName', 'dynamodb', 'eventSourceARN']
    if not all(field in record for field in required_fields):
        raise ValueError(f"Missing required fields in record: {required_fields}")
    
    if 'NewImage' not in record['dynamodb']:
        raise ValueError("Missing NewImage in DynamoDB record")
    
    return True

def get_table_name_from_arn(arn):
    """Extract table name from DynamoDB Stream ARN"""
    try:
        return arn.split('/')[1]
    except Exception:
        raise ValueError(f"Invalid DynamoDB Stream ARN format: {arn}")

def process_dynamodb_record(record):
    """Process a DynamoDB record and take appropriate action"""
    try:
        validate_dynamodb_record(record)
        table_name = get_table_name_from_arn(record['eventSourceARN'])
        print(f"Processing record from table: {table_name}, event type: {record['eventName']}")
        
        # For new subscribers or subscriber updates, handle SNS subscription
        if table_name == SUBSCRIBERS_TABLE and record['eventName'] in ['INSERT', 'MODIFY']:
            new_item = record['dynamodb']['NewImage']
            if 'email' in new_item:
                email = new_item['email']['S']
                subscribe_user_to_sns(email)
                
        # For new incidents or incident updates, notify nearby subscribers
        elif table_name == 'Incidents' and record['eventName'] in ['INSERT', 'MODIFY']:
            notifications_sent = process_new_incident(record['dynamodb']['NewImage'])
            put_metric('NotificationsSent', notifications_sent)
                
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        put_metric('ValidationErrors', 1)
    except Exception as e:
        print(f"Error processing record: {str(e)}")
        put_metric('ProcessingErrors', 1)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers using Haversine formula"""
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def get_nearby_subscribers(incident_lat, incident_lon):
    """Get subscribers within notification radius of incident"""
    subscribers_table = dynamodb.Table(SUBSCRIBERS_TABLE)
    nearby_subscribers = []
    
    try:
        # Scan for all subscribers
        response = subscribers_table.scan()
        print(f"Found {len(response['Items'])} total subscribers")
        
        for subscriber in response['Items']:
            try:
                # Get subscriber coordinates
                subscriber_lat = float(subscriber.get('latitude', 0))
                subscriber_lon = float(subscriber.get('longitude', 0))
                
                # Calculate distance
                distance = calculate_distance(
                    incident_lat, 
                    incident_lon,
                    subscriber_lat,
                    subscriber_lon
                )
                
                print(f"Subscriber {subscriber.get('email')} is {distance:.2f}km from incident")
                
                # Add subscriber if within radius
                if distance <= NOTIFICATION_RADIUS_KM:
                    subscriber['distance'] = f"{distance:.1f}"
                    nearby_subscribers.append(subscriber)
                    print(f"Added {subscriber.get('email')} to notification list")
                    
            except (ValueError, TypeError) as e:
                print(f"Error processing subscriber coordinates: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error scanning subscribers table: {str(e)}")
        put_metric('SubscriberScanErrors', 1)
        
    return nearby_subscribers

def process_new_incident(incident):
    """Process a new incident and notify nearby subscribers"""
    try:
        # Extract incident details
        incident_id = incident['id']['S']
        latitude = float(incident.get('latitude', {}).get('N', 0))
        longitude = float(incident.get('longitude', {}).get('N', 0))
        description = incident.get('description', {}).get('S', 'No description')
        incident_type = incident.get('type', {}).get('S', 'Unknown')
        timestamp = incident.get('timestamp', {}).get('S', 'Just now')
        
        print(f"Processing incident: {incident_id} at ({latitude}, {longitude})")
        
        # Find nearby subscribers
        nearby_subscribers = get_nearby_subscribers(latitude, longitude)
        print(f"Found {len(nearby_subscribers)} nearby subscribers")
        
        notifications_sent = 0
        # Send email directly to each nearby subscriber
        ses = boto3.client('ses', region_name='us-east-1')
        
        for subscriber in nearby_subscribers:
            try:
                # Prepare notification message
                message_data = {
                    'incident_id': incident_id,
                    'type': incident_type,
                    'description': description,
                    'latitude': latitude,
                    'longitude': longitude,
                    'timestamp': timestamp,
                    'distance': subscriber.get('distance'),
                    'address': subscriber.get('address'),
                    'subscriber_email': subscriber['email']
                }
                
                # Send email using SES
                ses.send_email(
                    Source='noreply@flowalerts.com',
                    Destination={
                        'ToAddresses': [subscriber['email']]
                    },
                    Message={
                        'Subject': {
                            'Data': f"🚨 Emergency Alert: {incident_type} Incident Nearby"
                        },
                        'Body': {
                            'Html': {
                                'Data': format_notification_message(message_data)
                            }
                        }
                    }
                )
                
                notifications_sent += 1
                print(f"Sent email to {subscriber['email']}")
                
            except Exception as e:
                print(f"Error sending email to {subscriber['email']}: {str(e)}")
                put_metric('NotificationErrors', 1)
                continue
        
        return notifications_sent
        
    except Exception as e:
        print(f"Error processing incident: {str(e)}")
        put_metric('IncidentProcessingErrors', 1)
        return 0

def handler(event, context):
    """Process records from DynamoDB Stream"""
    try:
        print("Received event:", json.dumps(event))
        for record in event['Records']:
            process_dynamodb_record(record)
            
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Successfully processed all records'})
        }
        
    except Exception as e:
        error_message = f"Fatal error in handler: {str(e)}"
        print(error_message)
        put_metric('FatalErrors', 1)
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_message})
        }
