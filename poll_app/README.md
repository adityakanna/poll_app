# VoxPoll — Django Poll & Voting Application

A full-featured production-ready Poll/Voting web app built with Django, Bootstrap 5, and vanilla JavaScript.

---

## Features

- **Authentication** — Register, Login, Logout with username or email
- **Poll CRUD** — Create, edit, delete polls (2–10 options each)
- **Smart Voting** — Radio-button single-choice; change vote without inflating count
- **Live Results** — Auto-refresh every 3 seconds via Fetch API
- **My Polls** — Manage your own polls with vote stats
- **Settings** — Update profile, change password, delete account
- **Responsive UI** — Dark theme, Bootstrap 5, mobile-friendly

---

## Project Structure

```
poll_app/
├── accounts/           # Auth app: register, login, logout, settings
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── polls/              # Core polls app
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
├── templates/
│   ├── base.html
│   ├── accounts/
│   │   ├── login.html
│   │   ├── register.html
│   │   └── settings.html
│   └── polls/
│       ├── dashboard.html
│       ├── poll_list.html
│       ├── create_poll.html
│       ├── edit_poll.html
│       ├── vote.html
│       ├── results.html
│       └── my_polls.html
├── poll_app/           # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
└── README.md
```

---

## Quick Setup

### 1. Create & Activate Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install django
```

### 3. Apply Migrations

```bash
python manage.py migrate
```

### 4. Create Superuser (optional)

```bash
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** in your browser.

---

## URL Routes

| URL | View | Description |
|-----|------|-------------|
| `/` | login_view | Redirects to login |
| `/register/` | register_view | User registration |
| `/login/` | login_view | User login |
| `/logout/` | logout_view | Logout |
| `/settings/` | settings_view | Account settings |
| `/delete-account/` | delete_account_view | Delete account |
| `/dashboard/` | dashboard_view | Home dashboard |
| `/polls/` | poll_list_view | All polls |
| `/polls/create/` | create_poll_view | Create a poll |
| `/polls/my/` | my_polls_view | User's polls |
| `/polls/edit/<id>/` | edit_poll_view | Edit poll |
| `/polls/delete/<id>/` | delete_poll_view | Delete poll |
| `/vote/<id>/` | vote_view | Cast/change vote |
| `/results/<id>/` | results_view | Live results |
| `/api/results/<id>/` | api_results_view | JSON results API |

---

## Database Models

### Poll
```python
question      CharField(max_length=500)
created_by    ForeignKey(User)
created_at    DateTimeField(auto_now_add=True)
updated_at    DateTimeField(auto_now=True)
```

### PollOption
```python
poll          ForeignKey(Poll, related_name='options')
option_text   CharField(max_length=300)
```

### Vote
```python
user          ForeignKey(User, related_name='votes')
poll          ForeignKey(Poll, related_name='votes')
option        ForeignKey(PollOption, related_name='votes')
voted_at      DateTimeField(auto_now=True)

# Constraint: one vote per user per poll
UniqueConstraint(fields=['user', 'poll'])
```

---

## Key Behaviors

### Vote Change Logic
When a user changes their vote:
1. The existing `Vote` record is found (unique per user+poll)
2. Only the `option` field is updated — no new record created
3. Old option's count decreases, new option's count increases
4. Total vote count stays the same ✓

### Live Results
- `/api/results/<poll_id>/` returns JSON with vote counts and percentages
- Results page fetches this endpoint every 3 seconds using `setInterval`
- Progress bars animate smoothly using CSS transitions

### Security
- All poll management views require `@login_required`
- CSRF protection on all POST forms
- Users can only edit/delete their own polls (404 if not owner)
- Vote changes validated server-side

---

## Customization

### Change Theme Colors
Edit CSS variables in `templates/base.html`:
```css
:root {
    --accent: #6EE7B7;    /* Primary green accent */
    --accent2: #38BDF8;   /* Blue accent */
    --surface: #111827;   /* Card background */
    --brand: #0D0D0D;     /* Page background */
}
```

### Change Refresh Interval
In `templates/polls/results.html`:
```javascript
setInterval(fetchResults, 3000); // Change 3000ms to desired interval
```

---

## Requirements

- Python 3.8+
- Django 4.0+
- No other packages required (Bootstrap loaded from CDN)
