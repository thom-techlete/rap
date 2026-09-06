from datetime import date

import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


def create_seasons_and_backfill(apps, schema_editor):
    Season = apps.get_model("events", "Season")
    Event = apps.get_model("events", "Event")

    seasons = {
        "2024–2025": Season.objects.create(
            name="2024–2025", start_date=date(2024, 8, 1), end_date=date(2025, 8, 1)
        ),
        "2025–2026": Season.objects.create(
            name="2025–2026", start_date=date(2025, 8, 1), end_date=date(2026, 8, 1)
        ),
        "2026–2027": Season.objects.create(
            name="2026–2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 8, 1),
            is_active=True,
        ),
    }

    for event in Event.objects.all().only("id", "date"):
        event_date = timezone.localdate(event.date)
        season = next(
            (s for s in seasons.values() if s.start_date <= event_date < s.end_date),
            None,
        )
        if season is None:
            start_year = (
                event_date.year if event_date.month >= 8 else event_date.year - 1
            )
            start_date = date(start_year, 8, 1)
            season, _ = Season.objects.get_or_create(
                name=f"{start_year}\u2013{start_year + 1}",
                defaults={
                    "start_date": start_date,
                    "end_date": date(start_year + 1, 8, 1),
                },
            )
        Event.objects.filter(pk=event.pk).update(season_id=season.pk)


class Migration(migrations.Migration):
    dependencies = [("events", "0004_matchstatistic")]

    operations = [
        migrations.CreateModel(
            name="Season",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=20, unique=True, verbose_name="Seizoen"
                    ),
                ),
                ("start_date", models.DateField(verbose_name="Startdatum")),
                ("end_date", models.DateField(verbose_name="Einddatum")),
                (
                    "is_active",
                    models.BooleanField(default=False, verbose_name="Actief seizoen"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["start_date"],
                "verbose_name": "Seizoen",
                "verbose_name_plural": "Seizoenen",
            },
        ),
        migrations.AddConstraint(
            model_name="season",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True),
                fields=("is_active",),
                name="only_one_active_season",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="season",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="events",
                to="events.season",
                verbose_name="Seizoen",
            ),
        ),
        migrations.RunPython(create_seasons_and_backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="event",
            name="season",
            field=models.ForeignKey(
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="events",
                to="events.season",
                verbose_name="Seizoen",
            ),
        ),
    ]
