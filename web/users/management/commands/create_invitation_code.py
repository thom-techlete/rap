from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from users.models import InvitationCode


class Command(BaseCommand):
    help = "Create invitation codes for user registration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--code",
            type=str,
            help="Specific code to create (if not provided, a random code will be generated)",
        )
        parser.add_argument(
            "--description", type=str, help="Description for the invitation code"
        )
        parser.add_argument(
            "--max-uses", type=int, help="Maximum number of times this code can be used"
        )
        parser.add_argument(
            "--expires-in-days", type=int, help="Number of days until the code expires"
        )
        parser.add_argument(
            "--count",
            type=int,
            default=1,
            help="Number of codes to create (default: 1)",
        )

    def handle(self, *args, **options):
        count = options["count"]
        created_codes = []

        for i in range(count):
            # Prepare kwargs for code creation
            code_kwargs = {}

            if options["code"]:
                if count > 1:
                    raise CommandError(
                        "Cannot specify a specific code when creating multiple codes"
                    )
                code_kwargs["code"] = options["code"]

            if options["description"]:
                if count > 1:
                    code_kwargs["description"] = f"{options['description']} ({i+1})"
                else:
                    code_kwargs["description"] = options["description"]

            if options["max_uses"]:
                code_kwargs["max_uses"] = options["max_uses"]

            if options["expires_in_days"]:
                code_kwargs["expires_at"] = timezone.now() + timedelta(
                    days=options["expires_in_days"]
                )

            try:
                invitation_code = InvitationCode.objects.create(**code_kwargs)
                created_codes.append(invitation_code)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created invitation code: {invitation_code.code}"
                    )
                )

                if invitation_code.description:
                    self.stdout.write(f"  Description: {invitation_code.description}")

                if invitation_code.max_uses:
                    self.stdout.write(f"  Max uses: {invitation_code.max_uses}")

                if invitation_code.expires_at:
                    local_expires = timezone.localtime(invitation_code.expires_at)
                    self.stdout.write(
                        f'  Expires: {local_expires.strftime("%Y-%m-%d %H:%M")}'
                    )

                self.stdout.write("")  # Empty line for spacing

            except Exception as e:
                raise CommandError(f"Error creating invitation code: {e}") from e

        if count > 1:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {len(created_codes)} invitation codes"
                )
            )
