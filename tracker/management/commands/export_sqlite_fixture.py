import json
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections


class Command(BaseCommand):
    help = 'Export all data from a local SQLite file into a JSON fixture for Docker/PostgreSQL import.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sqlite',
            default='db.sqlite3',
            help='Path to SQLite file (default: db.sqlite3 in project root)',
        )
        parser.add_argument(
            '--output',
            default='fixtures/sqlite_export.json',
            help='Output JSON fixture path',
        )

    def handle(self, *args, **options):
        sqlite_path = Path(options['sqlite'])
        if not sqlite_path.is_absolute():
            sqlite_path = Path(settings.BASE_DIR) / sqlite_path

        if not sqlite_path.exists():
            raise CommandError(f'SQLite file not found: {sqlite_path}')

        output_path = Path(options['output'])
        if not output_path.is_absolute():
            output_path = Path(settings.BASE_DIR) / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        connections.close_all()
        settings.DATABASES['default'] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': sqlite_path,
        }

        buffer = StringIO()
        call_command(
            'dumpdata',
            exclude=['contenttypes', 'auth.permission'],
            natural_foreign=True,
            natural_primary=True,
            indent=2,
            stdout=buffer,
        )

        payload = buffer.getvalue()
        if not payload.strip():
            raise CommandError('Export is empty — check that SQLite contains data.')

        output_path.write_text(payload, encoding='utf-8')
        record_count = payload.count('"model":')
        self.stdout.write(
            self.style.SUCCESS(
                f'Exported ~{record_count} records to {output_path}'
            )
        )
