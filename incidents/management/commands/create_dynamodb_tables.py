from django.core.management.base import BaseCommand
from incidents.dynamodb import dynamodb_manager

class Command(BaseCommand):
    help = 'Creates DynamoDB tables for the application'

    def handle(self, *args, **options):
        try:
            dynamodb_manager.create_tables()
            self.stdout.write(self.style.SUCCESS('Successfully created DynamoDB tables'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating DynamoDB tables: {str(e)}'))
