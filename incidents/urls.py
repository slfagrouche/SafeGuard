# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.handle_chat, name='chat'),
    path('chat/history/', views.get_chat_history, name='chat_history'),
    path('', views.home, name='home'),
    path('map/', views.map_view, name='map'),
    path('ai-help/', views.ai_help, name='ai_help'),
    path('alerts/', views.alerts, name='alerts'),
    path('resources/', views.resources, name='resources'),
    path('api/incidents/', views.get_incidents, name='get_incidents'),
    path('report/', views.report_incident, name='report_incident'),
    path('subscribe/', views.subscribe, name='subscribe'),  # Added missing subscribe URL
]
