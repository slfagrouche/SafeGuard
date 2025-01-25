# views.py
from django.shortcuts import render
from django.http import JsonResponse
from .models import Incident, Subscriber
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt  # Add if needed for API endpoints
import json

def home(request):
    return render(request, 'incidents/home.html')

def map_view(request):
    incidents = Incident.objects.all().order_by('-datetime')
    return render(request, 'incidents/map.html', {'incidents': incidents})

def ai_help(request):
    return render(request, 'incidents/ai_help.html')

def alerts(request):
    return render(request, 'incidents/alerts.html')

def resources(request):
    return render(request, 'incidents/resources.html')

@csrf_exempt  # Add if needed for API endpoints
@require_http_methods(["POST"])
def report_incident(request):
    try:
        data = json.loads(request.body)
        incident = Incident.objects.create(
            datetime=data['dateTime'],
            latitude=data['lat'],
            longitude=data['lng'],
            description=data['description'],
            source=data.get('source', ''),
            image_data=data.get('image', ''),
            verified=False
        )
        return JsonResponse({'status': 'success', 'id': incident.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt  # Add if needed for API endpoints
@require_http_methods(["POST"])
def subscribe(request):
    try:
        data = json.loads(request.body)
        subscriber = Subscriber.objects.create(
            name=data['name'],
            email=data['email'],
            address=data['address'],
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def get_incidents(request):
    incidents = Incident.objects.all().values(
        'id', 'datetime', 'latitude', 'longitude', 
        'description', 'source', 'image_data', 'verified'
    )
    incident_list = []
    for incident in incidents:
        incident['lat'] = incident['latitude']
        incident['lng'] = incident['longitude']
        incident['image'] = incident['image_data']  
        incident['datetime'] = incident['datetime']
        incident_list.append(incident)
    return JsonResponse(incident_list, safe=False)