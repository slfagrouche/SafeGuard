from django.db import models

class Incident(models.Model):
    datetime = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField()
    source = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='incidents/', blank=True, null=True)
    image_data = models.TextField(blank=True, null=True)  # Add this line
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Incident at {self.datetime}"

class Subscriber(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    address = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email