from celery import shared_task
from django.utils import timezone
import datetime
from django.conf import settings
from .models import AuditLog, UserActivityLog, MyUser
from .services import log_action

@shared_task(bind=True)
def purge_old_logs(self, days=90, user_id=None):
    """
    Task to purge old audit and activity logs.
    """
    self.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Starting purge...'})
    
    cutoff_date = timezone.now() - datetime.timedelta(days=days)
    
    # Estimate sizes (rough average based on fields)
    # UserActivityLog has many fields, approx 1KB
    # AuditLog has JSON fields, can be larger, approx 2KB
    ACTIVITY_LOG_SIZE = 1024 # bytes
    AUDIT_LOG_SIZE = 2048    # bytes

    self.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Counting records to purge...'})
    
    activity_to_purge = UserActivityLog.objects.filter(timestamp__lt=cutoff_date)
    audit_to_purge = AuditLog.objects.filter(timestamp__lt=cutoff_date)
    
    total_activity = activity_to_purge.count()
    total_audit = audit_to_purge.count()
    
    self.update_state(state='PROGRESS', meta={'progress': 30, 'status': f'Purging {total_activity} activity logs...'})
    activity_count = activity_to_purge.delete()[0]
    
    self.update_state(state='PROGRESS', meta={'progress': 60, 'status': f'Purging {total_audit} audit logs...'})
    audit_count = audit_to_purge.delete()[0]
    
    total_deleted = activity_count + audit_count
    estimated_space_saved = (activity_count * ACTIVITY_LOG_SIZE) + (audit_count * AUDIT_LOG_SIZE)
    
    # Format space saved
    if estimated_space_saved < 1024 * 1024:
        space_str = f"{estimated_space_saved / 1024:.2f} KB"
    else:
        space_str = f"{estimated_space_saved / (1024 * 1024):.2f} MB"

    if user_id:
        try:
            user = MyUser.objects.get(id=user_id)
            log_action(
                user=user,
                action='PURGE',
                module='accounts',
                description=f"Purged logs older than {days} days via Celery. Deleted {activity_count} activity logs and {audit_count} audit logs. Estimated space saved: {space_str}."
            )
        except MyUser.DoesNotExist:
            pass

    return {
        'status': 'success',
        'activity_count': activity_count,
        'audit_count': audit_count,
        'total_deleted': total_deleted,
        'space_saved': space_str,
        'message': f'Purged {total_deleted} logs older than {days} days. Saved approx {space_str}.'
    }
