# Create your models here.
from django.contrib.auth import get_user_model
from django.db import models
from events.models import Event


class Attendance(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    present = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["event", "present"])]

    def __str__(self):
        return (
            f"{self.user} - {self.event} - {'Aanwezig' if self.present else 'Afwezig'}"
        )
