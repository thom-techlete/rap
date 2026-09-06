from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("events", "0006_season_unique_start_date")]
    operations = [
        migrations.AddConstraint(
            model_name="season",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    start_date__month=8,
                    start_date__day=1,
                    end_date__month=8,
                    end_date__day=1,
                ),
                name="season_dates_on_august_first",
            ),
        )
    ]
