from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Event, MatchStatistic
from attendance.models import Attendance

User = get_user_model()


class EventListTestCase(TestCase):
    """Test event listing functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test events
        self.future_event = Event.objects.create(
            name='Test Training',
            description='A test training session',
            event_type='training',
            date=timezone.now() + timedelta(days=7),
            location='Test Field'
        )
        
        self.future_match = Event.objects.create(
            name='Test Match',
            description='A test match',
            event_type='wedstrijd',
            date=timezone.now() + timedelta(days=14),
            location='Test Stadium'
        )
        
        self.client.login(username='testuser', password='testpass123')
    
    def test_event_list_view_loads(self):
        """Test event list page loads correctly"""
        response = self.client.get(reverse('events:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Training')
        self.assertContains(response, 'Test Match')
    
    def test_event_list_shows_matches(self):
        """Test event list displays match events"""
        response = self.client.get(reverse('events:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'wedstrijd')
    
    def test_event_detail_view(self):
        """Test individual event detail view"""
        response = self.client.get(
            reverse('events:detail', kwargs={'pk': self.future_event.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Training')
        self.assertContains(response, 'Test Field')
    
    def test_event_list_requires_authentication(self):
        """Test event list requires user to be logged in"""
        self.client.logout()
        response = self.client.get(reverse('events:list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class MatchCreateTestCase(TestCase):
    """Test match/event creation functionality"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_staff_can_create_match(self):
        """Test staff users can create matches"""
        self.client.login(username='staffuser', password='staffpass123')
        
        future_date = timezone.now() + timedelta(days=7)
        response = self.client.post(reverse('events:create'), {
            'name': 'New Test Match',
            'description': 'A newly created match',
            'event_type': 'wedstrijd',
            'date': future_date.strftime('%d/%m/%Y %H:%M'),  # Use dd/mm/yyyy format
            'location': 'Stadium',
            'is_mandatory': True,
            'max_participants': 22
        })
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Verify event was created
        event = Event.objects.filter(name='New Test Match').first()
        self.assertIsNotNone(event)
        self.assertEqual(event.event_type, 'wedstrijd')
        self.assertTrue(event.is_match)
    
    def test_regular_user_cannot_create_match(self):
        """Test regular users cannot create matches"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('events:create'))
        self.assertEqual(response.status_code, 302)  # Should redirect/deny access
    
    def test_match_properties(self):
        """Test match-specific properties and methods"""
        match = Event.objects.create(
            name='Test Match',
            event_type='wedstrijd',
            date=timezone.now() + timedelta(days=1),
            location='Stadium'
        )
        
        self.assertTrue(match.is_match)
        self.assertTrue(match.is_upcoming)
        self.assertEqual(match.get_attendance_count(), 0)
        self.assertEqual(match.get_attendance_rate(), 0)


class MatchStatisticsTestCase(TestCase):
    """Test match statistics functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testplayer',
            email='player@example.com',
            password='testpass123'
        )
        
        self.match = Event.objects.create(
            name='Test Match',
            event_type='wedstrijd',
            date=timezone.now() + timedelta(days=1),
            location='Stadium'
        )
        
        self.training = Event.objects.create(
            name='Test Training',
            event_type='training',
            date=timezone.now() + timedelta(days=1),
            location='Field'
        )
    
    def test_match_statistics_creation(self):
        """Test creating match statistics"""
        stat = MatchStatistic.objects.create(
            event=self.match,
            player=self.user,
            statistic_type='goal',
            value=2,
            minute=45
        )
        
        self.assertEqual(stat.value, 2)
        self.assertEqual(stat.minute, 45)
        self.assertEqual(stat.statistic_type, 'goal')
    
    def test_attendance_tracking(self):
        """Test basic attendance functionality"""
        # Create attendance record
        attendance = Attendance.objects.create(
            user=self.user,
            event=self.match,
            present=True
        )
        
        self.assertTrue(attendance.present)
        self.assertEqual(self.match.get_attendance_count(), 1)
        self.assertEqual(self.match.get_user_attendance_status(self.user), True)
