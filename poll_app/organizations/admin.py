from django.contrib import admin
from .models import Organization, Follow, Notification, FeedItem, UserProfile


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'verified', 'created_at']
    search_fields = ['name', 'email']
    list_filter = ['verified', 'created_at']


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'created_at']
    search_fields = ['follower_user__username', 'following_user__username', 'follower_organization__name', 'following_organization__name']
    list_filter = ['created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'notification_type', 'read', 'created_at']
    search_fields = ['message', 'recipient_user__username', 'recipient_organization__name']
    list_filter = ['notification_type', 'read', 'created_at']


@admin.register(FeedItem)
class FeedItemAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'added_at']
    search_fields = ['user__username', 'organization__name', 'poll__question']
    list_filter = ['added_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'verified', 'created_at']
    search_fields = ['user__username']
    list_filter = ['verified', 'created_at']
