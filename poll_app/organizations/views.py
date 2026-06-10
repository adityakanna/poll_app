from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from polls.models import Poll, Vote
from .models import Organization, Follow, Notification, FeedItem, UserProfile
from .forms import OrganizationRegisterForm, OrganizationUpdateForm, UserProfileForm
import json


# ============ ORGANIZATION AUTHENTICATION VIEWS ============

def organization_register(request):
    """Register a new organization"""
    if request.method == 'POST':
        form = OrganizationRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create organization
                org = form.save(commit=False)
                org.save()
                
                # Create a system user for the organization
                org_user = User.objects.create_user(
                    username=f"org_{org.id}_{org.name.lower().replace(' ', '_')}",
                    email=org.email,
                    password=form.cleaned_data['password'],
                    first_name=org.name
                )
                org_user.save()
                
                # Link user to organization for authentication
                messages.success(request, 'Organization registered successfully! You can now login.')
                return redirect('organization_login')
            except Exception as e:
                messages.error(request, f'Error creating organization: {str(e)}')
                org.delete()
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = OrganizationRegisterForm()
    
    return render(request, 'organizations/register.html', {'form': form})


def organization_login(request):
    """Login as organization"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        # Find organization by email
        try:
            org = Organization.objects.get(email=email)
            # Try to authenticate with org's system user
            org_user = User.objects.get(email=email)
            user = authenticate(request, username=org_user.username, password=password)
            
            if user is not None:
                login(request, user)
                request.session['is_organization'] = True
                request.session['organization_id'] = org.id
                messages.success(request, f'Welcome back, {org.name}!')
                return redirect('organization_dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        except Organization.DoesNotExist:
            messages.error(request, 'Organization not found.')
    
    return render(request, 'organizations/login.html')


# ============ FOLLOW/UNFOLLOW SYSTEM ============

@login_required
@require_http_methods(["POST"])
def follow_user(request, user_id):
    """Follow a user"""
    try:
        target_user = User.objects.get(id=user_id)
        
        # Prevent self-follow
        if request.user == target_user:
            return JsonResponse({'error': 'Cannot follow yourself'}, status=400)
        
        # Check if already following
        existing = Follow.objects.filter(follower_user=request.user, following_user=target_user).first()
        
        if existing:
            existing.delete()
            return JsonResponse({'status': 'unfollowed'})
        else:
            Follow.objects.create(follower_user=request.user, following_user=target_user)
            
            # Create notification
            Notification.objects.create(
                recipient_user=target_user,
                sender_user=request.user,
                notification_type='follow',
                message=f"{request.user.username} followed you."
            )
            
            return JsonResponse({'status': 'followed'})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def follow_organization(request, org_id):
    """Follow an organization"""
    try:
        org = Organization.objects.get(id=org_id)
        
        # Check if already following
        existing = Follow.objects.filter(follower_user=request.user, following_organization=org).first()
        
        if existing:
            existing.delete()
            return JsonResponse({'status': 'unfollowed'})
        else:
            Follow.objects.create(follower_user=request.user, following_organization=org)
            
            # Create notification
            Notification.objects.create(
                recipient_organization=org,
                sender_user=request.user,
                notification_type='follow',
                message=f"{request.user.username} followed you."
            )
            
            # Add all active polls from this organization to user's feed
            polls = Poll.objects.filter(created_by_organization=org, is_closed=False)
            for poll in polls:
                FeedItem.objects.get_or_create(user=request.user, poll=poll)
            
            return JsonResponse({'status': 'followed'})
    except Organization.DoesNotExist:
        return JsonResponse({'error': 'Organization not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def unfollow_user(request, user_id):
    """Unfollow a user"""
    try:
        target_user = User.objects.get(id=user_id)
        Follow.objects.filter(follower_user=request.user, following_user=target_user).delete()
        return JsonResponse({'status': 'unfollowed'})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def unfollow_organization(request, org_id):
    """Unfollow an organization"""
    try:
        org = Organization.objects.get(id=org_id)
        Follow.objects.filter(follower_user=request.user, following_organization=org).delete()
        return JsonResponse({'status': 'unfollowed'})
    except Organization.DoesNotExist:
        return JsonResponse({'error': 'Organization not found'}, status=404)


# ============ FEED VIEWS ============

@login_required
def feed_view(request):
    """Personalized feed for logged-in users"""
    # Get all feed items for the user
    feed_items = FeedItem.objects.filter(user=request.user).select_related('poll', 'poll__created_by', 'poll__created_by_organization').prefetch_related('poll__options', 'poll__votes')
    
    # Get user's votes to show voting status
    user_votes = Vote.objects.filter(user=request.user).values_list('poll_id', flat=True)
    
    context = {
        'feed_items': feed_items,
        'user_votes': user_votes,
        'total_following': Follow.objects.filter(follower_user=request.user).count(),
    }
    
    return render(request, 'organizations/feed.html', context)


# ============ SEARCH VIEWS ============

@login_required
def search_view(request):
    """Search for users and organizations"""
    query = request.GET.get('q', '').strip()
    
    users = []
    organizations = []
    suggested_orgs = []
    
    if query:
        # Search users
        users = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:10]
        
        # Search organizations
        organizations = Organization.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:10]
    else:
        # Show suggested organizations
        suggested_orgs = Organization.objects.exclude(
            followers__follower_user=request.user
        ).annotate(follower_count=Count('followers')).order_by('-follower_count')[:5]
    
    # Get user's following list
    user_following_orgs = Follow.objects.filter(follower_user=request.user, following_organization__isnull=False).values_list('following_organization_id', flat=True)
    user_following_users = Follow.objects.filter(follower_user=request.user, following_user__isnull=False).values_list('following_user_id', flat=True)
    
    context = {
        'query': query,
        'users': users,
        'organizations': organizations,
        'suggested_orgs': suggested_orgs,
        'user_following_orgs': user_following_orgs,
        'user_following_users': user_following_users,
    }
    
    return render(request, 'organizations/search.html', context)


# ============ PROFILE VIEWS ============

@login_required
def user_profile(request, user_id):
    """View user profile"""
    user = get_object_or_404(User, id=user_id)
    profile = UserProfile.objects.get_or_create(user=user)[0]
    
    # Get user's polls
    user_polls = Poll.objects.filter(created_by=user)
    
    # Get follow status
    is_following = Follow.objects.filter(follower_user=request.user, following_user=user).exists()
    
    # Get follower/following counts
    follower_count = Follow.objects.filter(following_user=user).count()
    following_count = Follow.objects.filter(follower_user=user).count()
    
    context = {
        'profile_user': user,
        'user_profile': profile,
        'user_polls': user_polls,
        'is_following': is_following,
        'follower_count': follower_count,
        'following_count': following_count,
        'can_edit': request.user == user,
    }
    
    return render(request, 'organizations/user_profile.html', context)


@login_required
def edit_user_profile(request):
    """Edit user profile"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_profile', user_id=request.user.id)
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'organizations/edit_user_profile.html', {'form': form})


