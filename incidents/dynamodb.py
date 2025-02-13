import boto3
from django.conf import settings
from datetime import datetime
import uuid

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
            'source': data.get('source', ''),
            'image_url': data.get('image_url', ''),  # S3 URL for the image
            'verified': data.get('verified', False),
            'created_at': datetime.now().isoformat()
        }
        self.incidents_table.put_item(Item=item)
        return item['id']

    def get_all_incidents(self):
        response = self.incidents_table.scan()
        items = response.get('Items', [])
        for item in items:
            item['datetime'] = datetime.fromisoformat(item['datetime'])
            item['latitude'] = float(item['latitude']) if item['latitude'] else None
            item['longitude'] = float(item['longitude']) if item['longitude'] else None
            item['verified'] = bool(item['verified'])
            # Set default placeholder image if no image URL
            if not item.get('image_url'):
                item['image_url'] = '/static/incidents/images/placeholder.jpg'
        return items

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
        item = {
            'email': data['email'],
            'name': data['name'],
            'address': data['address'],
            'latitude': str(data.get('latitude', '')),
            'longitude': str(data.get('longitude', '')),
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

# Create a singleton instance
dynamodb_manager = DynamoDBManager()
