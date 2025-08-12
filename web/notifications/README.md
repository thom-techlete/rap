# Notification System Documentation

## Overview

The SV Rap 8 notification system automatically sends email notifications to all active players when:
1. A new event is created
2. Reminders are sent for upcoming events

## Features

### Automatic Notifications
- **New Event Notifications**: Automatically sent when an event is created via the web interface
- **Recurring Event Support**: When creating recurring events, notifications are sent for all events in the series
- **Smart Error Handling**: If notifications fail, the event is still created but admins are notified of the issue

### Manual Notifications
Staff members can manually send notifications for any event via:
- Event cards in the event list (dropdown menu)
- Django admin interface 
- Management commands

### Email Templates
- **HTML emails** with responsive design for modern email clients
- **Plain text fallback** for older email clients
- **Dutch language** with appropriate formatting for the target audience

## Configuration

### Email Settings
The system uses the existing Django email configuration in `settings.py`:
```python
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp-relay.brevo.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD") 
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
```

### Environment Variables Required
- `EMAIL_HOST_USER`: Brevo SMTP login email
- `EMAIL_HOST_PASSWORD`: Brevo SMTP key
- `DEFAULT_FROM_EMAIL`: Verified sender email address

## Usage

### For Developers

#### Sending notifications programmatically:
```python
from notifications.utils import send_new_event_notification, send_event_reminder_notification
from events.models import Event

# Send new event notification
event = Event.objects.get(id=1)
send_new_event_notification(event)

# Send reminder notification  
send_event_reminder_notification(event)
```

#### Testing email configuration:
```bash
python manage.py test_email --to your@email.com
```

### For Administrators

#### Manual notification sending:
1. Navigate to the Events page
2. Find the event you want to send notifications for
3. Click the "..." menu in the top-right corner of the event card
4. Choose either:
   - "Verzend evenement notificatie" - sends new event notification to all active players
   - "Verzend herinnering" - sends reminder to players who haven't responded yet

#### Management commands:
```bash
# Send test email
python manage.py test_email --to recipient@email.com

# Send reminders for events happening tomorrow
python manage.py send_event_reminders --days 1

# Send reminder for specific event
python manage.py send_event_reminders --event-id 123
```

## Notification Types

### New Event Notification
- **Trigger**: When a new event is created
- **Recipients**: All active players with email addresses
- **Content**: Event details, date/time, location, description
- **Call-to-action**: Encourages players to log in and indicate attendance

### Event Reminder  
- **Trigger**: Manual or scheduled (e.g., 1 day before event)
- **Recipients**: Active players who haven't indicated their attendance yet
- **Content**: Event reminder with details and urgency
- **Call-to-action**: Reminds players to indicate their attendance

## Error Handling

The notification system includes robust error handling:
- **Individual failures**: If an email fails to send, it logs the error but continues processing other recipients
- **Bulk failures**: For recurring events, if some notifications fail, successful ones are still sent
- **User feedback**: Admin users receive clear feedback about notification success/failure
- **Logging**: All notification attempts and errors are logged for debugging

## Customization

### Email Templates
Templates are located in `notifications/templates/notifications/emails/`:
- `new_event.html` / `new_event.txt` - New event notifications
- `event_reminder.html` / `event_reminder.txt` - Event reminders

### Adding New Notification Types
1. Create new template files
2. Add function to `notifications/utils.py`
3. Create views in `notifications/views.py`
4. Add URL patterns in `notifications/urls.py`

## Security Considerations

- Only staff users can manually send notifications
- CSRF protection on all notification endpoints
- Email addresses are validated before sending
- Rate limiting should be considered for high-volume usage

## Troubleshooting

### Common Issues

1. **No emails being sent**
   - Check environment variables are set correctly
   - Verify Brevo SMTP credentials
   - Test with `python manage.py test_email --to your@email.com`

2. **Users not receiving emails**
   - Verify users have email addresses in their profiles
   - Check spam/junk folders
   - Ensure users are marked as active

3. **Emails sent but notifications failing**
   - Check Django logs for error messages
   - Verify template syntax is correct
   - Ensure event data is complete

### Logging
All notification activities are logged. Check Django logs for:
- Successful notifications: `INFO` level
- Failed notifications: `ERROR` level
- Email sending attempts: `DEBUG` level

## Future Enhancements

Potential improvements to consider:
- **Scheduling**: Automatic reminders sent X days before events
- **Preferences**: Allow users to choose notification types
- **SMS notifications**: Integration with SMS services
- **Push notifications**: Web push notifications for logged-in users
- **Notification history**: Track which notifications were sent when
- **A/B testing**: Test different email templates for engagement
