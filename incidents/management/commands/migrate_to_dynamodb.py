from django.core.management.base import BaseCommand
from django.db import connections
from incidents.models import Incident, Subscriber
from incidents.dynamodb import dynamodb_manager
import sqlite3
from botocore.exceptions import ClientError

class Command(BaseCommand):
    help = 'Migrates data from SQLite to DynamoDB'

    def handle(self, *args, **options):
        self.stdout.write('Starting migration from SQLite to DynamoDB...')

        try:
            # Verify DynamoDB tables exist
            try:
                dynamodb_manager.incidents_table.table_status
                dynamodb_manager.subscribers_table.table_status
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    self.stdout.write(self.style.ERROR('DynamoDB tables not found. Please run create_dynamodb_tables first.'))
                    return
                raise e

            # Count records
            incident_count = Incident.objects.using('default').count()
            subscriber_count = Subscriber.objects.using('default').count()

            if incident_count == 0 and subscriber_count == 0:
                self.stdout.write(self.style.SUCCESS('No data to migrate - database is empty'))
                return

            # Migrate Incidents
            if incident_count > 0:
                self.stdout.write(f'Migrating {incident_count} incidents...')
                migrated_incidents = 0
                incidents = Incident.objects.using('default').all()
                for incident in incidents:
                    try:
                        incident_data = {
                            'datetime': incident.datetime,
                            'latitude': incident.latitude,
                            'longitude': incident.longitude,
                            'description': incident.description,
                            'source': incident.source or '',
                            'image_url': incident.image_url or '',  # Use existing image_url or empty string
                            'verified': incident.verified
                        }
                        dynamodb_manager.create_incident(incident_data)
                        migrated_incidents += 1
                        if migrated_incidents % 10 == 0:  # Progress update every 10 items
                            self.stdout.write(f'Migrated {migrated_incidents}/{incident_count} incidents')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'Error migrating incident {incident.id}: {str(e)}'))

            # Migrate Subscribers
            if subscriber_count > 0:
                self.stdout.write(f'Migrating {subscriber_count} subscribers...')
                migrated_subscribers = 0
                subscribers = Subscriber.objects.using('default').all()
                for subscriber in subscribers:
                    try:
                        subscriber_data = {
                            'name': subscriber.name,
                            'email': subscriber.email,
                            'address': subscriber.address,
                            'latitude': subscriber.latitude if subscriber.latitude is not None else '',
                            'longitude': subscriber.longitude if subscriber.longitude is not None else ''
                        }
                        dynamodb_manager.create_subscriber(subscriber_data)
                        migrated_subscribers += 1
                        if migrated_subscribers % 10 == 0:  # Progress update every 10 items
                            self.stdout.write(f'Migrated {migrated_subscribers}/{subscriber_count} subscribers')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'Error migrating subscriber {subscriber.email}: {str(e)}'))

            self.stdout.write(self.style.SUCCESS(
                f'Migration completed:\n'
                f'- Incidents: {migrated_incidents}/{incident_count}\n'
                f'- Subscribers: {migrated_subscribers}/{subscriber_count}'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during migration: {str(e)}'))
