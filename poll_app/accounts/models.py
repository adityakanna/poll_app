from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile with privacy settings and personal information"""
    VISIBILITY_CHOICES = [
        ('public', 'Public - Everyone can see'),
        ('private', 'Private - Only me'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account_profile')
    bio = models.TextField(max_length=500, blank=True, default='')
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_deleted = models.BooleanField(default=False, help_text='Account has been deleted by user')
    deleted_at = models.DateTimeField(null=True, blank=True, help_text='When the account was deleted')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.is_deleted:
            return f"Profile of [Deleted User]"
        return f"Profile of {self.user.username}"


class PrivacySettings(models.Model):
    """
    Privacy settings for each user.
    Controls what information is visible to other users.
    """
    ACCOUNT_VISIBILITY = [
        ('public', 'Public Account - Everyone can find you'),
        ('private', 'Private Account - Only followers can see content'),
    ]
    
    FOLLOWERS_VISIBILITY = [
        ('only_me', 'Only Me'),
        ('followers', 'Followers Only'),
        ('everyone', 'Everyone'),
    ]
    
    FOLLOWING_VISIBILITY = [
        ('only_me', 'Only Me'),
        ('followers', 'Followers Only'),
        ('everyone', 'Everyone'),
    ]
    
    ACTIVITY_VISIBILITY = [
        ('hidden', 'Hidden From Everyone (Recommended)'),
        ('followers', 'Followers Only'),
        ('public', 'Everyone'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='privacy_settings')
    
    # Account visibility
    account_visibility = models.CharField(
        max_length=20, 
        choices=ACCOUNT_VISIBILITY, 
        default='public',
        help_text='Controls if your account can be found by other users'
    )
    
    # Followers/Following visibility
    followers_visibility = models.CharField(
        max_length=20, 
        choices=FOLLOWERS_VISIBILITY, 
        default='only_me',
        help_text='Who can see your followers list'
    )
    
    following_visibility = models.CharField(
        max_length=20, 
        choices=FOLLOWING_VISIBILITY, 
        default='only_me',
        help_text='Who can see who you are following'
    )
    
    # Activity visibility
    voting_activity_visibility = models.CharField(
        max_length=20, 
        choices=ACTIVITY_VISIBILITY, 
        default='hidden',
        help_text='Who can see your voting activity'
    )
    
    poll_activity_visibility = models.CharField(
        max_length=20, 
        choices=ACTIVITY_VISIBILITY, 
        default='hidden',
        help_text='Who can see your poll creation activity'
    )
    
    # Notification settings
    show_follower_notifications = models.BooleanField(default=True)
    show_poll_notifications = models.BooleanField(default=True)
    show_activity_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Privacy Settings'
        verbose_name_plural = 'Privacy Settings'
    
    def __str__(self):
        return f"Privacy Settings for {self.user.username}"


class Follow(models.Model):
    """
    Model for tracking follow relationships.
    Follows are private by default - followers/following lists are private.
    """
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower', '-created_at']),
            models.Index(fields=['following', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
    
    def clean(self):
        """Users cannot follow themselves"""
        if self.follower == self.following:
            from django.core.exceptions import ValidationError
            raise ValidationError("You cannot follow yourself.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Notification(models.Model):
    """
    Model for user notifications - PRIVATE by default.
    Only the recipient can see their own notifications.
    """
    NOTIFICATION_TYPES = [
        ('follow', 'New Follower'),
        ('poll_vote', 'Poll Vote'),
        ('poll_update', 'Poll Update'),
        ('account', 'Account Activity'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"
    
    @staticmethod
    def create_notification(recipient, notification_type, title, message, sender=None):
        """
        Create a notification with privacy settings check.
        Only creates notification if user has enabled that type.
        """
        try:
            privacy = recipient.privacy_settings
        except PrivacySettings.DoesNotExist:
            privacy = PrivacySettings.objects.create(user=recipient)
        
        # Check if user wants this notification type
        if notification_type == 'follow' and not privacy.show_follower_notifications:
            return None
        elif notification_type in ['poll_vote', 'poll_update'] and not privacy.show_poll_notifications:
            return None
        elif notification_type == 'account' and not privacy.show_activity_notifications:
            return None
        
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            sender=sender
        )
        return notification
