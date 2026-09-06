from datetime import UTC, datetime, timedelta

from attendance.models import Attendance
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .dashboard_views import calculate_match_statistics, calculate_player_rankings
from .forms import EventForm
from .models import Event, MatchStatistic, Season
from .seasoning import get_season_for_datetime, get_selected_season

User = get_user_model()


class SeasonDomainTestCase(TestCase):
    def setUp(self):
        self.archived = Season.objects.get(name="2025–2026")
        self.active = Season.objects.get(name="2026–2027")

    def test_active_season_and_boundaries(self):
        self.assertEqual(Season.get_active(), self.active)
        self.assertTrue(
            self.archived.contains(timezone.make_aware(datetime(2026, 7, 31, 23, 59)))
        )
        self.assertFalse(
            self.archived.contains(timezone.make_aware(datetime(2026, 8, 1)))
        )
        self.assertTrue(self.active.contains(timezone.make_aware(datetime(2026, 8, 1))))

    def test_only_one_active_season_is_allowed(self):
        with self.assertRaises(ValidationError):
            Season.objects.create(
                name="Dubbel",
                start_date="2027-08-01",
                end_date="2028-08-01",
                is_active=True,
            )

    def test_event_defaults_to_active_and_protects_season(self):
        event = Event.objects.create(name="Nieuw", date=timezone.now())
        self.assertEqual(event.season, self.active)
        with self.assertRaises(ProtectedError):
            self.active.delete()

    def test_selected_season_and_datetime_lookup(self):
        request = self.client.get("/").wsgi_request
        self.assertEqual(get_selected_season(request), self.active)
        request.GET = {"season": str(self.archived.pk)}
        self.assertEqual(get_selected_season(request), self.archived)
        self.assertEqual(
            get_season_for_datetime(timezone.make_aware(datetime(2026, 8, 1))),
            self.active,
        )
        self.assertEqual(
            get_season_for_datetime(datetime(2026, 7, 31, 22, 30, tzinfo=UTC)),
            self.active,
        )

    def test_event_form_defaults_to_active_and_rejects_unknown_date(self):
        form = EventForm()
        self.assertEqual(form.initial["season"], self.active)
        data = {
            "name": "Oud evenement",
            "event_type": "training",
            "date": "01/01/2030 12:00",
            "season": self.active.pk,
            "recurrence_type": "none",
        }
        self.assertFalse(EventForm(data).is_valid())
        self.assertIn("bekend seizoen", str(EventForm(data).errors))

    def test_seasons_must_start_on_first_of_august(self):
        with self.assertRaises(ValidationError):
            Season.objects.create(
                name="Ongeldig", start_date="2026-01-01", end_date="2027-01-01"
            )

    def test_direct_event_save_rejects_unknown_date(self):
        with self.assertRaises(ValidationError):
            Event.objects.create(name="Ver buiten seizoen", date=datetime(2030, 1, 1))

    def test_dashboard_calculations_are_isolated_by_season(self):
        player = User.objects.create_user(username="season-player")
        old_match = Event.objects.create(
            name="Oude wedstrijd",
            event_type="wedstrijd",
            date=timezone.make_aware(datetime(2026, 7, 1)),
            season=self.archived,
        )
        new_match = Event.objects.create(
            name="Nieuwe wedstrijd",
            event_type="wedstrijd",
            date=timezone.make_aware(datetime(2026, 8, 15)),
            season=self.active,
        )
        Attendance.objects.create(user=player, event=old_match, present=True)
        Attendance.objects.create(user=player, event=new_match, present=False)
        MatchStatistic.objects.create(
            event=old_match, player=player, statistic_type="goal", value=3
        )
        MatchStatistic.objects.create(
            event=new_match, player=player, statistic_type="goal", value=1
        )

        self.assertEqual(calculate_match_statistics(self.archived)["total_goals"], 3)
        self.assertEqual(calculate_match_statistics(self.active)["total_goals"], 1)
        self.assertEqual(
            calculate_player_rankings(self.archived)[0]["present_count"], 1
        )
        self.assertEqual(calculate_player_rankings(self.active)[0]["present_count"], 0)
        self.assertEqual(Attendance.objects.count(), 2)
        self.assertEqual(MatchStatistic.objects.count(), 2)

    def test_recurring_events_cannot_cross_seasons(self):
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            Event.create_recurring_events(
                {"name": "Zomer", "date": timezone.make_aware(datetime(2026, 7, 25))},
                "weekly",
                datetime(2026, 8, 15).date(),
            )

    def test_event_list_and_attendance_dashboard_use_selected_season(self):
        user = User.objects.create_user(username="season-viewer", password="test")
        self.client.login(username="season-viewer", password="test")
        old_event = Event.objects.create(
            name="Archief evenement",
            date=timezone.make_aware(datetime(2026, 7, 1)),
            season=self.archived,
        )
        Event.objects.create(
            name="Actief evenement",
            date=timezone.make_aware(datetime(2026, 8, 15)),
            season=self.active,
        )
        Attendance.objects.create(user=user, event=old_event, present=True)

        response = self.client.get("/events/")
        self.assertNotContains(response, "Archief evenement")
        response = self.client.get(f"/events/?season={self.archived.pk}")
        self.assertContains(response, "Archief evenement")
        response = self.client.get(f"/attendance/dashboard/?season={self.archived.pk}")
        self.assertEqual(response.context["total_events"], 1)


