import boto3
from django.conf import settings
from datetime import datetime
import uuid
from .notifications import sns_manager

class DynamoDBManager:
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.incidents_table = self.dynamodb.Table(settings.DYNAMODB_INCIDENTS_TABLE)
        self.subscribers_table = self.dynamodb.Table(settings.DYNAMODB_SUBSCRIBERS_TABLE)

    def create_tables(self):
        try:
            # Check if tables exist
            existing_tables = self.dynamodb.meta.client.list_tables()['TableNames']
            
            # Create Incidents table if it doesn't exist
            if settings.DYNAMODB_INCIDENTS_TABLE not in existing_tables:
                self.dynamodb.create_table(
                    TableName=settings.DYNAMODB_INCIDENTS_TABLE,
                    KeySchema=[
                        {'AttributeName': 'id', 'KeyType': 'HASH'},
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'id', 'AttributeType': 'S'},
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                # Wait until the table exists
                table = self.dynamodb.Table(settings.DYNAMODB_INCIDENTS_TABLE)
                table.meta.client.get_waiter('table_exists').wait(TableName=settings.DYNAMODB_INCIDENTS_TABLE)

            # Create Subscribers table if it doesn't exist
            if settings.DYNAMODB_SUBSCRIBERS_TABLE not in existing_tables:
                self.dynamodb.create_table(
                    TableName=settings.DYNAMODB_SUBSCRIBERS_TABLE,
                    KeySchema=[
                        {'AttributeName': 'email', 'KeyType': 'HASH'},
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'email', 'AttributeType': 'S'},
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                # Wait until the table exists
                table = self.dynamodb.Table(settings.DYNAMODB_SUBSCRIBERS_TABLE)
                table.meta.client.get_waiter('table_exists').wait(TableName=settings.DYNAMODB_SUBSCRIBERS_TABLE)

            # Initialize table references
            self.incidents_table = self.dynamodb.Table(settings.DYNAMODB_INCIDENTS_TABLE)
            self.subscribers_table = self.dynamodb.Table(settings.DYNAMODB_SUBSCRIBERS_TABLE)

        except Exception as e:
            raise Exception(f"Error creating DynamoDB tables: {str(e)}")

    # Incident Operations
    def create_incident(self, data):
        item = {
            'id': str(uuid.uuid4()),
            'datetime': data['datetime'].isoformat(),
            'latitude': str(data['latitude']) if data['latitude'] is not None else '',
            'longitude': str(data['longitude']) if data['longitude'] is not None else '',
            'description': data['description'],
            'type': data.get('type', 'Unknown'),
            'source': data.get('source', ''),
            'image_url': data.get('image_url', ''),  # S3 object key
            'verified': data.get('verified', False),
            'created_at': datetime.now().isoformat()
        }
        
        # Save incident
        self.incidents_table.put_item(Item=item)
        
        # Get all subscribers
        response = self.subscribers_table.scan()
        subscribers = response.get('Items', [])
        
        # For each subscriber, check if they should be notified
        for subscriber in subscribers:
            # First verify their subscription status is current
            email = subscriber['email']
            sns_status = sns_manager.get_subscription_status(email)
            
            if sns_status and sns_status['status'] == 'CONFIRMED':
                # Update subscriber status if needed
                if subscriber.get('subscription_status') != 'CONFIRMED':
                    self.update_subscriber(email, {
                        'subscription_status': 'CONFIRMED',
                        'subscription_arn': sns_status['subscription_arn']
                    })
                
                # Calculate distance
                try:
                    from math import radians, sin, cos, sqrt, asin
                    
                    def haversine_distance(lat1, lon1, lat2, lon2):
                        R = 6371  # Earth's radius in km
                        
                        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
                        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                        
                        dlat = lat2 - lat1
                        dlon = lon2 - lon1
                        
                        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                        c = 2 * asin(sqrt(a))
                        
                        return R * c
                    
                    distance = haversine_distance(
                        subscriber['latitude'],
                        subscriber['longitude'],
                        item['latitude'],
                        item['longitude']
                    )
                    
                    # If incident is within 5km, send notification
                    if distance <= 5:
                        message = (
                            f"New incident reported {distance:.2f}km from your location.\n"
                            f"Description: {item['description']}\n"
                            f"Type: {item['type']}\n"
                            f"Time: {data['datetime'].strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        
                        sns_manager.send_notification(
                            subject="New Nearby Incident Alert",
                            message=message,
                            email=email
                        )
                except (ValueError, TypeError) as e:
                    print(f"Error calculating distance for subscriber {email}: {str(e)}")
                    continue
        
        return item['id']

    def get_all_incidents(self):
        response = self.incidents_table.scan()
        items = response.get('Items', [])
        formatted_items = []
        
        for item in items:
            try:
                formatted_item = {
                    'id': item.get('id', ''),
                    'datetime': datetime.fromisoformat(item['datetime']) if 'datetime' in item else datetime.now(),
                    'latitude': float(item['latitude']) if item.get('latitude') else None,
                    'longitude': float(item['longitude']) if item.get('longitude') else None,
                    'description': item.get('description', ''),
                    'type': item.get('type', 'Unknown'),
                    'source': item.get('source', ''),
                    'verified': bool(item.get('verified', False)),
                    'created_at': item.get('created_at', datetime.now().isoformat()),
                    'image_url': item.get('image_url', '')  # Return empty string if no image
                }
                formatted_items.append(formatted_item)
            except (ValueError, TypeError) as e:
                print(f"Error formatting incident {item.get('id', 'unknown')}: {str(e)}")
                continue
                
        return formatted_items

    def get_incident(self, incident_id):
        response = self.incidents_table.get_item(Key={'id': incident_id})
        item = response.get('Item')
        if item:
            item['datetime'] = datetime.fromisoformat(item['datetime'])
            item['latitude'] = float(item['latitude']) if item['latitude'] else None
            item['longitude'] = float(item['longitude']) if item['longitude'] else None
            item['verified'] = bool(item['verified'])
        return item

    # Subscriber Operations
    def create_subscriber(self, data):
        try:
            # Subscribe to SNS first
            subscription = sns_manager.subscribe_email(data['email'])
            
            # Prepare item for DynamoDB
            item = {
                'email': data['email'],
                'name': data['name'],
                'address': data['address'],
                'latitude': str(data.get('latitude', '40.608971')),
                'longitude': str(data.get('longitude', '-73.9867549')),
                'subscription_status': subscription['status'],
                'subscription_arn': subscription['subscription_arn'],
                'created_at': datetime.now().isoformat()
            }
            
            # Ensure coordinates are strings
            if isinstance(item['latitude'], float):
                item['latitude'] = str(item['latitude'])
            if isinstance(item['longitude'], float):
                item['longitude'] = str(item['longitude'])
                
            # Save to DynamoDB
            self.subscribers_table.put_item(Item=item)
            
            # Check if SNS status is different from what we initially got
            current_sns_status = sns_manager.get_subscription_status(data['email'])
            if current_sns_status and current_sns_status['status'] != subscription['status']:
                # Update item with current SNS status
                item['subscription_status'] = current_sns_status['status']
                item['subscription_arn'] = current_sns_status['subscription_arn']
                self.subscribers_table.put_item(Item=item)
                
                # Send welcome notification if confirmed
                if current_sns_status['status'] == 'CONFIRMED':
                    sns_manager.send_notification(
                        subject="Welcome to Flow Alerts!",
                        message="Thank you for subscribing to Flow Alerts. You will receive notifications about new incidents in your area.",
                        email=data['email']
                    )
            
            return item['email']
            
        except Exception as e:
            print(f"Error creating subscriber: {str(e)}")
            # If SNS fails, try creating with default values
            item = {
                'email': data['email'],
                'name': data['name'],
                'address': data['address'],
                'latitude': '40.608971',
                'longitude': '-73.9867549',
                'subscription_status': 'PENDING',
                'subscription_arn': '',
                'created_at': datetime.now().isoformat()
            }
            self.subscribers_table.put_item(Item=item)
            return item['email']

    def get_subscriber(self, email):
        response = self.subscribers_table.get_item(Key={'email': email})
        item = response.get('Item')
        if item and item.get('latitude'):
            item['latitude'] = float(item['latitude'])
            item['longitude'] = float(item['longitude'])
        return item

    def update_subscriber(self, email, data):
        """
        Update an existing subscriber in DynamoDB
        
        Args:
            email: The email of the subscriber to update
            data: Dictionary containing the subscriber data to update
        """
        update_expr = "SET "
        expr_names = {}
        expr_values = {}
        
        # Build update expression dynamically
        for key, value in data.items():
            if key != 'email':  # Skip the primary key
                update_expr += f"#{key} = :{key}, "
                expr_names[f"#{key}"] = key
                expr_values[f":{key}"] = value

        # Remove trailing comma and space
        update_expr = update_expr.rstrip(", ")

        try:
            self.subscribers_table.update_item(
                Key={'email': email},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values
            )
            return True
        except Exception as e:
            print(f"Error updating subscriber: {str(e)}")
            return False

    def update_incident(self, incident_id, data):
        """
        Update an existing incident in DynamoDB
        
        Args:
            incident_id: The ID of the incident to update
            data: Dictionary containing the incident data
        """
        update_expr = "SET "
        expr_names = {}
        expr_values = {}
        
        # Build update expression dynamically
        for key, value in data.items():
            if key != 'id':  # Skip the primary key
                update_expr += f"#{key} = :{key}, "
                expr_names[f"#{key}"] = key
                expr_values[f":{key}"] = value

        # Remove trailing comma and space
        update_expr = update_expr.rstrip(", ")

        try:
            self.incidents_table.update_item(
                Key={'id': incident_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values
            )
            return True
        except Exception as e:
            print(f"Error updating incident: {str(e)}")
            return False

# Create a singleton instance
dynamodb_manager = DynamoDBManager()
