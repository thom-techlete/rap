import random
from datetime import timedelta

from attendance.models import Attendance
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import Player

from events.models import Event


class Command(BaseCommand):
    help = "Populate the database with sample events and attendance data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing events before creating new ones",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            Event.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared all existing events"))

        # Create sample events
        now = timezone.now()

        events_data = [
            {
                "name": "Wekelijkse Training",
                "description": "Reguliere training met focus op techniek en conditie",
                "event_type": "training",
                "date": now + timedelta(days=2, hours=19),
                "location": "Hoofdveld SV Rap 8",
                "is_mandatory": True,
            },
            {
                "name": "Wedstrijd tegen FC Rivalen",
                "description": "Belangrijke thuiswedstrijd in de competitie",
                "event_type": "wedstrijd",
                "date": now + timedelta(days=7, hours=14, minutes=30),
                "location": "Hoofdveld SV Rap 8",
                "is_mandatory": True,
            },
            {
                "name": "Training Tactiek",
                "description": "Speciale training gericht op tactische aspecten",
                "event_type": "training",
                "date": now + timedelta(days=5, hours=19, minutes=30),
                "location": "Trainingsveld A",
                "is_mandatory": False,
            },
            {
                "name": "Teambuilding BBQ",
                "description": "Gezellig teamuitje met barbecue en spelletjes",
                "event_type": "uitje",
                "date": now + timedelta(days=14, hours=17),
                "location": "Clubhuis SV Rap 8",
                "is_mandatory": False,
                "max_participants": 25,
            },
            {
                "name": "Uitwedstrijd FC Buren",
                "description": "Lastige uitwedstrijd tegen de koploper",
                "event_type": "wedstrijd",
                "date": now + timedelta(days=21, hours=15),
                "location": "Sportpark De Buren",
                "is_mandatory": True,
            },
            {
                "name": "Keeperstraining",
                "description": "Speciale training voor keepers",
                "event_type": "training",
                "date": now + timedelta(days=9, hours=18),
                "location": "Trainingsveld B",
                "is_mandatory": False,
            },
            {
                "name": "Teamvergadering",
                "description": "Bespreking van de seizoensresultaten en plannen",
                "event_type": "vergadering",
                "date": now + timedelta(days=28, hours=20),
                "location": "Clubhuis SV Rap 8",
                "is_mandatory": True,
            },
        ]

        # Past events for history
        past_events_data = [
            {
                "name": "Training Afgelopen Week",
                "description": "Vorige week training",
                "event_type": "training",
                "date": now - timedelta(days=3, hours=19),
                "location": "Hoofdveld SV Rap 8",
                "is_mandatory": True,
            },
            {
                "name": "Gewonnen Wedstrijd",
                "description": "Mooie overwinning tegen FC Buurman",
                "event_type": "wedstrijd",
                "date": now - timedelta(days=7, hours=14, minutes=30),
                "location": "Hoofdveld SV Rap 8",
                "is_mandatory": True,
            },
            {
                "name": "Vorige Training",
                "description": "Training van twee weken geleden",
                "event_type": "training",
                "date": now - timedelta(days=10, hours=19),
                "location": "Hoofdveld SV Rap 8",
                "is_mandatory": True,
            },
        ]

        all_events = events_data + past_events_data
        created_events = []

        for event_data in all_events:
            event = Event.objects.create(**event_data)
            created_events.append(event)
            self.stdout.write(
                f'Created event: {event.name} on {event.date.strftime("%d-%m-%Y %H:%M")}'
            )

        # Create sample attendance for past events if there are users
        users = Player.objects.all()
        if users.exists():
            for event in created_events:
                if event.date < now:  # Only for past events
                    for user in users:
                        # Simulate realistic attendance patterns
                        present = random.choice(
                            [True, True, True, False]
                        )  # 75% attendance rate
                        Attendance.objects.create(
                            user=user, event=event, present=present
                        )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created sample attendance for {users.count()} users"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {len(created_events)} events")
        )
