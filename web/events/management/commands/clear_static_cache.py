import os

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clear browser cache for static files by touching all static files to update their modification time"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what files would be touched without actually touching them",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        touched_files = 0

        # Get static directories
        static_dirs = []

        if hasattr(settings, "STATICFILES_DIRS") and settings.STATICFILES_DIRS:
            static_dirs.extend(settings.STATICFILES_DIRS)

        if hasattr(settings, "STATIC_ROOT") and settings.STATIC_ROOT:
            static_dirs.append(settings.STATIC_ROOT)

        if not static_dirs:
            self.stdout.write(
                self.style.WARNING("No static directories found in settings")
            )
            return

        for static_dir in static_dirs:
            if not os.path.exists(static_dir):
                self.stdout.write(
                    self.style.WARNING(f"Static directory does not exist: {static_dir}")
                )
                continue

            self.stdout.write(f"Processing static directory: {static_dir}")

            # Find all static files
            for root, _dirs, files in os.walk(static_dir):
                for file in files:
                    # Skip certain file types that shouldn't be cached
                    if file.endswith((".pyc", ".pyo", ".log", ".tmp")):
                        continue

                    file_path = os.path.join(root, file)

                    if dry_run:
                        self.stdout.write(f"  Would touch: {file_path}")
                    else:
                        try:
                            # Touch the file to update modification time
                            os.utime(file_path, None)
                            self.stdout.write(f"  Touched: {file_path}")
                        except OSError as e:
                            self.stdout.write(
                                self.style.ERROR(f"  Error touching {file_path}: {e}")
                            )
                            continue

                    touched_files += 1

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"Would touch {touched_files} static files")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully touched {touched_files} static files")
            )
            self.stdout.write(
                "Static file cache busting is now active. "
                "All static files will have new version hashes."
            )
