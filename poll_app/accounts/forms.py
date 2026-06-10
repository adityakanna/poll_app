from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from accounts.models import PrivacySettings, UserProfile


class RegisterForm(UserCreationForm):
    EMAIL_EXISTS_MESSAGE = "An account already exists with this email. Please log in."

    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Choose a username'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Create a password'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm your password'
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Allow email reuse if the account with that email is deleted
        active_users = User.objects.filter(email=email, is_active=True)
        if active_users.exists():
            raise forms.ValidationError(self.EMAIL_EXISTS_MESSAGE)
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Allow username reuse if the account is deleted/inactive
        active_users = User.objects.filter(username=username, is_active=True)
        if active_users.exists():
            raise forms.ValidationError("This username is already taken.")
        return username


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username or Email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))


class UpdateProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user_id = self.instance.id
        # Allow email reuse if the account with that email is deleted/inactive
        active_users = User.objects.filter(email=email, is_active=True).exclude(id=user_id)
        if active_users.exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        user_id = self.instance.id
        # Allow username reuse if the account is deleted/inactive
        active_users = User.objects.filter(username=username, is_active=True).exclude(id=user_id)
        if active_users.exists():
            raise forms.ValidationError("This username is already taken.")
        return username


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Current password'
    }))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'New password'
    }))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm new password'
    }))

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("New passwords do not match.")
        return cleaned_data


class DeleteAccountForm(forms.Form):
    """Form for secure account deletion with password confirmation"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password to confirm deletion'
        }),
        label='Password Confirmation',
        help_text='Enter your password to confirm account deletion'
    )
    confirm_deletion = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='I understand this will permanently delete my account and all data',
        error_messages={'required': 'You must confirm to delete your account'}
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and not self.user.check_password(password):
            raise forms.ValidationError("The password you entered is incorrect.")
        return password


class PrivacySettingsForm(forms.ModelForm):
    """Form for managing user privacy settings"""
    
    class Meta:
        model = PrivacySettings
        fields = [
            'account_visibility',
            'followers_visibility',
            'following_visibility',
            'voting_activity_visibility',
            'poll_activity_visibility',
            'show_follower_notifications',
            'show_poll_notifications',
            'show_activity_notifications',
        ]
        
        widgets = {
            'account_visibility': forms.RadioSelect(choices=PrivacySettings.ACCOUNT_VISIBILITY),
            'followers_visibility': forms.Select(attrs={'class': 'form-control'}),
            'following_visibility': forms.Select(attrs={'class': 'form-control'}),
            'voting_activity_visibility': forms.Select(attrs={'class': 'form-control'}),
            'poll_activity_visibility': forms.Select(attrs={'class': 'form-control'}),
            'show_follower_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_poll_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_activity_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        labels = {
            'account_visibility': 'Account Visibility',
            'followers_visibility': 'Who can see your followers?',
            'following_visibility': 'Who can see who you follow?',
            'voting_activity_visibility': 'Voting Activity Visibility',
            'poll_activity_visibility': 'Poll Creation Activity Visibility',
            'show_follower_notifications': 'Get notified when someone follows you',
            'show_poll_notifications': 'Get notified about poll activities',
            'show_activity_notifications': 'Get notified about account activities',
        }


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information"""
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture']
        
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Tell us about yourself...',
                'class': 'form-control'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        
        labels = {
            'bio': 'Bio',
            'profile_picture': 'Profile Picture',
        }
