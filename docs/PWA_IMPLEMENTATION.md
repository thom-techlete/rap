# PWA Implementation Documentation for SV Rap 8

## Overview

The SV Rap 8 webapp has been successfully enhanced with Progressive Web App (PWA) capabilities and push notifications to provide a native app-like experience for users.

## Features Implemented

### 1. Web App Manifest (`/static/manifest.json`)
- **Name**: "SV Rap 8 - Aanwezigheid"
- **Display**: Standalone mode for native app feel
- **Theme Colors**: Team blue (#1e40af)
- **Icons**: 8 different sizes (72x72 to 512x512) for various devices
- **Shortcuts**: Quick access to Dashboard, Events, and Attendance
- **Language**: Dutch (nl) as primary language

### 2. Service Worker (`/static/sw.js`)
- **Offline Support**: Caches static assets and provides offline fallback
- **Push Notifications**: Handles incoming push messages
- **Background Sync**: Prepared for future offline functionality
- **Cache Strategy**: Network-first with cache fallback
- **Notification Click Handling**: Opens app when notification is clicked

### 3. Push Notification System
- **Backend**: Django models for subscription management
- **VAPID Keys**: Secure push notification authentication
- **Celery Tasks**: Background processing for sending notifications
- **Admin Interface**: Push subscription management and testing

### 4. User Interface
- **PWA Meta Tags**: Apple Touch icons and mobile optimization
- **Install Detection**: Shows when app can be installed
- **Notification Settings**: User-friendly permission management
- **Offline Page**: Branded fallback when offline

## Database Models Added

### PushSubscription
- User relationship
- Endpoint and encryption keys
- User agent tracking
- Active status management

### PushNotificationLog
- Notification sending history
- Success/failure tracking
- Error message logging

## API Endpoints

- `GET /notifications/push/subscribe/` - Check subscription status
- `POST /notifications/push/subscribe/` - Subscribe to notifications
- `DELETE /notifications/push/subscribe/` - Unsubscribe
- `POST /notifications/push/test/` - Send test notification
- `GET /notifications/push/vapid-key/` - Get public VAPID key
- `GET /notifications/offline/` - Offline page

## Installation Instructions

### 1. Dependencies
Add to `pyproject.toml`:
```toml
"pywebpush",  # For web push notifications
```

### 2. VAPID Keys Generation
```python
from py_vapid import Vapid01
from cryptography.hazmat.primitives import serialization
import base64

vapid = Vapid01()
vapid.generate_keys()

# Get private key (PEM format)
private_key_bytes = vapid.private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Get public key for browser (base64 URL-safe)
raw_public_key = vapid.public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)
public_key_b64 = base64.urlsafe_b64encode(raw_public_key).decode('utf-8').rstrip('=')
```

### 3. Environment Variables
```bash
export VAPID_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
export VAPID_PUBLIC_KEY="BChQ0eFZqW-0nBlV3N734..."
```

### 4. Database Migration
```bash
python manage.py makemigrations notifications
python manage.py migrate
```

## Testing PWA Features

### 1. PWA Installation
1. Open the app in Chrome/Edge on mobile or desktop
2. Look for "Install" prompt in address bar
3. Install to home screen
4. App should open in standalone mode (no browser UI)

### 2. Push Notifications
1. Log in to the app
2. Open user menu → "Notificaties"
3. Click "Inschakelen" for push notifications
4. Grant permission when prompted
5. Test with "Test Notificatie Verzenden" button

### 3. Offline Functionality
1. Open the app and browse some pages
2. Disable internet connection
3. Navigate to cached pages (should work)
4. Try new pages (should show offline page)

## Browser Support

### PWA Installation
- ✅ Chrome/Chromium (Android, Desktop)
- ✅ Edge (Android, Desktop)
- ✅ Safari (iOS 11.3+)
- ✅ Firefox (Android, with limitations)

### Push Notifications
- ✅ Chrome/Chromium (Android, Desktop)
- ✅ Edge (Android, Desktop)
- ✅ Firefox (Android, Desktop)
- ⚠️ Safari (iOS 16.4+, macOS 13+)

## Usage Examples

### Send Event Notification
```python
from notifications.tasks import send_event_push_notification

# Send notification for new event
send_event_push_notification.delay(event_id=123, message_type='new_event')

# Send reminder
send_event_push_notification.delay(event_id=123, message_type='reminder')
```

### Manual Push Notification
```python
from notifications.tasks import send_push_to_users

notification_data = {
    'title': 'Team Meeting',
    'body': 'Don\'t forget about today\'s team meeting at 7 PM',
    'icon': '/static/media/icons/icon-192x192.png',
    'url': '/events/123/'
}

user_ids = [1, 2, 3, 4]  # List of user IDs
send_push_to_users.delay(user_ids, notification_data)
```

## Security Considerations

1. **VAPID Keys**: Keep private key secure and never expose in frontend
2. **Subscription Validation**: Validate push subscriptions before sending
3. **Rate Limiting**: Prevent notification spam (implemented in views)
4. **User Consent**: Explicit permission required for notifications

## Future Enhancements

1. **Background Sync**: Sync attendance when back online
2. **Advanced Caching**: More intelligent cache strategies
3. **Notification Categories**: Different types of notifications
4. **Notification History**: Track user notification preferences
5. **Rich Notifications**: Images and interactive buttons

## Troubleshooting

### Service Worker Not Installing
- Check browser developer tools → Application → Service Workers
- Ensure HTTPS or localhost for development
- Clear browser cache and reload

### Push Notifications Not Working
- Verify VAPID keys are correctly set
- Check notification permissions in browser settings
- Ensure subscription is active in database
- Check Celery worker is running for background tasks

### PWA Not Installable
- Verify manifest.json is accessible
- Check all required manifest fields are present
- Ensure service worker is registered
- Use Lighthouse audit to check PWA criteria

## Maintenance

### Regular Tasks
1. Clean up old push subscriptions (weekly)
2. Monitor notification delivery rates
3. Update service worker version when deploying
4. Test PWA functionality on new browser versions

### Monitoring
- Push notification success rates in admin
- Service worker cache hit rates
- PWA installation analytics
- User notification preferences