class EventListTestCase(TestCase):
    """Test event listing functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create test events
        self.future_event = Event.objects.create(
            name="Test Training",
            description="A test training session",
            event_type="training",
            date=timezone.now() + timedelta(days=7),
            location="Test Field",
        )

        self.future_match = Event.objects.create(
            name="Test Match",
            description="A test match",
            event_type="wedstrijd",
            date=timezone.now() + timedelta(days=14),
            location="Test Stadium",
        )

        self.client.login(username="testuser", password="testpass123")

    def test_event_list_view_loads(self):
        """Test event list page loads correctly"""
        response = self.client.get(reverse("events:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Training")
        self.assertContains(response, "Test Match")

    def test_event_list_shows_matches(self):
        """Test event list displays match events"""
        response = self.client.get(reverse("events:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "wedstrijd")

    def test_event_detail_view(self):
        """Test individual event detail view"""
        response = self.client.get(
            reverse("events:detail", kwargs={"pk": self.future_event.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Training")
        self.assertContains(response, "Test Field")

    def test_event_list_requires_authentication(self):
        """Test event list requires user to be logged in"""
        self.client.logout()
        response = self.client.get(reverse("events:list"))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class MatchCreateTestCase(TestCase):
    """Test match/event creation functionality"""

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="staffpass123",
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_staff_can_create_match(self):
        """Test staff users can create matches"""
        self.client.login(username="staffuser", password="staffpass123")

        future_date = timezone.now() + timedelta(days=7)
        response = self.client.post(
            reverse("events:create"),
            {
                "name": "New Test Match",
                "description": "A newly created match",
                "event_type": "wedstrijd",
                "date": future_date.strftime("%d/%m/%Y %H:%M"),  # Use dd/mm/yyyy format
                "location": "Stadium",
                "is_mandatory": True,
                "max_participants": 22,
            },
        )

        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)

        # Verify event was created
        event = Event.objects.filter(name="New Test Match").first()
        self.assertIsNotNone(event)
        self.assertEqual(event.event_type, "wedstrijd")
        self.assertTrue(event.is_match)

    def test_regular_user_cannot_create_match(self):
        """Test regular users cannot create matches"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("events:create"))
        self.assertEqual(response.status_code, 302)  # Should redirect/deny access

    def test_match_properties(self):
        """Test match-specific properties and methods"""
        match = Event.objects.create(
            name="Test Match",
            event_type="wedstrijd",
            date=timezone.now() + timedelta(days=1),
            location="Stadium",
        )

        self.assertTrue(match.is_match)
        self.assertTrue(match.is_upcoming)
        self.assertEqual(match.get_attendance_count(), 0)
        self.assertEqual(match.get_attendance_rate(), 0)


class MatchStatisticsTestCase(TestCase):
    """Test match statistics functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testplayer", email="player@example.com", password="testpass123"
        )

        self.match = Event.objects.create(
            name="Test Match",
            event_type="wedstrijd",
            date=timezone.now() + timedelta(days=1),
            location="Stadium",
        )

        self.training = Event.objects.create(
            name="Test Training",
            event_type="training",
            date=timezone.now() + timedelta(days=1),
            location="Field",
        )

    def test_match_statistics_creation(self):
        """Test creating match statistics"""
        stat = MatchStatistic.objects.create(
            event=self.match,
            player=self.user,
            statistic_type="goal",
            value=2,
            minute=45,
        )

        self.assertEqual(stat.value, 2)
        self.assertEqual(stat.minute, 45)
        self.assertEqual(stat.statistic_type, "goal")

    def test_attendance_tracking(self):
        """Test basic attendance functionality"""
        # Create attendance record
        attendance = Attendance.objects.create(
            user=self.user, event=self.match, present=True
        )

        self.assertTrue(attendance.present)
        self.assertEqual(self.match.get_attendance_count(), 1)
        self.assertEqual(self.match.get_user_attendance_status(self.user), True)
