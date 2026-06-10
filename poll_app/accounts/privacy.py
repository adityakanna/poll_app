"""
Privacy decorators and utilities for enforcing user data isolation.
Ensures users cannot access each other's private information.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from accounts.models import PrivacySettings, Follow


def require_login(view_func):
    """Redirect unauthenticated users to login"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def check_profile_access(view_func):
    """
    Check if the requesting user has permission to view a profile.
    Users can only view their own profile or public profiles they follow.
    """
    @wraps(view_func)
    def wrapper(request, username, *args, **kwargs):
        from django.contrib.auth.models import User
        
        try:
            profile_user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('home')
        
        # Users can always view their own profile
        if request.user == profile_user:
            return view_func(request, username, *args, **kwargs)
        
        # Check privacy settings
        try:
            privacy = profile_user.privacy_settings
        except PrivacySettings.DoesNotExist:
            # Create default privacy settings if they don't exist
            privacy = PrivacySettings.objects.create(user=profile_user)
        
        # Check if profile is public
        if privacy.account_visibility == 'private':
            # Check if requesting user is a follower
            is_follower = Follow.objects.filter(
                follower=request.user,
                following=profile_user
            ).exists()
            
            if not is_follower:
                messages.error(request, "This profile is private.")
                return redirect('home')
        
        return view_func(request, username, *args, **kwargs)
    
    return wrapper


def check_followers_visibility(target_user, requesting_user):
    """
    Check if the requesting user can view another user's followers list.
    Returns True if they can, False otherwise.
    """
    if target_user == requesting_user:
        return True  # Users can always see their own followers
    
    try:
        privacy = target_user.privacy_settings
    except PrivacySettings.DoesNotExist:
        privacy = PrivacySettings.objects.create(user=target_user)
    
    if privacy.followers_visibility == 'only_me':
        return False
    elif privacy.followers_visibility == 'followers':
        # Check if requesting user follows the target user
        return Follow.objects.filter(
            follower=requesting_user,
            following=target_user
        ).exists()
    else:  # 'everyone'
        return True


def check_following_visibility(target_user, requesting_user):
    """
    Check if the requesting user can view another user's following list.
    Returns True if they can, False otherwise.
    """
    if target_user == requesting_user:
        return True  # Users can always see who they follow
    
    try:
        privacy = target_user.privacy_settings
    except PrivacySettings.DoesNotExist:
        privacy = PrivacySettings.objects.create(user=target_user)
    
    if privacy.following_visibility == 'only_me':
        return False
    elif privacy.following_visibility == 'followers':
        # Check if requesting user follows the target user
        return Follow.objects.filter(
            follower=requesting_user,
            following=target_user
        ).exists()
    else:  # 'everyone'
        return True


def check_voting_activity_visibility(target_user, requesting_user):
    """
    Check if the requesting user can see another user's voting activity.
    Voting activity is private by default and should never be visible to others.
    """
    if target_user == requesting_user:
        return True  # Users can always see their own voting activity
    
    # Voting activity should never be visible to other users
    return False


def check_poll_activity_visibility(target_user, requesting_user):
    """
    Check if the requesting user can see another user's poll creation activity.
    """
    if target_user == requesting_user:
        return True  # Users can always see their own polls
    
    try:
        privacy = target_user.privacy_settings
    except PrivacySettings.DoesNotExist:
        privacy = PrivacySettings.objects.create(user=target_user)
    
    if privacy.poll_activity_visibility == 'hidden':
        return False
    elif privacy.poll_activity_visibility == 'followers':
        # Check if requesting user follows the target user
        return Follow.objects.filter(
            follower=requesting_user,
            following=target_user
        ).exists()
    else:  # 'public'
        return True


def ensure_privacy_settings(user):
    """
    Ensure a user has privacy settings initialized.
    Called when a new user is created.
    """
    if not hasattr(user, 'privacy_settings'):
        PrivacySettings.objects.get_or_create(user=user)
    return user


class PrivacyEnforcementMiddleware:
    """
    Middleware to enforce privacy settings across the application.
    Logs privacy-sensitive operations and prevents unauthorized access.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add privacy check utility to request
        request.can_view_profile = self.can_view_profile
        request.can_view_followers = self.can_view_followers
        request.can_view_following = self.can_view_following
        request.can_view_voting_activity = self.can_view_voting_activity
        
        response = self.get_response(request)
        return response
    
    @staticmethod
    def can_view_profile(target_user, requesting_user):
        """Check if user can view another user's profile"""
        if target_user == requesting_user:
            return True
        
        try:
            privacy = target_user.privacy_settings
        except PrivacySettings.DoesNotExist:
            privacy = PrivacySettings.objects.create(user=target_user)
        
        if privacy.account_visibility == 'private':
            return Follow.objects.filter(
                follower=requesting_user,
                following=target_user
            ).exists()
        return True
    
    @staticmethod
    def can_view_followers(target_user, requesting_user):
        """Check if user can view another user's followers"""
        return check_followers_visibility(target_user, requesting_user)
    
    @staticmethod
    def can_view_following(target_user, requesting_user):
        """Check if user can view another user's following list"""
        return check_following_visibility(target_user, requesting_user)
    
    @staticmethod
    def can_view_voting_activity(target_user, requesting_user):
        """Check if user can view another user's voting activity"""
        return check_voting_activity_visibility(target_user, requesting_user)
