from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from .dynamodb import dynamodb_manager
from .s3 import s3_manager
from datetime import datetime
import json
from .models import Incident, Subscriber

class IncidentAdmin(admin.ModelAdmin):
    change_list_template = 'admin/incidents/incident_list.html'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.incident_list_view, name='incident_list'),
            path('<str:incident_id>/toggle-verify/', self.toggle_verify, name='toggle_verify'),
            path('<str:incident_id>/delete/', self.delete_incident, name='delete_incident'),
        ]
        return custom_urls + urls

    def incident_list_view(self, request):
        # Get all incidents from DynamoDB
        incidents = dynamodb_manager.get_all_incidents()
        
        # Sort by datetime in descending order
        incidents.sort(key=lambda x: x['datetime'], reverse=True)
        
        context = {
            'incidents': incidents,
            'title': 'Incidents',
            'opts': self.model._meta,
            'cl': self,
        }
        return render(request, 'admin/incidents/incident_list.html', context)

    def toggle_verify(self, request, incident_id):
        try:
            incident = dynamodb_manager.get_incident(incident_id)
            if incident:
                # Update verification status
                incident['verified'] = not incident['verified']
                dynamodb_manager.incidents_table.put_item(Item=incident)
                messages.success(request, 'Verification status updated successfully.')
            else:
                messages.error(request, 'Incident not found.')
        except Exception as e:
            messages.error(request, f'Error updating verification status: {str(e)}')
        return redirect('admin:incident_list')

    def delete_incident(self, request, incident_id):
        try:
            incident = dynamodb_manager.get_incident(incident_id)
            if incident:
                # Delete image from S3 if exists
                if 'image_key' in incident:
                    s3_manager.delete_image(incident['image_key'])
                
                # Delete from DynamoDB
                dynamodb_manager.incidents_table.delete_item(Key={'id': incident_id})
                messages.success(request, 'Incident deleted successfully.')
            else:
                messages.error(request, 'Incident not found.')
        except Exception as e:
            messages.error(request, f'Error deleting incident: {str(e)}')
        return redirect('admin:incident_list')

    def has_add_permission(self, request):
        return False  # Disable add through admin

    def has_change_permission(self, request, obj=None):
        return True  # Allow verification toggle

    def has_delete_permission(self, request, obj=None):
        return True  # Allow deletion

class SubscriberAdmin(admin.ModelAdmin):
    change_list_template = 'admin/incidents/subscriber_list.html'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.subscriber_list_view, name='subscriber_list'),
            path('<str:email>/delete/', self.delete_subscriber, name='delete_subscriber'),
        ]
        return custom_urls + urls

    def subscriber_list_view(self, request):
        # Scan subscribers table
        response = dynamodb_manager.subscribers_table.scan()
        subscribers = response.get('Items', [])
        
        # Sort by created_at in descending order
        subscribers.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        context = {
            'subscribers': subscribers,
            'title': 'Subscribers',
            'opts': self.model._meta,
            'cl': self,
        }
        return render(request, 'admin/incidents/subscriber_list.html', context)

    def delete_subscriber(self, request, email):
        try:
            subscriber = dynamodb_manager.get_subscriber(email)
            if subscriber:
                # Delete from DynamoDB
                dynamodb_manager.subscribers_table.delete_item(Key={'email': email})
                messages.success(request, 'Subscriber deleted successfully.')
            else:
                messages.error(request, 'Subscriber not found.')
        except Exception as e:
            messages.error(request, f'Error deleting subscriber: {str(e)}')
        return redirect('admin:subscriber_list')

    def has_add_permission(self, request):
        return False  # Disable add through admin

    def has_change_permission(self, request, obj=None):
        return False  # Disable editing

    def has_delete_permission(self, request, obj=None):
        return True  # Allow deletion

# Register the admin classes
admin.site.register(Incident, IncidentAdmin)
admin.site.register(Subscriber, SubscriberAdmin)
