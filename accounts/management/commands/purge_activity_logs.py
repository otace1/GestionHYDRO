import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import UserActivityLog

class Command(BaseCommand):
    help = 'Purge UserActivityLog records older than 90 days (or specified days)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days of logs to keep (default: 90)'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff = timezone.now() - datetime.timedelta(days=days)
        
        count, _ = UserActivityLog.objects.filter(timestamp__lt=cutoff).delete()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} log entries older than {days} days.'))
