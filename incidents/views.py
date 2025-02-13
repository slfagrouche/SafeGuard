from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .dynamodb import dynamodb_manager
from .s3 import s3_manager
import json
from datetime import datetime
import base64
import re

def home(request):
    return render(request, 'incidents/home.html')

def map_view(request):
    incidents = dynamodb_manager.get_all_incidents()
    # Sort incidents by datetime in descending order
    incidents = sorted(incidents, key=lambda x: x['datetime'], reverse=True)
    return render(request, 'incidents/map.html', {'incidents': incidents})

def ai_help(request):
    return render(request, 'incidents/ai_help.html')

def alerts(request):
    return render(request, 'incidents/alerts.html')

def resources(request):
    return render(request, 'incidents/resources.html')

@csrf_exempt
@require_http_methods(["POST"])
def report_incident(request):
    try:
        data = json.loads(request.body)
        
        # Handle image upload if present
        image_url = ''
        if image_data := data.get('image'):
            # Extract content type from base64 data
            content_type_match = re.match(r'data:(.+);base64,', image_data)
            if content_type_match:
                content_type = content_type_match.group(1)
                # Remove the data URL prefix
                image_data = re.sub(r'data:image/.+;base64,', '', image_data)
                # Convert base64 to bytes
                image_bytes = base64.b64decode(image_data)
                # Upload to S3
                image_url = s3_manager.upload_image(image_bytes, content_type)
                
                if not image_url:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Failed to upload image to S3'
                    })

        # Create incident with image URL if upload was successful
        incident_data = {
            'datetime': datetime.fromisoformat(data['dateTime']),
            'latitude': float(data.get('lat') or data.get('latitude')) if (data.get('lat') or data.get('latitude')) else None,
            'longitude': float(data.get('lng') or data.get('longitude')) if (data.get('lng') or data.get('longitude')) else None,
            'description': data['description'],
            'source': data.get('source', ''),
            'image_url': image_url,
            'verified': False
        }
        incident_id = dynamodb_manager.create_incident(incident_data)
        
        return JsonResponse({
            'status': 'success',
            'id': incident_id,
            'image_url': image_url,
            'message': 'Incident created successfully'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def subscribe(request):
    try:
        data = json.loads(request.body)
        subscriber_data = {
            'name': data['name'],
            'email': data['email'],
            'address': data['address'],
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude')
        }
        email = dynamodb_manager.create_subscriber(subscriber_data)
        return JsonResponse({'status': 'success', 'email': email})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def get_incidents(request):
    incidents = dynamodb_manager.get_all_incidents()
    incident_list = []
    for incident in incidents:
        # Generate a pre-signed URL if image_url exists
        image_url = incident.get('image_url', '')
        if image_url:
            try:
                image_url = s3_manager.generate_presigned_url(image_url)
            except Exception as e:
                print(f"Error generating presigned URL: {str(e)}")
                image_url = '/static/incidents/images/placeholder.svg'

        incident_data = {
            'id': incident['id'],
            'datetime': incident['datetime'].isoformat(),
            'latitude': incident['latitude'],
            'longitude': incident['longitude'],
            'lat': incident['latitude'],
            'lng': incident['longitude'],
            'description': incident['description'],
            'source': incident.get('source', ''),
            'image_url': image_url,
            'verified': incident['verified']
        }
        incident_list.append(incident_data)
    return JsonResponse(incident_list, safe=False)
