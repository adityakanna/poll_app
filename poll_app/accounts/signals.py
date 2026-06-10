"""
Django signals for accounts app.
Automatically initialize privacy settings and user profiles for new users.
Handle notifications for user activities.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from accounts.models import PrivacySettings, UserProfile, Follow, Notification


@receiver(post_save, sender=User)
def create_privacy_settings(sender, instance, created, **kwargs):
    """
    Create privacy settings when a new user is created.
    This ensures every user has default privacy settings initialized.
    """
    if created:
        PrivacySettings.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create user profile when a new user is created.
    This provides a place for bio and profile picture storage.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Follow)
def notify_follow(sender, instance, created, **kwargs):
    """
    Send notification when a user is followed (respects privacy settings).
    Only sent if the user has enabled follower notifications.
    """
    if created:
        Notification.create_notification(
            recipient=instance.following,
            notification_type='follow',
            title=f'{instance.follower.username} followed you',
            message=f'{instance.follower.username} is now following you.',
            sender=instance.follower
        )
