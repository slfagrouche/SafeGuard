from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import asyncio
from .agents import chat
from .dynamodb import dynamodb_manager
from .s3 import s3_manager
from .geocoding import geocoding_manager
import json
from datetime import datetime
import base64
import re

@csrf_protect
@require_http_methods(["POST"])
async def handle_chat(request):
    try:
        data = json.loads(request.body)
        message = data.get('message')
        
        if not message:
            return await JsonResponse({
                'error': 'Message is required'
            }, status=400)
        
        # Get user context from session if available
        user_context = request.session.get('chat_context', {
            'conversation_history': [],
            'current_emergency': None,
            'user_location': None,
            'risk_level': 'low',
        })
        
        # Call the chat function from our agent workflow with context
        response = await chat(message, context=user_context)
        
        # Update session with new context
        request.session['chat_context'] = {
            'conversation_history': user_context['conversation_history'] + [
                {'role': 'user', 'content': message},
                {'role': 'assistant', 'content': response}
            ],
            'current_emergency': user_context.get('current_emergency'),
            'user_location': user_context.get('user_location'),
            'risk_level': user_context.get('risk_level'),
        }
        
        return await JsonResponse({
            'response': response
        })
    except Exception as e:
        print(f"Chat error: {e}")
        return await JsonResponse({
            'error': 'Internal server error'
        }, status=500)

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
        object_key = ''
        if image_data := data.get('image'):
            # Extract content type from base64 data
            content_type_match = re.match(r'data:(.+);base64,', image_data)
            if content_type_match:
                content_type = content_type_match.group(1)
                # Remove the data URL prefix
                image_data = re.sub(r'data:image/.+;base64,', '', image_data)
                # Convert base64 to bytes
                image_bytes = base64.b64decode(image_data)
                # Upload to S3 and get object key
                object_key = s3_manager.upload_image(image_bytes, content_type)
                
                if not object_key:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Failed to upload image to S3'
                    })

        # Create incident with image object key if upload was successful
        incident_data = {
            'datetime': datetime.fromisoformat(data['dateTime']),
            'latitude': float(data['latitude']) if data.get('latitude') else None,
            'longitude': float(data['longitude']) if data.get('longitude') else None,
            'description': data['description'],
            'source': data.get('source', ''),
            'image_url': object_key,  # Store S3 object key instead of URL
            'verified': False,
            'address': data.get('address', '')
        }
        incident_id = dynamodb_manager.create_incident(incident_data)
        
        return JsonResponse({
            'status': 'success',
            'id': incident_id,
            'image_url': s3_manager.generate_presigned_url(object_key) if object_key else '',
            'message': 'Incident created successfully'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def subscribe(request):
    try:
        data = json.loads(request.body)
        
        # If coordinates aren't provided, geocode the address
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not (latitude and longitude) and data.get('address'):
            latitude, longitude = geocoding_manager.geocode_address(data['address'])
            
            if not (latitude and longitude):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Could not geocode the provided address. Please verify the address or provide coordinates directly.'
                })
        
        subscriber_data = {
            'name': data['name'],
            'email': data['email'],
            'address': data['address'],
            'latitude': str(latitude),
            'longitude': str(longitude)
        }
        
        email = dynamodb_manager.create_subscriber(subscriber_data)
        return JsonResponse({
            'status': 'success',
            'email': email,
            'latitude': latitude,
            'longitude': longitude
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_protect
@require_http_methods(["GET"])
def get_chat_history(request):
    try:
        # Get chat context from session
        user_context = request.session.get('chat_context', {
            'conversation_history': [],
            'current_emergency': None,
            'user_location': None,
            'risk_level': 'low',
        })
        
        return JsonResponse({
            'history': user_context.get('conversation_history', []),
            'current_emergency': user_context.get('current_emergency'),
            'user_location': user_context.get('user_location'),
            'risk_level': user_context.get('risk_level'),
        })
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return JsonResponse({
            'error': 'Internal server error'
        }, status=500)

def get_incidents(request):
    incidents = dynamodb_manager.get_all_incidents()
    incident_list = []
    for incident in incidents:
        # Handle image URL with content type preservation
        object_key = incident.get('image_url', '')
        image_url = '/static/incidents/images/placeholder.svg'  # Default placeholder
        
        if object_key and object_key.strip():
            if object_key.startswith('/static/'):
                image_url = object_key
            elif object_key.startswith('incidents/'):  # This is an S3 object key
                try:
                    # Get content type from file extension
                    content_type = 'image/jpeg'  # Default
                    if '.' in object_key:
                        ext = object_key.split('.')[-1].lower()
                        if ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                            content_type = f'image/{ext if ext != "jpg" else "jpeg"}'
                    
                    presigned_url = s3_manager.generate_presigned_url(object_key)
                    if presigned_url:
                        image_url = presigned_url
                        print(f"Generated presigned URL with content-type {content_type} for: {object_key}")
                    else:
                        print(f"Failed to generate presigned URL for: {object_key}")
                except Exception as e:
                    print(f"Error generating presigned URL: {str(e)}")
                    # Keep using placeholder if URL generation fails

        incident_data = {
            'id': incident['id'],
            'datetime': incident['datetime'].isoformat(),
            'latitude': incident['latitude'],
            'longitude': incident['longitude'],
            'description': incident['description'],
            'source': incident.get('source', ''),
            'image_url': image_url,
            'verified': incident['verified'],
            'address': incident.get('address', '')
        }
        incident_list.append(incident_data)
    return JsonResponse(incident_list, safe=False)
