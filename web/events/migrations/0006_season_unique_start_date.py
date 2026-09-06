from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("events", "0005_season_event_season")]
    operations = [
        migrations.AddConstraint(
            model_name="season",
            constraint=models.UniqueConstraint(
                fields=("start_date",), name="unique_season_start_date"
            ),
        )
    ]
