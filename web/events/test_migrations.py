from datetime import datetime

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class SeasonBackfillMigrationTestCase(TransactionTestCase):
    """Keep the legacy-date backfill and related-row preservation executable."""

    # This test intentionally uses the real migration rather than the test
    # runner's migrated schema, so it exercises the production upgrade path.
    migrate_from = ("events", "0004_matchstatistic")
    migrate_to = ("events", "0008_season_exact_year_check")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.executor = MigrationExecutor(connection)
        cls.executor.migrate([cls.migrate_from])
        old_apps = cls.executor.loader.project_state([cls.migrate_from]).apps
        Event = old_apps.get_model("events", "Event")
        MatchStatistic = old_apps.get_model("events", "MatchStatistic")
        from attendance.models import Attendance
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(
            username="migration-player", password="test", huisnummer=""
        )
        cls.may_event = Event.objects.create(
            name="Mei 2025", date=timezone.make_aware(datetime(2025, 6, 1))
        )
        cls.boundary_event = Event.objects.create(
            name="Start nieuw seizoen", date=timezone.make_aware(datetime(2025, 8, 1))
        )
        Attendance.objects.create(
            user_id=user.pk, event_id=cls.may_event.pk, present=True
        )
        MatchStatistic.objects.create(
            event=cls.boundary_event,
            player_id=user.pk,
            statistic_type="goal",
            value=2,
        )
        # Rebuild the loader after rolling back from the test runner's leaf;
        # this ensures the forward migration is planned from the real DB state.
        cls.executor = MigrationExecutor(connection)
        cls.executor.migrate([cls.migrate_to])

    def test_backfill_preserves_rows_and_assigns_boundaries(self):
        apps = self.executor.loader.project_state([self.migrate_to]).apps
        Season = apps.get_model("events", "Season")
        Event = apps.get_model("events", "Event")
        from attendance.models import Attendance

        from events.models import MatchStatistic

        self.assertEqual(Event.objects.get(name="Mei 2025").season.name, "2024–2025")
        self.assertEqual(
            Event.objects.get(name="Start nieuw seizoen").season.name, "2025–2026"
        )
        self.assertEqual(Attendance.objects.count(), 1)
        self.assertEqual(MatchStatistic.objects.count(), 1)
        self.assertTrue(Season.objects.get(name="2026–2027").is_active)
