from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, FeedItem, Notification
from polls.models import Poll, Vote


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=Poll)
def distribute_poll_to_feed(sender, instance, created, **kwargs):
    """Distribute poll to followers' feeds when created by organization"""
    if created and instance.created_by_organization:
        from .models import Follow
        # Get all followers of the organization
        followers = Follow.objects.filter(following_organization=instance.created_by_organization)
        
        for follow in followers:
            # Add poll to follower's feed
            FeedItem.objects.create(
                user=follow.follower_user,
                poll=instance
            )
            
            # Create notification
            Notification.objects.create(
                recipient_user=follow.follower_user,
                sender_organization=instance.created_by_organization,
                notification_type='poll_created',
                message=f"{instance.created_by_organization.name} posted a new poll.",
                poll=instance
            )


@receiver(post_save, sender=Vote)
def check_poll_closed(sender, instance, created, **kwargs):
    """Check if poll should be closed after vote"""
    # TODO: Implement logic to close poll if all followers have voted
    pass
