from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("attendance", "0002_initial")]

    operations = [
        migrations.AddIndex(
            model_name="attendance",
            index=models.Index(
                fields=("event", "present"), name="attendance__event_i_b188bd_idx"
            ),
        ),
    ]
