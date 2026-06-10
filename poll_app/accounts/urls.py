from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('settings/', views.settings_view, name='settings'),
    path('privacy/', views.privacy_settings_view, name='privacy_settings'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('profile/', views.profile_view, name='my_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('follow/<str:username>/', views.follow_user_view, name='follow_user'),
    path('unfollow/<str:username>/', views.unfollow_user_view, name='unfollow_user'),
    path('delete-account/', views.delete_account_view, name='delete_account'),
]
