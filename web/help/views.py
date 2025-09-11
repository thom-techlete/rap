from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .models import BugReport
from .forms import BugReportForm, AdminBugReportForm


@login_required
def help_index(request):
    """Main help page with options to report bugs and view help topics."""
    context = {
        'page_title': 'Hulp & Ondersteuning'
    }
    return render(request, 'help/index.html', context)


@login_required
def bug_report_create(request):
    """Allow users to submit bug reports."""
    if request.method == 'POST':
        form = BugReportForm(request.POST)
        if form.is_valid():
            bug_report = form.save(commit=False)
            bug_report.reported_by = request.user
            bug_report.save()
            messages.success(
                request, 
                "Je bug rapport is succesvol ingediend! Ons team zal er zo snel mogelijk naar kijken."
            )
            return redirect('help:bug_detail', pk=bug_report.pk)
    else:
        form = BugReportForm()
    
    context = {
        'form': form,
        'page_title': 'Bug Rapporteren'
    }
    return render(request, 'help/bug_report_create.html', context)


@login_required
def bug_detail(request, pk):
    """Show details of a specific bug report."""
    bug_report = get_object_or_404(BugReport, pk=pk)
    
    # Users can only view their own bug reports unless they're staff
    if not request.user.is_staff and bug_report.reported_by != request.user:
        raise Http404("Bug rapport niet gevonden")
    
    context = {
        'bug_report': bug_report,
        'page_title': f'Bug Rapport #{bug_report.id}'
    }
    return render(request, 'help/bug_detail.html', context)


@login_required
def my_bug_reports(request):
    """Show all bug reports submitted by the current user."""
    bug_reports = BugReport.objects.filter(reported_by=request.user)
    
    # Pagination
    paginator = Paginator(bug_reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'page_title': 'Mijn Bug Rapporten'
    }
    return render(request, 'help/my_bug_reports.html', context)


def is_staff(user):
    """Check if user is staff."""
    return user.is_staff


@login_required
@user_passes_test(is_staff)
def admin_bug_list(request):
    """Admin view to list all bug reports with filtering and search."""
    bug_reports = BugReport.objects.select_related('reported_by', 'assigned_to', 'resolved_by')
    
    # Filtering
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    search_query = request.GET.get('q')
    
    if status_filter:
        bug_reports = bug_reports.filter(status=status_filter)
    
    if priority_filter:
        bug_reports = bug_reports.filter(priority=priority_filter)
    
    if search_query:
        bug_reports = bug_reports.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(reported_by__username__icontains=search_query) |
            Q(reported_by__first_name__icontains=search_query) |
            Q(reported_by__last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(bug_reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter choices for template
    status_choices = BugReport.STATUS_CHOICES
    priority_choices = BugReport.PRIORITY_CHOICES
    
    context = {
        'page_obj': page_obj,
        'status_choices': status_choices,
        'priority_choices': priority_choices,
        'current_status': status_filter,
        'current_priority': priority_filter,
        'search_query': search_query or '',
        'page_title': 'Bug Rapporten Beheer'
    }
    return render(request, 'help/admin_bug_list.html', context)


@login_required
@user_passes_test(is_staff)
def admin_bug_detail(request, pk):
    """Admin view to manage a specific bug report."""
    bug_report = get_object_or_404(BugReport, pk=pk)
    
    if request.method == 'POST':
        form = AdminBugReportForm(request.POST, instance=bug_report)
        if form.is_valid():
            # Check if status changed to resolved/closed
            old_status = bug_report.status
            new_bug_report = form.save(commit=False)
            
            if old_status != new_bug_report.status:
                if new_bug_report.status == 'resolved' and not bug_report.resolved_at:
                    new_bug_report.resolved_at = timezone.now()
                    new_bug_report.resolved_by = request.user
                elif new_bug_report.status == 'closed' and not bug_report.resolved_at:
                    new_bug_report.resolved_at = timezone.now()
                    new_bug_report.resolved_by = request.user
            
            new_bug_report.save()
            messages.success(request, "Bug rapport is bijgewerkt.")
            return redirect('help:admin_bug_detail', pk=bug_report.pk)
    else:
        form = AdminBugReportForm(instance=bug_report)
    
    context = {
        'bug_report': bug_report,
        'form': form,
        'page_title': f'Bug Rapport #{bug_report.id} - Beheer'
    }
    return render(request, 'help/admin_bug_detail.html', context)


@login_required
@user_passes_test(is_staff)
def admin_bug_mark_resolved(request, pk):
    """Quick action to mark a bug as resolved."""
    if request.method == 'POST':
        bug_report = get_object_or_404(BugReport, pk=pk)
        bug_report.mark_resolved(request.user)
        messages.success(request, f"Bug rapport #{bug_report.id} is gemarkeerd als opgelost.")
    
    return redirect('help:admin_bug_list')


@login_required
@user_passes_test(is_staff)
def admin_bug_mark_closed(request, pk):
    """Quick action to mark a bug as closed."""
    if request.method == 'POST':
        bug_report = get_object_or_404(BugReport, pk=pk)
        bug_report.mark_closed(request.user)
        messages.success(request, f"Bug rapport #{bug_report.id} is gesloten.")
    
    return redirect('help:admin_bug_list')
