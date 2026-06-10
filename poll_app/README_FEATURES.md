# VoxPoll - Social Media Polling Platform

A comprehensive Django-based polling application with Instagram-like social features, including organizations, user follow systems, personalized feeds, and real-time notifications.

## 🎯 Features Implemented

### ✅ Dual Authentication System
- **User Accounts**: Regular user registration & login
- **Organization Accounts**: Organization registration with logo, description, verification badge
- **Role-Based Access**: Different dashboards for users vs organizations

### ✅ Follow/Unfollow System
Supports all 4 relationship types:
- User → User (follow other users)
- User → Organization (follow organizations)
- Organization → User (follow users)
- Organization → Organization (follow other orgs)

### ✅ Personalized Feeds
- Auto-distribution of polls to followers' feeds
- Real-time feed updates when organizations create polls
- Vote directly from feed
- Show poll results in feed

### ✅ Search System
- Search by username (users)
- Search by organization name
- Real-time results with suggestions
- Follow/unfollow from search results
- Suggested organizations when no query

### ✅ User Profiles
- User profile page with bio and profile picture
- Followers/following counts
- List of created polls
- Follow/unfollow button
- Edit profile functionality

### ✅ Organization Profiles
- Organization profile page with logo
- Verified badge support
- Follower/following counts
- List of created polls
- Poll statistics

### ✅ Notification System
- Follow notifications
- Poll creation notifications
- Real-time notification bell (expandable)
- Notification center page
- Mark as read functionality

### ✅ Database Structure
```
User → UserProfile (extended user info)
Organization (standalone entity)
Follow (relationships between all types)
Poll (supports both User and Organization creators)
FeedItem (polls in user feeds)
Notification (all notification types)
Vote (voting records with validation)
```

### ✅ Security Features
- Users cannot vote on their own polls
- Organizations cannot vote on their own polls
- Unique follow constraints (no duplicate follows)
- CSRF protection on all forms
- One vote per poll per user

---

## 📦 What Was Built

### New App: `organizations/`
Complete social features module with:
- Models for Organization, Follow, Notification, FeedItem, UserProfile
- Views for all social features
- Forms for registration and profile updates
- URL routing
- Signal-based automatic feed distribution
- Admin interface

### Updated Modules
- **polls/models.py**: Poll model now supports organizations, expiration dates, closed status
- **poll_app/settings.py**: Added organizations app, media file configuration
- **poll_app/urls.py**: Added organizations URLs, media file serving
- **base.html**: Added Feed, Search, Notifications to navbar
- **home.html**: Added organization login/register buttons

### 14 New Templates
All with Instagram-inspired styling:
1. `feed.html` - Personalized poll feed
2. `search.html` - User/organization search
3. `register.html` - Organization registration
4. `login.html` - Organization login
5. `user_profile.html` - User profile
6. `organization_profile.html` - Organization profile
7. `followers_list.html` - List of followers
8. `following_list.html` - List of following
9. `notifications.html` - Notification center
10. `edit_user_profile.html` - Edit profile
11-14. Additional organization management templates

---

## 🚀 Quick Start

### Prerequisites
```bash
pip install pillow  # For image uploads
```

### Setup (5 steps)
```bash
# 1. Create migrations
python manage.py makemigrations organizations
python manage.py makemigrations polls
python manage.py migrate

# 2. Create media directories
mkdir -p media/organization_logos
mkdir -p media/user_profiles

# 3. Run development server
python manage.py runserver

# 4. Create superuser (if needed)
python manage.py createsuperuser

# 5. Access the application
# User: http://localhost:8000/
# Admin: http://localhost:8000/admin/
```

