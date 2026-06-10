from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from .forms import RegisterForm, LoginForm, UpdateProfileForm, ChangePasswordForm, DeleteAccountForm
from polls.models import Poll, Vote


def home_view(request):
    """Landing page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    context = {}
    return render(request, 'landing.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    show_login_button = False
    login_email = ''

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
        else:
            login_email = request.POST.get('email', '').strip()
            email_errors = form.errors.get('email', [])
            if any(RegisterForm.EMAIL_EXISTS_MESSAGE in str(error) for error in email_errors):
                show_login_button = True
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = RegisterForm()
    
    context = {
        'form': form,
        'show_login_button': show_login_button,
        'login_email': login_email,
    }
    return render(request, 'accounts/register.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    email_prefill = request.GET.get('email', '')
    if request.GET.get('inactive') == '1':
        messages.warning(request, 'You have been logged out due to inactivity.')

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Try login with username or email
        user = None
        if '@' in username_or_email:
            u = User.objects.filter(email=username_or_email, is_active=True).first()
            if u:
                user = authenticate(request, username=u.username, password=password)
        else:
            user = authenticate(request, username=username_or_email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username/email or password.')
    
    form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form, 'email': email_prefill})


@login_required
def logout_view(request):
    inactive = request.GET.get('inactive') == '1'
    logout(request)
    if inactive:
        login_url = reverse('login') + '?inactive=1'
        return redirect(login_url)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def settings_view(request):
    profile_form = UpdateProfileForm(instance=request.user)
    password_form = ChangePasswordForm()
    delete_form = DeleteAccountForm(request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            profile_form = UpdateProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('settings')
            else:
                for field, errors in profile_form.errors.items():
                    for error in errors:
                        messages.error(request, error)
        
        elif action == 'change_password':
            password_form = ChangePasswordForm(request.POST)
            if password_form.is_valid():
                old_password = password_form.cleaned_data['old_password']
                if not request.user.check_password(old_password):
                    messages.error(request, 'Current password is incorrect.')
                else:
                    new_password = password_form.cleaned_data['new_password1']
                    request.user.set_password(new_password)
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    messages.success(request, 'Password changed successfully!')
                    return redirect('settings')
    
    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'delete_form': delete_form,
    }
    return render(request, 'accounts/settings.html', context)


@login_required
def delete_account_view(request):
    """
    Permanently delete a user's account and all related data.
    """
    if request.method == 'POST':
        form = DeleteAccountForm(request.user, request.POST)
        if form.is_valid():
            user = request.user
            try:
                user_profile = user.account_profile
            except Exception:
                user_profile = None

            if user_profile and getattr(user_profile, 'profile_picture', None):
                try:
                    user_profile.profile_picture.delete(save=False)
                except Exception:
                    pass

            logout(request)
            user.delete()

            messages.success(request, 'Your account has been permanently deleted.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
            return redirect('settings')
    
    return redirect('settings')


@login_required
def privacy_settings_view(request):
    """View for managing user privacy settings"""
    from .forms import PrivacySettingsForm, UserProfileForm
    from .models import PrivacySettings, UserProfile
    from .privacy import ensure_privacy_settings
    
    # Ensure user has privacy settings initialized
    privacy_settings, created = PrivacySettings.objects.get_or_create(user=request.user)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        privacy_form = PrivacySettingsForm(request.POST, instance=privacy_settings)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        
        if privacy_form.is_valid() and profile_form.is_valid():
            privacy_form.save()
            profile_form.save()
            messages.success(request, 'Privacy settings updated successfully!')
            return redirect('privacy_settings')
    else:
        privacy_form = PrivacySettingsForm(instance=privacy_settings)
        profile_form = UserProfileForm(instance=user_profile)
    
    context = {
        'privacy_form': privacy_form,
        'profile_form': profile_form,
        'user_profile': user_profile,
    }
    return render(request, 'accounts/privacy_settings.html', context)


@login_required
def profile_view(request, username=None):
    """
    View a user's profile with privacy checks.
    Privacy-first: only show allowed information.
    """
    from .privacy import check_profile_access, check_followers_visibility, check_following_visibility
    
    if username is None:
        username = request.user.username
    
    try:
        profile_user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('home')
    
    # Handle follow/unfollow actions
    if request.method == 'POST' and request.user != profile_user:
        action = request.POST.get('action')
        from .models import Follow
        
        if action == 'follow':
            Follow.objects.get_or_create(follower=request.user, following=profile_user)
            messages.success(request, f'You are now following {profile_user.username}.')
        elif action == 'unfollow':
            Follow.objects.filter(follower=request.user, following=profile_user).delete()
            messages.success(request, f'You unfollowed {profile_user.username}.')
        
        return redirect('profile', username=username)
    
    # Check profile access permission
    if request.user != profile_user:
        if not request.can_view_profile(profile_user, request.user):
            messages.error(request, 'This profile is private.')
            return redirect('home')
    
    # Get profile information
    try:
        user_profile = profile_user.account_profile
    except:
        from .models import UserProfile
        user_profile, created = UserProfile.objects.get_or_create(user=profile_user)
    
    # Check privacy settings for various sections
    try:
        privacy = profile_user.privacy_settings
    except:
        from .models import PrivacySettings
        privacy, created = PrivacySettings.objects.get_or_create(user=profile_user)
    
    can_view_followers = request.can_view_followers(profile_user, request.user)
    can_view_following = request.can_view_following(profile_user, request.user)
    
    # Get follower and following counts (only show if allowed)
    from .models import Follow
    followers_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()
    
    # Get followers and following lists
    followers = []
    following = []
    
    if can_view_followers:
        followers = [f.follower for f in Follow.objects.filter(following=profile_user).select_related('follower')]
    
    if can_view_following:
        following = [f.following for f in Follow.objects.filter(follower=profile_user).select_related('following')]
    
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=profile_user
        ).exists()
    
    # Get poll and vote stats (only for own profile)
    polls_created = 0
    polls_participated = 0
    votes_cast = 0
    
    if request.user == profile_user:
        from polls.models import Poll, Vote
        polls_created = Poll.objects.filter(created_by=profile_user).count()
        votes_cast = Vote.objects.filter(user=profile_user).count()
        # Count unique polls participated in
        polls_participated = Vote.objects.filter(user=profile_user).values('poll').distinct().count()
    
    context = {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'privacy': privacy,
        'can_view_followers': can_view_followers,
        'can_view_following': can_view_following,
        'followers_count': followers_count if can_view_followers else None,
        'following_count': following_count if can_view_following else None,
        'followers': followers,
        'following': following,
        'is_following': is_following,
        'polls_created': polls_created,
        'polls_participated': polls_participated,
        'votes_cast': votes_cast,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def follow_user_view(request, username):
    """Follow a user (AJAX endpoint)"""
    from .models import Follow
    
    try:
        user_to_follow = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'})
    
    if user_to_follow == request.user:
        return JsonResponse({'success': False, 'message': 'You cannot follow yourself.'})
    
    follow, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
    
    if created:
        return JsonResponse({
            'success': True,
            'message': f'You are now following {user_to_follow.username}.',
            'is_following': True
        })
    else:
        return JsonResponse({'success': False, 'message': 'Already following this user.'})


@login_required
def unfollow_user_view(request, username):
    """Unfollow a user (AJAX endpoint)"""
    from .models import Follow
    
    try:
        user_to_unfollow = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'})
    
    deleted_count, _ = Follow.objects.filter(
        follower=request.user,
        following=user_to_unfollow
    ).delete()
    
    if deleted_count > 0:
        return JsonResponse({
            'success': True,
            'message': f'You unfollowed {user_to_unfollow.username}.',
            'is_following': False
        })
    else:
        return JsonResponse({'success': False, 'message': 'Not following this user.'})


@login_required
def notifications_view(request):
    """View all notifications (PRIVATE - only for current user)"""
    from .models import Notification
    
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # Mark all as read if requested
    if request.method == 'POST' and request.POST.get('action') == 'mark_all_read':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('notifications')
    
    context = {
        'notifications': notifications,
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count(),
    }
    
    return render(request, 'accounts/notifications.html', context)


@login_required
def dashboard_view(request):
    """User dashboard with personalized content (PRIVATE)"""
    from .models import Follow, Notification
    from polls.models import Poll, Vote
    
    # Get user's own data
    polls_created = Poll.objects.filter(created_by=request.user).count()
    polls_participated = Vote.objects.filter(user=request.user).values('poll').distinct().count()
    votes_cast = Vote.objects.filter(user=request.user).count()
    
    # Get users this user follows
    following_users = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    follower_count = Follow.objects.filter(following=request.user).count()
    
    # Get polls from followed users (respecting privacy)
    from accounts.models import PrivacySettings
    polls_from_following = []
    
    for followed_user_id in following_users:
        followed_user = User.objects.get(id=followed_user_id)
        try:
            privacy = followed_user.privacy_settings
            # Only show polls if poll activity is visible
            if privacy.poll_activity_visibility != 'hidden':
                user_polls = Poll.objects.filter(created_by=followed_user).order_by('-created_at')[:3]
                polls_from_following.extend(user_polls)
        except:
            pass
    
    # Get user's unread notifications
    unread_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')[:5]
    
    context = {
        'polls_created': polls_created,
        'polls_participated': polls_participated,
        'votes_cast': votes_cast,
        'follower_count': follower_count,
        'following_count': len(following_users),
        'unread_notifications': unread_notifications,
        'polls_from_following': polls_from_following[:5],
    }
    
    return render(request, 'accounts/dashboard.html', context)
