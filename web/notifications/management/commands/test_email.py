from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Test email configuration by sending a test email"

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            type=str,
            required=True,
            help="Email address to send the test email to",
        )

    def handle(self, *args, **options):
        to_email = options["to"]

        self.stdout.write(
            self.style.SUCCESS(f"Attempting to send test email to: {to_email}")
        )

        try:
            send_mail(
                subject="SV Rap 8 - Test Email",
                message="This is a test email from the SV Rap 8 notification system.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )

            self.stdout.write(
                self.style.SUCCESS(f"Test email successfully sent to {to_email}")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send test email: {str(e)}"))
