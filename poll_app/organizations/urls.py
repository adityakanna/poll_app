from django.urls import path
from . import views

urlpatterns = [
    # Organization Authentication
    path('organization/register/', views.organization_register, name='organization_register'),
    path('organization/login/', views.organization_login, name='organization_login'),
    path('organization/dashboard/', views.organization_dashboard, name='organization_dashboard'),
    
    # Follow System
    path('follow/user/<int:user_id>/', views.follow_user, name='follow_user'),
    path('follow/organization/<int:org_id>/', views.follow_organization, name='follow_organization'),
    path('unfollow/user/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    path('unfollow/organization/<int:org_id>/', views.unfollow_organization, name='unfollow_organization'),
    
    # Feed
    path('feed/', views.feed_view, name='feed'),
    
    # Search
    path('search/', views.search_view, name='search'),
    
    # Profiles
    path('profile/user/<int:user_id>/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_user_profile, name='edit_user_profile'),
    path('profile/organization/<int:org_id>/', views.organization_profile, name='organization_profile'),
    
    # Followers/Following
    path('followers/<int:user_id>/', views.followers_list, name='followers_list'),
    path('following/<int:user_id>/', views.following_list, name='following_list'),
    
    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('api/notifications/unread/', views.get_unread_notifications, name='get_unread_notifications'),
]
