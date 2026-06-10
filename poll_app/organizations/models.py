from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from polls.models import Poll


class Organization(models.Model):
    """Organization model for organizational accounts"""
    name = models.CharField(max_length=200, unique=True)
    email = models.EmailField(unique=True)
    description = models.TextField(blank=True, null=True)
    logo = models.FileField(
        upload_to='organization_logos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def follower_count(self):
        return self.followers.count()
    
    def following_count(self):
        return self.following.count()
    
    def poll_count(self):
        return Poll.objects.filter(created_by_organization=self).count()


class Follow(models.Model):
    """Follow relationship model - can follow users or organizations"""
    FOLLOW_TYPES = [
        ('user', 'User'),
        ('organization', 'Organization'),
    ]
    
    # Who is following
    follower_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='following_users')
    follower_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='following_orgs')
    
    # Who is being followed
    following_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='followers_users')
    following_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='followers')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ['follower_user', 'following_user'],
            ['follower_user', 'following_organization'],
            ['follower_organization', 'following_user'],
            ['follower_organization', 'following_organization'],
        ]
    
    def __str__(self):
        follower = self.follower_user.username if self.follower_user else self.follower_organization.name
        following = self.following_user.username if self.following_user else self.following_organization.name
        return f"{follower} follows {following}"


class Notification(models.Model):
    """Notification model for user and organization notifications"""
    NOTIFICATION_TYPES = [
        ('follow', 'Someone followed you'),
        ('poll_created', 'Organization posted a poll'),
        ('poll_closed', 'Poll results announced'),
        ('vote_reminder', 'Reminder to vote'),
        ('poll_expiring', 'Poll expiring soon'),
    ]
    
    # Recipient
    recipient_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications_user')
    recipient_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications_org')
    
    # Sender
    sender_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications_user')
    sender_organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications_org')
    
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='follow')
    message = models.TextField()
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        recipient = self.recipient_user.username if self.recipient_user else self.recipient_organization.name
        return f"Notification for {recipient}: {self.message[:50]}"


class FeedItem(models.Model):
    """Feed item model - polls in user/organization feed"""
    # For user feed
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='feed_items')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='feed_items')
    
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='feed_items')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ['user', 'poll'],
            ['organization', 'poll'],
        ]
        ordering = ['-added_at']
    
    def __str__(self):
        recipient = self.user.username if self.user else self.organization.name
        return f"{recipient}'s feed - {self.poll.question[:50]}"


class UserProfile(models.Model):
    """Extended user profile for additional user information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True, max_length=500)
    profile_picture = models.FileField(
        upload_to='user_profiles/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"
    
    def follower_count(self):
        return Follow.objects.filter(following_user=self.user).count()
    
    def following_count(self):
        return Follow.objects.filter(follower_user=self.user).count()
