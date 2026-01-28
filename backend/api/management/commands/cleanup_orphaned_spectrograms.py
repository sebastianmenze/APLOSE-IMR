"""
Django management command to clean up orphaned spectrograms

Removes Spectrogram records that are not linked to any analysis.

Usage:
    python manage.py cleanup_orphaned_spectrograms [--dry-run]

Examples:
    # Preview what would be deleted
    python manage.py cleanup_orphaned_spectrograms --dry-run

    # Actually delete orphaned spectrograms
    python manage.py cleanup_orphaned_spectrograms
"""

import logging
from django.core.management.base import BaseCommand
from backend.api.models import Spectrogram

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up orphaned spectrograms (not linked to any analysis)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.MIGRATE_HEADING('='*70))
        self.stdout.write(self.style.MIGRATE_HEADING('Cleanup Orphaned Spectrograms'))
        self.stdout.write(self.style.MIGRATE_HEADING('='*70))
        self.stdout.write('')

        # Find spectrograms with no linked analyses
        orphaned = Spectrogram.objects.filter(analysis__isnull=True)
        count = orphaned.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('✓ No orphaned spectrograms found'))
            return

        self.stdout.write(f"Found {count} orphaned spectrograms:")
        self.stdout.write('')

        # Show some examples
        for spec in orphaned[:10]:
            self.stdout.write(f"  - {spec.filename} ({spec.start} - {spec.end})")

        if count > 10:
            self.stdout.write(f"  ... and {count - 10} more")

        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"⚠ DRY RUN: Would delete {count} orphaned spectrograms"
            ))
            self.stdout.write("Run without --dry-run to actually delete them")
        else:
            deleted_count, _ = orphaned.delete()
            self.stdout.write(self.style.SUCCESS(
                f"✓ Deleted {deleted_count} orphaned spectrograms"
            ))
