# Email Notification System Documentation

## Overview

The SV Rap 8 web application includes an automated email notification system that informs players about new events and sends reminders for upcoming events.

## Features

### 1. New Event Notifications

When a new event is created through the admin interface, all active players with email addresses automatically receive a notification.

#### Single Events
- One email per event
- Contains all event details (name, type, date, location, etc.)
- Clear call-to-action to log in and mark attendance

#### Recurring Events
- **One consolidated email** for the entire recurring series
- Shows first event date, recurrence pattern, and total number of events
- Explains that players can mark attendance for each individual event
- More efficient than sending separate emails for each event in the series

### 2. Event Reminder Notifications

Reminder emails can be sent to players who haven't yet responded to an event:
- Only sent to players who haven't marked their attendance
- Includes all event details
- Emphasizes the importance of responding

## Email Templates

### Regular Event Notification
- **Template**: `notifications/emails/new_event.html` (HTML) and `new_event.txt` (plain text)
- **Subject**: "Nieuw evenement: [Event Name]"
- **Content**: Event details, mandatory status, participant limits

### Recurring Event Notification
- **Template**: `notifications/emails/recurring_event.html` (HTML) and `recurring_event.txt` (plain text)
- **Subject**: "Herhalend evenement: [Event Name]"
- **Content**: Series overview, recurrence pattern, total events count

### Event Reminder
- **Template**: `notifications/emails/event_reminder.html` (HTML) and `event_reminder.txt` (plain text)
- **Subject**: "Herinnering: [Event Name] - Geef je aanwezigheid door"
- **Content**: Event details with emphasis on response needed

## Technical Implementation

### Key Functions

#### `send_new_event_notification(event)`
Sends notification for a single new event to all active players.

#### `send_recurring_event_notification(events)`
Sends one consolidated notification for a series of recurring events.

#### `send_bulk_notifications(events, notification_type)`
Smart function that:
- Detects if events are part of a recurring series
- For recurring events: sends one consolidated email
- For individual events: sends separate emails
- Returns success/error counts

#### `send_event_reminder_notification(event, days_before)`
Sends reminders to players who haven't responded yet.

### Integration Points

#### Event Creation (events/views.py)
When events are created via the web interface:
- Single events → `send_new_event_notification()`
- Recurring events → `send_bulk_notifications()` with smart detection

#### Admin Actions
Staff can manually trigger notifications through the admin interface.

### Configuration

Email settings are configured in `settings.py`:
- Uses Brevo SMTP backend
- Environment variables for credentials
- HTML and plain text versions for all emails

## Usage Examples

### Automatic Notifications
Notifications are sent automatically when:
1. Staff creates a new event through the web interface
2. Staff creates a recurring event series

### Manual Testing
Use management commands to test the system:

```bash
# Test basic email configuration
python manage.py test_email --to your@email.com

# Test recurring event notification
python manage.py test_recurring_notification --email your@email.com
```

### Message Feedback
The system provides clear feedback messages:
- **Success**: "Evenement succesvol aangemaakt en notificaties verzonden naar alle actieve spelers."
- **Warning**: Shows if events were created but notifications failed
- **Recurring**: "één samengevatte notificatie verzonden naar alle actieve spelers."

## Error Handling

- Graceful failure: Events are always created even if email sending fails
- Detailed logging of all notification attempts
- User-friendly error messages in the admin interface
- Automatic retry logic could be added with Celery in the future

## Future Enhancements

- Scheduled reminder emails (1 day before, 1 hour before)
- User preferences for notification frequency
- Push notifications for mobile apps
- Email templates with team branding
- Notification history tracking
