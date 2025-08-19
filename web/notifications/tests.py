from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from events.models import Event
from .utils import send_event_reminder_notification, send_new_event_notification
from unittest.mock import patch
import pytz

User = get_user_model()


class NotificationTimezoneTestCase(TestCase):
    """Test timezone handling in notification functions"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a test event with a specific time in Amsterdam timezone
        amsterdam_tz = pytz.timezone('Europe/Amsterdam')
        # Create a datetime at 20:30 Amsterdam time
        amsterdam_time = amsterdam_tz.localize(datetime(2024, 12, 25, 20, 30))
        
        self.event = Event.objects.create(
            name='Test Training',
            description='A test training session',
            event_type='training',
            date=amsterdam_time,  # This will be stored as UTC in the database
            location='Test Field'
        )
    
    @patch('notifications.utils.send_mail')
    def test_event_reminder_shows_correct_time(self, mock_send_mail):
        """Test that event reminder shows time in Amsterdam timezone (20:30), not UTC (18:30)"""
        # Call the function
        send_event_reminder_notification(self.event)
        
        # Verify send_mail was called
        self.assertTrue(mock_send_mail.called)
        
        # Get the html_message argument
        call_args = mock_send_mail.call_args
        html_message = call_args[1]['html_message']
        
        # Check that the message contains the correct Amsterdam time (20:30)
        self.assertIn('20:30', html_message)
        # And doesn't contain the incorrect UTC time (18:30)
        self.assertNotIn('18:30', html_message)
    
    @patch('notifications.utils.send_mail')
    def test_new_event_shows_correct_time(self, mock_send_mail):
        """Test that new event notification shows time in Amsterdam timezone (20:30), not UTC (18:30)"""
        # Call the function
        send_new_event_notification(self.event)
        
        # Verify send_mail was called
        self.assertTrue(mock_send_mail.called)
        
        # Get the html_message argument
        call_args = mock_send_mail.call_args
        html_message = call_args[1]['html_message']
        
        # Check that the message contains the correct Amsterdam time (20:30)
        self.assertIn('20:30', html_message)
        # And doesn't contain the incorrect UTC time (18:30)
        self.assertNotIn('18:30', html_message)
