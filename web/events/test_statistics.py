from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from events.models import Event, MatchStatistic

User = get_user_model()


class MatchStatisticsTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.player = User.objects.create_user(
            username='player1',
            email='player1@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )

        # Create a past match
        self.past_match = Event.objects.create(
            name='Test Match',
            description='A test match',
            event_type='wedstrijd',
            date=timezone.now() - timedelta(days=1),
            location='Test Stadium'
        )

        # Create a training (non-match)
        self.training = Event.objects.create(
            name='Test Training',
            description='A test training',
            event_type='training',
            date=timezone.now() + timedelta(days=1),
            location='Test Field'
        )

        self.client = Client()

    def test_event_is_match_property(self):
        """Test that event.is_match property works correctly"""
        self.assertTrue(self.past_match.is_match)
        self.assertFalse(self.training.is_match)

    def test_match_statistic_creation(self):
        """Test creating match statistics"""
        stat = MatchStatistic.objects.create(
            event=self.past_match,
            player=self.player,
            statistic_type='goal',
            value=2,
            minute=45,
            created_by=self.staff_user
        )
        
        self.assertEqual(stat.event, self.past_match)
        self.assertEqual(stat.player, self.player)
        self.assertEqual(stat.statistic_type, 'goal')
        self.assertEqual(stat.value, 2)
        self.assertEqual(stat.minute, 45)
        self.assertEqual(str(stat), "player1 (John Doe) - Doelpunt (45') - Test Match")

    def test_match_statistic_clean_validation(self):
        """Test that statistics can only be added to match events"""
        from django.core.exceptions import ValidationError
        
        stat = MatchStatistic(
            event=self.training,  # This is a training, not a match
            player=self.player,
            statistic_type='goal',
            value=1,
            created_by=self.staff_user
        )
        
        with self.assertRaises(ValidationError):
            stat.clean()

    def test_event_detail_shows_statistics_for_matches(self):
        """Test that event detail view shows statistics for matches"""
        # Create a statistic
        MatchStatistic.objects.create(
            event=self.past_match,
            player=self.player,
            statistic_type='goal',
            value=1,
            minute=30,
            created_by=self.staff_user
        )

        # Login as staff to see the form
        self.client.login(username='staffuser', password='testpass123')
        
        url = reverse('events:detail', kwargs={'pk': self.past_match.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wedstrijd Statistieken')
        self.assertContains(response, 'Doelpunt')
        self.assertContains(response, 'John Doe')

    def test_event_detail_no_statistics_for_training(self):
        """Test that event detail view doesn't show statistics for non-matches"""
        url = reverse('events:detail', kwargs={'pk': self.training.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Wedstrijd Statistieken')

    def test_staff_can_add_statistics(self):
        """Test that staff users can add statistics"""
        self.client.login(username='staffuser', password='testpass123')
        
        url = reverse('events:detail', kwargs={'pk': self.past_match.pk})
        response = self.client.post(url, {
            'add_statistic': '1',
            'player': self.player.pk,
            'statistic_type': 'goal',
            'value': '1',
            'minute': '25',
            'notes': 'Great goal!'
        })
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check that statistic was created
        stat = MatchStatistic.objects.get(event=self.past_match, player=self.player)
        self.assertEqual(stat.statistic_type, 'goal')
        self.assertEqual(stat.value, 1)
        self.assertEqual(stat.minute, 25)
        self.assertEqual(stat.notes, 'Great goal!')

    def test_non_staff_cannot_add_statistics(self):
        """Test that non-staff users cannot add statistics"""
        # Login as regular player
        self.client.login(username='player1', password='testpass123')
        
        url = reverse('events:detail', kwargs={'pk': self.past_match.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should not contain the statistics form
        self.assertNotContains(response, 'Statistiek toevoegen')

    def test_delete_statistic(self):
        """Test that staff can delete statistics"""
        stat = MatchStatistic.objects.create(
            event=self.past_match,
            player=self.player,
            statistic_type='goal',
            value=1,
            minute=30,
            created_by=self.staff_user
        )
        
        self.client.login(username='staffuser', password='testpass123')
        
        url = reverse('events:delete_statistic', kwargs={
            'pk': self.past_match.pk,
            'stat_id': stat.pk
        })
        response = self.client.post(url)
        
        # Should redirect after deletion
        self.assertEqual(response.status_code, 302)
        
        # Check that statistic was deleted
        self.assertFalse(MatchStatistic.objects.filter(pk=stat.pk).exists())

    def test_dashboard_statistics_calculation(self):
        """Test that dashboard statistics are calculated correctly"""
        from events.dashboard_views import calculate_match_statistics
        
        # Create some statistics
        MatchStatistic.objects.create(
            event=self.past_match,
            player=self.player,
            statistic_type='goal',
            value=2,
            created_by=self.staff_user
        )
        
        MatchStatistic.objects.create(
            event=self.past_match,
            player=self.player,
            statistic_type='assist',
            value=1,
            created_by=self.staff_user
        )
        
        MatchStatistic.objects.create(
            event=self.past_match,
            player=self.player,
            statistic_type='yellow_card',
            value=1,
            created_by=self.staff_user
        )
        
        stats = calculate_match_statistics()
        
        self.assertEqual(stats['total_matches'], 1)
        self.assertEqual(stats['total_goals'], 2)
        self.assertEqual(stats['total_assists'], 1)
        self.assertEqual(stats['total_cards'], 1)
        self.assertEqual(len(stats['top_goalscorers']), 1)
        self.assertEqual(stats['top_goalscorers'][0]['total_goals'], 2)