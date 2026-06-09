from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('polls/', views.poll_list_view, name='poll_list'),
    path('polls/create/', views.create_poll_view, name='create_poll'),
    path('polls/my/', views.my_polls_view, name='my_polls'),
    path('polls/edit/<int:poll_id>/', views.edit_poll_view, name='edit_poll'),
    path('polls/delete/<int:poll_id>/', views.delete_poll_view, name='delete_poll'),
    path('vote/<int:poll_id>/', views.vote_view, name='vote'),
    path('results/<int:poll_id>/', views.results_view, name='results'),
    path('api/results/<int:poll_id>/', views.api_results_view, name='api_results'),
]