### Test the Features
1. Register as user: `/register/`
2. Register as organization: `/organization/register/`
3. Create poll as organization
4. Follow organization as user: `/search/`
5. View feed: `/feed/` (should see org's poll)
6. Vote on poll from feed
7. Check notifications: `/notifications/`

---

## 📍 New URL Routes

### Authentication
```
POST /organization/register/     - Register organization
POST /organization/login/        - Login organization
GET  /organization/dashboard/    - Organization dashboard
```

### Social Features
```
GET  /feed/                      - Personalized feed
GET  /search/                    - Search page
GET  /profile/user/<id>/         - User profile
GET  /profile/edit/              - Edit your profile
GET  /profile/organization/<id>/ - Organization profile
GET  /followers/<id>/            - Followers list
GET  /following/<id>/            - Following list
GET  /notifications/             - Notification center
```

### API Endpoints (AJAX)
```
POST /follow/user/<id>/              - Follow user
POST /follow/organization/<id>/      - Follow organization
POST /unfollow/user/<id>/            - Unfollow user
POST /unfollow/organization/<id>/    - Unfollow organization
GET  /api/notifications/unread/      - Get unread count
```

---

## 🏗️ Architecture

### Models
- **Organization**: Stores organization data (name, email, logo, description, verified status)
- **UserProfile**: Extended user information (bio, profile picture, verified status)
- **Follow**: Tracks all follow relationships with flexible foreign keys
- **Notification**: Stores notifications with type classification
- **FeedItem**: Manages poll distribution to user feeds
- **Poll**: Updated to support organization creators

### Views
- **Authentication**: Organization registration, login, session management
- **Follow**: Follow/unfollow endpoints with automatic feed population
- **Feed**: Personalized feed showing followed organizations' polls
- **Search**: Search users and organizations with suggestions
- **Profiles**: User and organization profile pages
- **Notifications**: Notification display and management

### Signals
- **Auto UserProfile creation**: Created when User is created
- **Auto Feed Distribution**: When organization creates poll, distributed to all followers

---

## 💡 Key Implementation Details

### Follow System
```python
Follow.objects.create(
    follower_user=user,
    following_organization=org
)
# Automatically:
# 1. Creates notification
# 2. Adds org's active polls to user's feed
```

### Feed Distribution
```python
@receiver(post_save, sender=Poll)
def distribute_poll_to_feed(sender, instance, created, **kwargs):
    # When org creates poll:
    # 1. Find all followers of org
    # 2. Create FeedItem for each follower
    # 3. Create notification for each follower
```

### Vote Validation
```python
class Vote:
    def clean(self):
        if self.poll.created_by == self.user:
            raise ValidationError("Cannot vote on own poll")
```

---

## 📊 Data Flow Examples

### When User Follows Organization
```
User clicks Follow
    ↓
POST /follow/organization/<id>/
    ↓
Follow record created
    ↓
Notification sent to organization
    ↓
All active org polls added to user's feed
    ↓
User sees polls in /feed/
```

### When Organization Creates Poll
```
Organization creates poll
    ↓
Poll.post_save signal triggered
    ↓
Find all followers of organization
    ↓
For each follower:
    - Create FeedItem (poll in their feed)
    - Create Notification ("Org posted new poll")
    ↓
Followers see poll in /feed/
Followers receive notification
```

---

## 🎨 UI Features

- **Instagram-Inspired Design**: Modern dark mode with accent colors
- **Responsive Layout**: Works on desktop, tablet, mobile
- **Smooth Transitions**: Hover effects, animations
- **Loading States**: User feedback for all actions
- **Error Handling**: Graceful error messages
- **Avatar System**: Profile pictures and organization logos

---

## 🔐 Security Features

1. **Authentication**: Session-based with CSRF tokens
2. **Authorization**: Role-based access control
3. **Data Validation**: Form and model-level validation
4. **Vote Integrity**: Unique constraints, self-voting prevention
5. **Follow Constraints**: No duplicate follows, no self-follows

---

## 📚 Documentation Files

1. **QUICK_START.md** - Get started in 5 steps
2. **IMPLEMENTATION_GUIDE.md** - Detailed implementation docs
3. **This file** - Feature overview and architecture

---

## 🛠️ Tech Stack

- **Backend**: Django 3.2+
- **Database**: SQLite (development), can use PostgreSQL
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Images**: Pillow for image processing
- **Authentication**: Django built-in

---

## 📈 Future Enhancements

### Short-term
- Real-time notifications with Django Channels
- Advanced search filters
- User blocking/muting
- Poll comments and discussion

### Medium-term
- Trending algorithms
- Analytics dashboard for organizations
- Email notifications
- Account verification system

### Long-term
- REST API for mobile apps
- Mobile applications (iOS/Android)
- Community moderation tools
- Advanced polling features

---

## 🤝 Contributing

To extend this platform:

1. **Add new notification types**: Update Notification model choices
2. **Create new API endpoints**: Add to organizations/views.py and urls.py
3. **Custom feed algorithms**: Modify feed_view in views.py
4. **Advanced search**: Enhance search_view in views.py

---

## 📝 License

This project is part of the VoxPoll application suite.

---

## 🎉 Summary

The VoxPoll platform now features:
- ✅ Dual authentication (Users & Organizations)
- ✅ Complete follow system
- ✅ Personalized feeds with auto-distribution
- ✅ Powerful search functionality
- ✅ User and organization profiles
- ✅ Real-time notifications
- ✅ Modern Instagram-like UI
- ✅ Secure and validated system

**Ready to launch!** 🚀

See QUICK_START.md to get started immediately.
