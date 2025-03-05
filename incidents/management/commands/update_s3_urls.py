from django.core.management.base import BaseCommand
from incidents.dynamodb import dynamodb_manager
from incidents.s3 import s3_manager
from datetime import datetime
from decimal import Decimal

class Command(BaseCommand):
    help = 'Updates existing S3 URLs in DynamoDB to use object keys'

    def handle(self, *args, **options):
        self.stdout.write('Starting S3 URL migration...')
        
        # Get all incidents
        incidents = dynamodb_manager.get_all_incidents()
        updated_count = 0

        for incident in incidents:
            image_url = incident.get('image_url')
            if image_url and 's3.' in image_url:
                try:
                    # Extract the object key from the URL
                    object_key = image_url.split(f"{s3_manager.bucket_name}.s3.{s3_manager.s3.meta.region_name}.amazonaws.com/")[1]
                    if '?' in object_key:  # Remove any query parameters
                        object_key = object_key.split('?')[0]
                    
                    # Convert datetime to ISO format string
                    if isinstance(incident['datetime'], datetime):
                        incident['datetime'] = incident['datetime'].isoformat()
                    
                    # Update the incident with just the object key
                    incident['image_url'] = object_key
                    
                    # Convert any other datetime fields to strings
                    if 'created_at' in incident and isinstance(incident['created_at'], datetime):
                        incident['created_at'] = incident['created_at'].isoformat()
                    
                    # Convert float coordinates to Decimal
                    if incident.get('latitude'):
                        incident['latitude'] = str(incident['latitude'])
                    if incident.get('longitude'):
                        incident['longitude'] = str(incident['longitude'])
                    dynamodb_manager.update_incident(incident['id'], incident)
                    updated_count += 1
                    
                    self.stdout.write(f'Updated incident {incident["id"]}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error updating incident {incident["id"]}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} incidents'))
