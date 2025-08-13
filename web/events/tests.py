# # Create your tests here.
# from django.test import TestCase
# from django.urls import reverse
# from django.contrib.auth import get_user_model
# from django.utils import timezone
# from datetime import timedelta

# from .models import Event
# from attendance.models import Attendance

# User = get_user_model()


# class EventDetailViewTest(TestCase):
#     def setUp(self):
#         """Set up test data"""
#         self.user = User.objects.create_user(
#             username='testuser',
#             email='test@example.com',
#             password='testpass123'
#         )
#         self.staff_user = User.objects.create_user(
#             username='staffuser',
#             email='staff@example.com',
#             password='staffpass123',
#             is_staff=True
#         )

#         # Create a future event
#         self.future_event = Event.objects.create(
#             name='Test Training',
#             description='A test training session',
#             event_type='training',
#             date=timezone.now() + timedelta(days=7),
#             location='Test Field'
#         )

#         # Create a past event
#         self.past_event = Event.objects.create(
#             name='Past Game',
#             description='A past game',
#             event_type='wedstrijd',
#             date=timezone.now() - timedelta(days=7),
#             location='Test Stadium'
#         )

#     def test_event_detail_view_accessible(self):
#         """Test that event detail view is accessible"""
#         url = reverse('events:detail', kwargs={'pk': self.future_event.pk})
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, self.future_event.name)
#         self.assertContains(response, 'Evenement details')

#     def test_event_detail_view_with_authenticated_user(self):
#         """Test event detail view with authenticated user"""
#         self.client.login(username='testuser', password='testpass123')
#         url = reverse('events:detail', kwargs={'pk': self.future_event.pk})
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#         # Should show attendance buttons for upcoming events
#         if self.future_event.is_upcoming:
#             self.assertContains(response, 'Jouw aanwezigheid')

#     def test_event_detail_view_with_staff_user(self):
#         """Test event detail view with staff user"""
#         self.client.login(username='staffuser', password='staffpass123')
#         url = reverse('events:detail', kwargs={'pk': self.future_event.pk})
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#         # Should show staff actions
#         self.assertContains(response, 'Bewerk evenement')

#     def test_event_detail_with_attendance_data(self):
#         """Test event detail view shows attendance data correctly"""
#         # Create attendance record
#         Attendance.objects.create(
#             user=self.user,
#             event=self.future_event,
#             present=True
#         )

#         url = reverse('events:detail', kwargs={'pk': self.future_event.pk})
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, 'Spelers aanwezigheid')
#         # Should show attendance stats
#         self.assertContains(response, 'Aanwezig')

#     def test_event_detail_nonexistent_event(self):
#         """Test accessing detail for non-existent event returns 404"""
#         url = reverse('events:detail', kwargs={'pk': 9999})
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 404)

#     def test_event_absolute_url_points_to_detail(self):
#         """Test that event's get_absolute_url points to detail view"""
#         expected_url = reverse('events:detail', kwargs={'pk': self.future_event.pk})
#         self.assertEqual(self.future_event.get_absolute_url(), expected_url)
