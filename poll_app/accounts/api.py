"""
API endpoints for VoxPoll with privacy-first design.
All endpoints respect user privacy settings and data isolation.
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.db.models import Count
from accounts.models import Follow, Notification, PrivacySettings
from polls.models import Poll, Vote


@login_required
@require_http_methods(["GET"])
def api_user_profile(request, username):
    """
    Get user profile information respecting privacy settings.
    Only returns publicly available information or information the requesting user is allowed to see.
    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    # Check if requesting user can view this profile
    if request.user != user:
        if not request.can_view_profile(user, request.user):
            return JsonResponse({'error': 'This profile is private'}, status=403)
    
    try:
        profile = user.account_profile
    except:
        profile = None
    
    try:
        privacy = user.privacy_settings
    except:
        privacy = PrivacySettings.objects.create(user=user)
    
    # Build response with only allowed information
    response_data = {
        'username': user.username,
        'email': user.email if request.user == user else None,
        'bio': profile.bio if profile else None,
        'account_visibility': privacy.account_visibility,
        'is_self': request.user == user,
    }
    
    # Only include follower/following counts if allowed
    if request.user == user or privacy.followers_visibility != 'only_me':
        response_data['followers_count'] = Follow.objects.filter(following=user).count()
    
    if request.user == user or privacy.following_visibility != 'only_me':
        response_data['following_count'] = Follow.objects.filter(follower=user).count()
    
    return JsonResponse(response_data)


@login_required
@require_http_methods(["GET"])
def api_user_followers(request, username):
    """
    Get a user's followers list (respects privacy settings).
    Returns empty list if followers are private.
    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    # Check privacy settings
    if request.user != user:
        if not request.can_view_followers(user, request.user):
            return JsonResponse({'error': 'This information is private'}, status=403)
    
    followers = Follow.objects.filter(following=user).select_related('follower').values_list('follower__username', flat=True)
    
    return JsonResponse({
        'username': user.username,
        'followers': list(followers),
        'count': len(followers),
    })


@login_required
@require_http_methods(["GET"])
def api_user_following(request, username):
    """
    Get a user's following list (respects privacy settings).
    Returns empty list if following is private.
    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    # Check privacy settings
    if request.user != user:
        if not request.can_view_following(user, request.user):
            return JsonResponse({'error': 'This information is private'}, status=403)
    
    following = Follow.objects.filter(follower=user).select_related('following').values_list('following__username', flat=True)
    
    return JsonResponse({
        'username': user.username,
        'following': list(following),
        'count': len(following),
    })


@login_required
@require_http_methods(["GET"])
def api_my_notifications(request):
    """
    Get current user's notifications (PRIVATE - only accessible to authenticated user).
    Respects user's notification preferences.
    """
    notifications = Notification.objects.filter(recipient=request.user).values(
        'id', 'notification_type', 'title', 'message', 'is_read', 'created_at'
    ).order_by('-created_at')[:20]
    
    unread_count = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    return JsonResponse({
        'notifications': list(notifications),
        'unread_count': unread_count,
    })


@login_required
@require_http_methods(["POST"])
def api_mark_notification_read(request, notification_id):
    """
    Mark a notification as read (PRIVATE - only for notification owner).
    """
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Notification not found'}, status=404)
    
    notification.is_read = True
    notification.save()
    
    return JsonResponse({'success': True, 'message': 'Notification marked as read'})


@login_required
@require_http_methods(["GET"])
def api_poll_results(request, poll_id):
    """
    Get poll results (anonymous statistics only).
    Poll creators can see more detailed stats, but never individual voter information.
    """
    try:
        poll = Poll.objects.get(id=poll_id)
    except Poll.DoesNotExist:
        return JsonResponse({'error': 'Poll not found'}, status=404)
    
    # Get vote statistics (aggregated, anonymous data)
    results = []
    total_votes = poll.votes.count()
    
    for option in poll.options.all():
        vote_count = Vote.objects.filter(option=option).count()
        percentage = round((vote_count / total_votes * 100), 1) if total_votes > 0 else 0
        
        results.append({
            'id': option.id,
            'text': option.option_text,
            'votes': vote_count,
            'percentage': percentage,
        })
    
    # Check if requesting user created this poll
    is_creator = request.user == poll.created_by
    
    response_data = {
        'poll_id': poll.id,
        'question': poll.question,
        'total_votes': total_votes,
        'results': results,
        'is_creator': is_creator,
    }
    
    # Only poll creators can see detailed analytics
    if is_creator:
        response_data['analytics'] = {
            'created_at': poll.created_at.isoformat(),
            'is_closed': poll.is_closed,
            'expires_at': poll.expires_at.isoformat() if poll.expires_at else None,
        }
    
    return JsonResponse(response_data)


@login_required
@require_http_methods(["GET"])
def api_my_votes(request):
    """
    Get current user's voting history (PRIVATE - only accessible to self).
    This endpoint is completely private - other users can NEVER access this data.
    """
    votes = Vote.objects.filter(user=request.user).select_related('poll', 'option').values(
        'poll_id', 'poll__question', 'option__option_text', 'voted_at'
    ).order_by('-voted_at')
    
    return JsonResponse({
        'votes': list(votes),
        'count': len(votes),
        'privacy_note': 'This voting history is completely private and only visible to you',
    })


@login_required
@require_http_methods(["GET"])
def api_my_polls(request):
    """
    Get current user's polls (own data only).
    """
    polls = Poll.objects.filter(created_by=request.user).annotate(
        vote_count=Count('votes')
    ).values(
        'id', 'question', 'description', 'created_at', 'is_closed', 'vote_count'
    ).order_by('-created_at')
    
    return JsonResponse({
        'polls': list(polls),
        'count': len(polls),
    })


@login_required
@require_http_methods(["GET"])
def api_privacy_settings(request):
    """
    Get current user's privacy settings (only for authenticated user viewing their own settings).
    """
    try:
        privacy = request.user.privacy_settings
    except:
        privacy = PrivacySettings.objects.create(user=request.user)
    
    return JsonResponse({
        'account_visibility': privacy.account_visibility,
        'followers_visibility': privacy.followers_visibility,
        'following_visibility': privacy.following_visibility,
        'voting_activity_visibility': privacy.voting_activity_visibility,
        'poll_activity_visibility': privacy.poll_activity_visibility,
        'notifications': {
            'followers': privacy.show_follower_notifications,
            'polls': privacy.show_poll_notifications,
            'activities': privacy.show_activity_notifications,
        }
    })


@login_required
@require_http_methods(["GET"])
def api_check_privacy_access(request, username, resource_type):
    """
    Check if requesting user can access a specific resource of another user.
    Useful for frontend to show/hide UI elements based on privacy.
    """
    try:
        target_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    if request.user == target_user:
        # Users can always access their own data
        return JsonResponse({
            'can_access': True,
            'resource_type': resource_type,
            'is_self': True,
        })
    
    # Check specific resource types
    can_access = False
    
    if resource_type == 'followers':
        can_access = request.can_view_followers(target_user, request.user)
    elif resource_type == 'following':
        can_access = request.can_view_following(target_user, request.user)
    elif resource_type == 'voting_activity':
        can_access = request.can_view_voting_activity(target_user, request.user)
    elif resource_type == 'profile':
        can_access = request.can_view_profile(target_user, request.user)
    
    return JsonResponse({
        'can_access': can_access,
        'resource_type': resource_type,
        'is_self': False,
    })
