from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Train LSTM models until quality gate passes (see scripts/train_models_until_gate.py).'

    def add_arguments(self, parser):
        parser.add_argument('--only', nargs='*', help='Tickers to train, e.g. SOL LTC')

    def handle(self, *args, **options):
        import subprocess
        import sys
        from pathlib import Path

        cmd = [sys.executable, str(Path('scripts') / 'train_models_until_gate.py')]
        if options.get('only'):
            cmd.extend(['--only', *options['only']])
        subprocess.check_call(cmd)
