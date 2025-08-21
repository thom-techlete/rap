from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from events.models import Event
import json
import logging

from .models import ScheduleConfiguration, EventScheduleOverride, PushSubscription, PushNotificationLog
from .utils import send_event_reminder_notification, send_new_event_notification, sync_periodic_tasks
from .tasks import send_push_notification

logger = logging.getLogger(__name__)


def is_staff(user):
    """Check if user is staff"""
    return user.is_staff


@user_passes_test(is_staff)
def schedule_admin_dashboard(request):
    """
    Admin dashboard for managing notification scheduling.
    """
    configurations = ScheduleConfiguration.objects.all().order_by("name")
    overrides = EventScheduleOverride.objects.select_related("event", "configuration").order_by("-created_at")[:10]
    
    context = {
        "configurations": configurations,
        "recent_overrides": overrides,
        "total_configurations": configurations.count(),
        "total_overrides": EventScheduleOverride.objects.count(),
    }
    
    return render(request, "notifications/admin/schedule_dashboard.html", context)


@user_passes_test(is_staff)
@require_POST
def sync_tasks_manual(request):
    """
    Manually trigger sync of periodic tasks.
    """
    try:
        sync_periodic_tasks()
        messages.success(request, "Periodic tasks successfully synchronized with Celery beat.")
    except Exception as e:
        messages.error(request, f"Failed to sync periodic tasks: {e}")
    
    return redirect("notifications:schedule_admin_dashboard")


@user_passes_test(is_staff)
@require_POST
def send_event_notification(request, event_id):
    """Send new event notification manually"""
    event = get_object_or_404(Event, id=event_id)

    try:
        send_new_event_notification(event)
        messages.success(
            request,
            f"Nieuwe evenement notificatie succesvol verzonden voor '{event.name}'",
        )
    except Exception as e:
        messages.error(
            request, f"Fout bij verzenden notificatie voor '{event.name}': {str(e)}"
        )

    return redirect("events:list")


@user_passes_test(is_staff)
@require_POST
def send_event_reminder(request, event_id):
    """Send event reminder notification manually"""
    event = get_object_or_404(Event, id=event_id)

    try:
        send_event_reminder_notification(event)
        messages.success(
            request, f"Herinnering succesvol verzonden voor '{event.name}'"
        )
    except Exception as e:
        messages.error(
            request, f"Fout bij verzenden herinnering voor '{event.name}': {str(e)}"
        )

    return redirect("events:list")


@user_passes_test(is_staff)
def notification_status(request):
    """AJAX endpoint to check notification sending status"""
    # This could be extended to show notification logs/status
    return JsonResponse(
        {"status": "active", "message": "Notification system is operational"}
    )


# ==============================================================================
# PUSH NOTIFICATION VIEWS
# ==============================================================================

@method_decorator(login_required, name='dispatch')
class PushSubscriptionView(View):
    """
    Handle push notification subscription management.
    """
    
    def get(self, request):
        """Get user's current push subscription status."""
        subscriptions = PushSubscription.objects.filter(
            user=request.user,
            is_active=True
        ).count()
        
        return JsonResponse({
            'subscribed': subscriptions > 0,
            'count': subscriptions,
            'vapid_public_key': getattr(settings, 'VAPID_PUBLIC_KEY', None)
        })
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Subscribe to push notifications."""
        try:
            data = json.loads(request.body)
            subscription_data = data.get('subscription', {})
            
            if not subscription_data:
                return JsonResponse({'error': 'No subscription data provided'}, status=400)
            
            # Extract subscription details
            endpoint = subscription_data.get('endpoint')
            keys = subscription_data.get('keys', {})
            p256dh = keys.get('p256dh')
            auth = keys.get('auth')
            
            if not all([endpoint, p256dh, auth]):
                return JsonResponse({'error': 'Invalid subscription data'}, status=400)
            
            # Create or update subscription
            subscription, created = PushSubscription.objects.update_or_create(
                user=request.user,
                endpoint=endpoint,
                defaults={
                    'p256dh_key': p256dh,
                    'auth_key': auth,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'is_active': True
                }
            )
            
            action = 'created' if created else 'updated'
            logger.info(f"Push subscription {action} for user {request.user.get_full_name()}")
            
            return JsonResponse({
                'success': True,
                'action': action,
                'subscription_id': subscription.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Error creating push subscription: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    @method_decorator(csrf_exempt)
    def delete(self, request):
        """Unsubscribe from push notifications."""
        try:
            data = json.loads(request.body)
            endpoint = data.get('endpoint')
            
            if not endpoint:
                # Delete all subscriptions for user
                deleted_count, _ = PushSubscription.objects.filter(
                    user=request.user,
                    is_active=True
                ).update(is_active=False)
            else:
                # Delete specific subscription
                deleted_count = PushSubscription.objects.filter(
                    user=request.user,
                    endpoint=endpoint,
                    is_active=True
                ).update(is_active=False)
            
            return JsonResponse({
                'success': True,
                'unsubscribed_count': deleted_count
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Error deleting push subscription: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def send_test_notification(request):
    """
    Send a test push notification to the user.
    """
    try:
        # Get user's active subscriptions
        subscriptions = PushSubscription.objects.filter(
            user=request.user,
            is_active=True
        )
        
        if not subscriptions.exists():
            return JsonResponse({'error': 'No active push subscriptions found'}, status=400)
        
        # Prepare test notification
        notification_data = {
            'title': 'Test Notificatie - SV Rap 8',
            'body': 'Dit is een test notificatie om te controleren of push notifications werken.',
            'icon': '/static/media/icons/icon-192x192.png',
            'badge': '/static/media/icons/icon-96x96.png',
            'url': '/',
            'tag': 'test-notification',
            'actions': [
                {
                    'action': 'open',
                    'title': 'Openen',
                    'icon': '/static/media/icons/icon-96x96.png'
                }
            ],
            'data': {
                'url': '/',
                'test': True
            }
        }
        
        # Send to all user's subscriptions
        sent_count = 0
        for subscription in subscriptions:
            success = send_push_notification.delay(subscription.id, notification_data)
            if success:
                sent_count += 1
        
        return JsonResponse({
            'success': True,
            'sent_count': sent_count,
            'total_subscriptions': subscriptions.count()
        })
        
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        return JsonResponse({'error': 'Failed to send test notification'}, status=500)


@login_required
def get_vapid_public_key(request):
    """
    Return the VAPID public key for push subscriptions.
    """
    public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
    
    if not public_key:
        return JsonResponse({'error': 'VAPID public key not configured'}, status=500)
    
    return JsonResponse({'vapid_public_key': public_key})


def offline_page(request):
    """
    Serve offline page for PWA.
    """
    from django.shortcuts import render
    return render(request, 'offline.html')
