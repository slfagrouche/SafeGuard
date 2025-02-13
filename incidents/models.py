from django.db import models
from .dynamodb import dynamodb_manager
from datetime import datetime

class Incident(models.Model):
    """
    Django model that mirrors the DynamoDB Incident structure.
    Used primarily for admin interface compatibility.
    """
    id = models.CharField(max_length=36, primary_key=True)
    datetime = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField()
    source = models.URLField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)  # S3 URL for the image
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Save to DynamoDB
        incident_data = {
            'datetime': self.datetime,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'description': self.description,
            'source': self.source or '',
            'image_url': self.image_url or '',
            'verified': self.verified
        }
        if not self.id:
            # New incident
            self.id = dynamodb_manager.create_incident(incident_data)
        else:
            # Update existing incident
            incident_data['id'] = self.id
            dynamodb_manager.incidents_table.put_item(Item=incident_data)
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete from DynamoDB
        dynamodb_manager.incidents_table.delete_item(Key={'id': self.id})
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Incident at {self.datetime}"

class Subscriber(models.Model):
    """
    Django model that mirrors the DynamoDB Subscriber structure.
    Used primarily for admin interface compatibility.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField(primary_key=True)
    address = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Save to DynamoDB
        subscriber_data = {
            'name': self.name,
            'email': self.email,
            'address': self.address,
            'latitude': self.latitude if self.latitude is not None else '',
            'longitude': self.longitude if self.longitude is not None else '',
        }
        dynamodb_manager.create_subscriber(subscriber_data)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete from DynamoDB
        dynamodb_manager.subscribers_table.delete_item(Key={'email': self.email})
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.email