def organization_profile(request, org_id):
    """View organization profile"""
    org = get_object_or_404(Organization, id=org_id)
    
    # Get organization's polls
    org_polls = Poll.objects.filter(created_by_organization=org)
    
    # Get follow status
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower_user=request.user, following_organization=org).exists()
    
    # Get follower/following counts
    follower_count = Follow.objects.filter(following_organization=org).count()
    following_count = Follow.objects.filter(follower_organization=org).count()
    
    context = {
        'organization': org,
        'org_polls': org_polls,
        'is_following': is_following,
        'follower_count': follower_count,
        'following_count': following_count,
        'can_edit': False,  # TODO: Implement org edit permissions
    }
    
    return render(request, 'organizations/organization_profile.html', context)


@login_required
def followers_list(request, user_id):
    """View user's followers"""
    user = get_object_or_404(User, id=user_id)
    followers = Follow.objects.filter(following_user=user).select_related('follower_user')
    
    context = {
        'profile_user': user,
        'followers': followers,
        'follower_count': followers.count(),
    }
    
    return render(request, 'organizations/followers_list.html', context)


@login_required
def following_list(request, user_id):
    """View user's following"""
    user = get_object_or_404(User, id=user_id)
    following = Follow.objects.filter(follower_user=user).select_related('following_user', 'following_organization')
    
    context = {
        'profile_user': user,
        'following': following,
        'following_count': following.count(),
    }
    
    return render(request, 'organizations/following_list.html', context)


# ============ NOTIFICATION VIEWS ============

@login_required
def notifications_view(request):
    """View user notifications"""
    notifications = Notification.objects.filter(recipient_user=request.user).order_by('-created_at')
    
    # Mark as read
    unread = notifications.filter(read=False)
    unread.update(read=True)
    
    context = {
        'notifications': notifications,
        'unread_count': unread.count(),
    }
    
    return render(request, 'organizations/notifications.html', context)


@login_required
def get_unread_notifications(request):
    """Get unread notifications count (for AJAX)"""
    unread_count = Notification.objects.filter(recipient_user=request.user, read=False).count()
    return JsonResponse({'unread_count': unread_count})


# ============ ORGANIZATION DASHBOARD ============

@login_required
def organization_dashboard(request):
    """Organization dashboard"""
    # Check if user is an organization
    if 'organization_id' not in request.session:
        messages.error(request, 'You must login as an organization.')
        return redirect('organization_login')
    
    org = get_object_or_404(Organization, id=request.session['organization_id'])
    
    # Get organization's polls
    polls = Poll.objects.filter(created_by_organization=org)
    
    # Get organization's followers
    followers = Follow.objects.filter(following_organization=org)
    
    context = {
        'organization': org,
        'polls': polls,
        'followers': followers,
        'follower_count': followers.count(),
    }
    
    return render(request, 'organizations/org_dashboard.html', context)
