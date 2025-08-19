import json
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import PollForm, PollOptionFormSet
from .models import Poll, PollOption, Vote

User = get_user_model()


def is_staff(user):
    """Check if user is staff"""
    return user.is_staff


def is_active_player(user):
    """Check if user is an active player"""
    return user.is_authenticated and user.is_active


@login_required
def poll_list(request: HttpRequest):
    """List all polls - active ones first, then closed ones"""
    active_polls = Poll.objects.filter(is_active=True).order_by('-created_at')
    closed_polls = Poll.objects.filter(is_active=False).order_by('-closed_at', '-created_at')
    
    context = {
        'active_polls': active_polls,
        'closed_polls': closed_polls,
    }
    return render(request, 'polls/poll_list.html', context)


@login_required
def poll_detail(request: HttpRequest, pk: int):
    """View poll details and results"""
    poll = get_object_or_404(Poll, pk=pk)
    
    # Get current user's votes for this poll
    user_votes = []
    if request.user.is_authenticated:
        user_votes = Vote.objects.filter(
            poll_option__poll=poll, 
            user=request.user
        ).values_list('poll_option_id', flat=True)
    
    # Get poll results
    results = poll.get_results()
    
    context = {
        'poll': poll,
        'results': results,
        'user_votes': list(user_votes),
        'can_vote': poll.is_open and is_active_player(request.user),
    }
    return render(request, 'polls/poll_detail.html', context)


@user_passes_test(is_staff)
def poll_create(request: HttpRequest):
    """Create a new poll - staff only"""
    if request.method == 'POST':
        form = PollForm(request.POST)
        formset = PollOptionFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                poll = form.save(commit=False)
                poll.created_by = request.user
                poll.save()
                
                # Save poll options
                for option_form in formset:
                    if option_form.cleaned_data and not option_form.cleaned_data.get('DELETE', False):
                        option = option_form.save(commit=False)
                        option.poll = poll
                        option.save()
                
                messages.success(request, f'Poll "{poll.title}" is succesvol aangemaakt!')
                return redirect('polls:detail', pk=poll.pk)
    else:
        form = PollForm()
        formset = PollOptionFormSet()
    
    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'polls/poll_create.html', context)


@user_passes_test(is_staff)
def poll_edit(request: HttpRequest, pk: int):
    """Edit an existing poll - staff only"""
    poll = get_object_or_404(Poll, pk=pk)
    
    if request.method == 'POST':
        form = PollForm(request.POST, instance=poll)
        formset = PollOptionFormSet(request.POST, instance=poll)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                poll = form.save()
                formset.save()
                
                messages.success(request, f'Poll "{poll.title}" is bijgewerkt!')
                return redirect('polls:detail', pk=poll.pk)
    else:
        form = PollForm(instance=poll)
        formset = PollOptionFormSet(instance=poll)
    
    context = {
        'poll': poll,
        'form': form,
        'formset': formset,
    }
    return render(request, 'polls/poll_edit.html', context)


@user_passes_test(is_staff)
@require_POST
def poll_close(request: HttpRequest, pk: int):
    """Close a poll manually - staff only"""
    poll = get_object_or_404(Poll, pk=pk)
    
    if poll.is_open:
        poll.close_poll(user=request.user)
        messages.success(request, f'Poll "{poll.title}" is gesloten.')
    else:
        messages.warning(request, f'Poll "{poll.title}" is al gesloten.')
    
    return redirect('polls:detail', pk=poll.pk)


@user_passes_test(is_staff)
@require_POST
def poll_reopen(request: HttpRequest, pk: int):
    """Reopen a closed poll - staff only"""
    poll = get_object_or_404(Poll, pk=pk)
    
    if not poll.is_open:
        poll.is_active = True
        poll.closed_at = None
        poll.closed_by = None
        poll.save()
        messages.success(request, f'Poll "{poll.title}" is heropend.')
    else:
        messages.warning(request, f'Poll "{poll.title}" is al open.')
    
    return redirect('polls:detail', pk=poll.pk)


@login_required
@require_POST
def vote(request: HttpRequest, pk: int):
    """Cast a vote on a poll - active players only"""
    poll = get_object_or_404(Poll, pk=pk)
    
    if not is_active_player(request.user):
        return JsonResponse({
            'success': False, 
            'error': 'Alleen actieve spelers kunnen stemmen.'
        }, status=403)
    
    if not poll.is_open:
        return JsonResponse({
            'success': False, 
            'error': 'Deze poll is gesloten voor stemmen.'
        }, status=400)
    
    try:
        data = json.loads(request.body)
        option_ids = data.get('option_ids', [])
        
        if not option_ids:
            return JsonResponse({
                'success': False, 
                'error': 'Geen opties geselecteerd.'
            }, status=400)
        
        # Validate option IDs belong to this poll
        valid_option_ids = set(
            poll.options.filter(id__in=option_ids).values_list('id', flat=True)
        )
        
        if set(option_ids) != valid_option_ids:
            return JsonResponse({
                'success': False, 
                'error': 'Ongeldige opties geselecteerd.'
            }, status=400)
        
        # Check multiple choice restriction
        if len(option_ids) > 1 and not poll.allow_multiple_choices:
            return JsonResponse({
                'success': False, 
                'error': 'Deze poll staat slechts één keuze toe.'
            }, status=400)
        
        with transaction.atomic():
            # Remove existing votes for this poll
            Vote.objects.filter(
                poll_option__poll=poll, 
                user=request.user
            ).delete()
            
            # Create new votes
            for option_id in option_ids:
                option = PollOption.objects.get(id=option_id, poll=poll)
                Vote.objects.create(user=request.user, poll_option=option)
        
        # Return updated results
        results = poll.get_results()
        
        return JsonResponse({
            'success': True,
            'message': 'Je stem is geregistreerd!',
            'results': [{
                'option_id': result['option'].id,
                'vote_count': result['vote_count'],
                'percentage': result['percentage']
            } for result in results],
            'total_votes': poll.total_votes,
            'unique_voters': poll.unique_voters
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'Ongeldige data ontvangen.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': 'Er is een fout opgetreden bij het verwerken van je stem.'
        }, status=500)


@login_required
def poll_results(request: HttpRequest, pk: int):
    """Get poll results via AJAX for real-time updates"""
    poll = get_object_or_404(Poll, pk=pk)
    results = poll.get_results()
    
    return JsonResponse({
        'results': [{
            'option_id': result['option'].id,
            'option_text': result['option'].text,
            'vote_count': result['vote_count'],
            'percentage': result['percentage']
        } for result in results],
        'total_votes': poll.total_votes,
        'unique_voters': poll.unique_voters,
        'is_open': poll.is_open
    })
