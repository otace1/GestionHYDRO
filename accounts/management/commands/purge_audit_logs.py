import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from accounts.models import AuditLog

class Command(BaseCommand):
    help = 'Purge AuditLog records older than specified days in settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=getattr(settings, 'AUDIT_LOG_RETENTION_DAYS', 90),
            help='Number of days of logs to keep'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff = timezone.now() - datetime.timedelta(days=days)
        
        count, _ = AuditLog.objects.filter(timestamp__lt=cutoff).delete()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} audit log entries older than {days} days.'))
