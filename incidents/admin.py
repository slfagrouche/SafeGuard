# admin.py

from django.contrib import admin
from .models import Incident, Subscriber
from django.utils.safestring import mark_safe

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('datetime', 'description', 'location', 'source', 'verified', 'created_at', 'image_preview')
    list_filter = ('verified', 'created_at')
    search_fields = ('description', 'source')
    list_editable = ('verified',)

    def location(self, obj):
        return f"Lat: {obj.latitude}, Lng: {obj.longitude}"
    
    def image_preview(self, obj):
        if obj.image_data:
            return mark_safe(f'<img src="{obj.image_data}" width="100"/>')
        return "No Image"
    
    image_preview.short_description = 'Image'

    image_preview.short_description = 'Image'

    fieldsets = (
        ('Basic Info', {
            'fields': ('datetime', 'description')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Media', {
            'fields': ('image', 'image_preview', 'source')
        }),
        ('Status', {
            'fields': ('verified',)
        })
    )

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'address', 'location', 'created_at')
    search_fields = ('name', 'email', 'address')

    def location(self, obj):
        if obj.latitude and obj.longitude:
            return f"Lat: {obj.latitude}, Lng: {obj.longitude}"
        return "No location"
