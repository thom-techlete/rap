"""
Tests for PWA and push notification functionality.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from notifications.models import PushSubscription, PushNotificationLog
import json

User = get_user_model()


class PWATestCase(TestCase):
    """Test PWA basic functionality."""
    
    def test_manifest_accessible(self):
        """Test that the PWA manifest is accessible."""
        response = self.client.get('/static/manifest.json')
        self.assertEqual(response.status_code, 200)
        # Should be valid JSON - handle FileResponse for static files
        content = b''.join(response.streaming_content) if hasattr(response, 'streaming_content') else response.content
        manifest = json.loads(content)
        self.assertEqual(manifest['name'], 'SV Rap 8 - Aanwezigheid')
        self.assertEqual(manifest['display'], 'standalone')
    
    def test_service_worker_accessible(self):
        """Test that the service worker is accessible."""
        response = self.client.get('/static/sw.js')
        self.assertEqual(response.status_code, 200)
        # Handle FileResponse for static files
        content = b''.join(response.streaming_content) if hasattr(response, 'streaming_content') else response.content
        self.assertIn(b'Service Worker', content)
    
    def test_offline_page(self):
        """Test that the offline page is accessible."""
        response = self.client.get('/notifications/offline/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'offline')


class PushNotificationTestCase(TestCase):
    """Test push notification functionality."""
    
    def setUp(self):
        """Set up test user and client."""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client = Client()
        self.client.login(username='testuser@example.com', password='testpass123')
    
    def test_vapid_key_endpoint(self):
        """Test VAPID public key endpoint."""
        response = self.client.get(reverse('notifications:vapid_key'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        # Should have vapid_public_key field (might be None in tests)
        self.assertIn('vapid_public_key', data)
    
    def test_subscription_status_endpoint(self):
        """Test subscription status endpoint."""
        response = self.client.get(reverse('notifications:push_subscribe'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('subscribed', data)
        self.assertEqual(data['subscribed'], False)  # No subscription yet
    
    def test_push_subscription_creation(self):
        """Test creating a push subscription."""
        subscription_data = {
            'subscription': {
                'endpoint': 'https://fcm.googleapis.com/fcm/send/test-endpoint',
                'keys': {
                    'p256dh': 'test-p256dh-key',
                    'auth': 'test-auth-key'
                }
            }
        }
        
        response = self.client.post(
            reverse('notifications:push_subscribe'),
            data=json.dumps(subscription_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['action'], 'created')
        
        # Check subscription was created in database
        subscription = PushSubscription.objects.get(user=self.user)
        self.assertEqual(subscription.endpoint, 'https://fcm.googleapis.com/fcm/send/test-endpoint')
        self.assertEqual(subscription.p256dh_key, 'test-p256dh-key')
        self.assertEqual(subscription.auth_key, 'test-auth-key')
    
    def test_push_subscription_delete(self):
        """Test deleting a push subscription."""
        # Create a subscription first
        subscription = PushSubscription.objects.create(
            user=self.user,
            endpoint='https://fcm.googleapis.com/fcm/send/test-endpoint',
            p256dh_key='test-p256dh-key',
            auth_key='test-auth-key',
            is_active=True
        )
        
        delete_data = {
            'endpoint': 'https://fcm.googleapis.com/fcm/send/test-endpoint'
        }
        
        response = self.client.delete(
            reverse('notifications:push_subscribe'),
            data=json.dumps(delete_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Check subscription was deactivated
        subscription.refresh_from_db()
        self.assertFalse(subscription.is_active)
    
    def test_subscription_status_after_creation(self):
        """Test subscription status after creating a subscription."""
        # Create a subscription
        PushSubscription.objects.create(
            user=self.user,
            endpoint='https://fcm.googleapis.com/fcm/send/test-endpoint',
            p256dh_key='test-p256dh-key',
            auth_key='test-auth-key',
            is_active=True
        )
        
        response = self.client.get(reverse('notifications:push_subscribe'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['subscribed'], True)
        self.assertEqual(data['count'], 1)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access push endpoints."""
        self.client.logout()
        
        # Test subscription status endpoint
        response = self.client.get(reverse('notifications:push_subscribe'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test VAPID key endpoint
        response = self.client.get(reverse('notifications:vapid_key'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test push subscription creation
        response = self.client.post(reverse('notifications:push_subscribe'))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class PushNotificationModelTestCase(TestCase):
    """Test push notification models."""
    
    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
    
    def test_push_subscription_creation(self):
        """Test creating a PushSubscription."""
        subscription = PushSubscription.objects.create(
            user=self.user,
            endpoint='https://fcm.googleapis.com/fcm/send/test-endpoint',
            p256dh_key='test-p256dh-key',
            auth_key='test-auth-key'
        )
        
        self.assertEqual(str(subscription), f'Push subscription voor {self.user.get_full_name()} (https://fcm.googleapis.com/fcm/send/test-endpoint...)')
        self.assertTrue(subscription.is_active)
        
        # Test subscription info format
        info = subscription.get_subscription_info()
        self.assertEqual(info['endpoint'], 'https://fcm.googleapis.com/fcm/send/test-endpoint')
        self.assertEqual(info['keys']['p256dh'], 'test-p256dh-key')
        self.assertEqual(info['keys']['auth'], 'test-auth-key')
    
    def test_push_notification_log_creation(self):
        """Test creating a PushNotificationLog."""
        subscription = PushSubscription.objects.create(
            user=self.user,
            endpoint='https://fcm.googleapis.com/fcm/send/test-endpoint',
            p256dh_key='test-p256dh-key',
            auth_key='test-auth-key'
        )
        
        log = PushNotificationLog.objects.create(
            subscription=subscription,
            title='Test Notification',
            body='This is a test notification',
            success=True
        )
        
        self.assertEqual(str(log), f'✓ Test Notification naar {self.user.get_full_name()}')
        self.assertTrue(log.success)