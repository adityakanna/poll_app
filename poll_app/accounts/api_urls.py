"""
API URL patterns for privacy-first endpoints.
All APIs respect user data isolation and privacy settings.
"""

from django.urls import path
from . import api

urlpatterns = [
    # User profile APIs
    path('api/profile/<str:username>/', api.api_user_profile, name='api_profile'),
    path('api/followers/<str:username>/', api.api_user_followers, name='api_followers'),
    path('api/following/<str:username>/', api.api_user_following, name='api_following'),
    path('api/check-access/<str:username>/<str:resource_type>/', api.api_check_privacy_access, name='api_check_access'),
    
    # Current user private APIs
    path('api/me/notifications/', api.api_my_notifications, name='api_my_notifications'),
    path('api/me/notifications/<int:notification_id>/read/', api.api_mark_notification_read, name='api_mark_notification_read'),
    path('api/me/votes/', api.api_my_votes, name='api_my_votes'),
    path('api/me/polls/', api.api_my_polls, name='api_my_polls'),
    path('api/me/privacy/', api.api_privacy_settings, name='api_privacy_settings'),
    
    # Poll APIs
    path('api/poll/<int:poll_id>/results/', api.api_poll_results, name='api_poll_results'),
]
