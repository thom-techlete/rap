from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("events", "0007_season_august_boundary_checks")]
    operations = [
        migrations.AddConstraint(
            model_name="season",
            constraint=models.CheckConstraint(
                condition=models.Q(end_date__year=models.F("start_date__year") + 1),
                name="season_is_exactly_one_year",
            ),
        )
    ]
