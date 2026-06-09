from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
from .models import Poll, PollOption, Vote
from .forms import PollForm


@login_required
def dashboard_view(request):
    polls = Poll.objects.all().select_related('created_by').prefetch_related('options', 'votes')
    user_votes = {v.poll_id: v.option_id for v in Vote.objects.filter(user=request.user)}
    
    poll_data = []
    for poll in polls:
        poll_data.append({
            'poll': poll,
            'total_votes': poll.total_votes(),
            'user_voted': poll.id in user_votes,
            'user_option_id': user_votes.get(poll.id),
        })
    
    return render(request, 'polls/dashboard.html', {
        'poll_data': poll_data,
        'total_polls': polls.count(),
        'user_poll_count': request.user.polls.count(),
        'user_vote_count': Vote.objects.filter(user=request.user).count(),
    })


@login_required
def poll_list_view(request):
    polls = Poll.objects.all().select_related('created_by').prefetch_related('options')
    user_votes = {v.poll_id: v.option_id for v in Vote.objects.filter(user=request.user)}
    
    poll_data = []
    for poll in polls:
        poll_data.append({
            'poll': poll,
            'total_votes': poll.total_votes(),
            'user_voted': poll.id in user_votes,
            'user_option_id': user_votes.get(poll.id),
        })
    
    return render(request, 'polls/poll_list.html', {'poll_data': poll_data})


@login_required
def create_poll_view(request):
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        options = request.POST.getlist('options[]')
        options = [o.strip() for o in options if o.strip()]
        
        errors = []
        if not question:
            errors.append("Poll question is required.")
        if len(options) < 2:
            errors.append("Please provide at least 2 options.")
        if len(options) > 10:
            errors.append("Maximum 10 options allowed.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'polls/create_poll.html', {
                'question': question,
                'options': options
            })
        
        with transaction.atomic():
            poll = Poll.objects.create(question=question, created_by=request.user)
            for option_text in options:
                PollOption.objects.create(poll=poll, option_text=option_text)
        
        messages.success(request, 'Poll created successfully!')
        return redirect('poll_list')
    
    return render(request, 'polls/create_poll.html')


@login_required
def vote_view(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    
    if request.method == 'POST':
        option_id = request.POST.get('option')
        
        if not option_id:
            messages.error(request, 'Please select an option to vote.')
            return redirect('vote', poll_id=poll_id)
        
        try:
            option = PollOption.objects.get(id=option_id, poll=poll)
        except PollOption.DoesNotExist:
            messages.error(request, 'Invalid option selected.')
            return redirect('vote', poll_id=poll_id)
        
        with transaction.atomic():
            vote, created = Vote.objects.get_or_create(
                user=request.user,
                poll=poll,
                defaults={'option': option}
            )
            if not created:
                if vote.option == option:
                    messages.info(request, 'You already voted for this option.')
                else:
                    old_option = vote.option.option_text
                    vote.option = option
                    vote.save()
                    messages.success(request, f'Vote changed from "{old_option}" to "{option.option_text}"!')
            else:
                messages.success(request, f'Vote cast for "{option.option_text}"!')
        
        return redirect('results', poll_id=poll_id)
    
    user_vote = None
    try:
        user_vote = Vote.objects.get(user=request.user, poll=poll)
    except Vote.DoesNotExist:
        pass
    
    return render(request, 'polls/vote.html', {
        'poll': poll,
        'user_vote': user_vote,
    })


@login_required
def results_view(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    results, total = poll.get_results()
    
    user_vote = None
    try:
        user_vote = Vote.objects.get(user=request.user, poll=poll)
    except Vote.DoesNotExist:
        pass
    
    return render(request, 'polls/results.html', {
        'poll': poll,
        'results': results,
        'total': total,
        'user_vote': user_vote,
    })


@require_GET
def api_results_view(request, poll_id):
    """AJAX endpoint for live results"""
    try:
        poll = Poll.objects.get(id=poll_id)
    except Poll.DoesNotExist:
        return JsonResponse({'error': 'Poll not found'}, status=404)
    
    results, total = poll.get_results()
    return JsonResponse({
        'poll_id': poll_id,
        'total': total,
        'results': results,
    })


@login_required
def my_polls_view(request):
    polls = Poll.objects.filter(created_by=request.user).prefetch_related('options', 'votes')
    poll_data = []
    for poll in polls:
        poll_data.append({
            'poll': poll,
            'total_votes': poll.total_votes(),
        })
    return render(request, 'polls/my_polls.html', {'poll_data': poll_data})


@login_required
def edit_poll_view(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id, created_by=request.user)
    
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        options = request.POST.getlist('options[]')
        options = [o.strip() for o in options if o.strip()]
        
        errors = []
        if not question:
            errors.append("Poll question is required.")
        if len(options) < 2:
            errors.append("Please provide at least 2 options.")
        if len(options) > 10:
            errors.append("Maximum 10 options allowed.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            with transaction.atomic():
                poll.question = question
                poll.save()
                # Delete old votes and options, recreate
                Vote.objects.filter(poll=poll).delete()
                poll.options.all().delete()
                for option_text in options:
                    PollOption.objects.create(poll=poll, option_text=option_text)
            messages.success(request, 'Poll updated successfully! All votes have been reset.')
            return redirect('my_polls')
    
    existing_options = list(poll.options.values_list('option_text', flat=True))
    return render(request, 'polls/edit_poll.html', {
        'poll': poll,
        'existing_options': existing_options,
    })


@login_required
@require_POST
def delete_poll_view(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id, created_by=request.user)
    poll.delete()
    messages.success(request, 'Poll deleted successfully.')
    return redirect('my_polls')
