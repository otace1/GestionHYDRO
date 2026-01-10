from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .services import log_action, log_audit, model_to_dict_sanitized
from .middleware import get_current_request

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    log_action(request, 'LOGIN', f"User {user.username} logged in successfully")

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        log_action(request, 'LOGOUT', f"User {user.username} logged out")

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get('username', 'unknown')
    log_action(request, 'LOGIN_FAILED', f"Failed login attempt for username: {username}", status='failure')

# Exclude models from audit logging
EXCLUDE_MODELS = getattr(settings, 'AUDIT_LOG_EXCLUDE_MODELS', [])

def is_audited(sender):
    model_name = f"{sender._meta.app_label}.{sender._meta.model_name}"
    return model_name not in EXCLUDE_MODELS and getattr(settings, 'AUDIT_LOG_ENABLED', True)

@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    if not is_audited(sender):
        return
    
    if instance.pk:
        try:
            # Fetch original instance from DB
            original = sender.objects.get(pk=instance.pk)
            instance._audit_old_state = model_to_dict_sanitized(original)
        except sender.DoesNotExist:
            instance._audit_old_state = None
    else:
        instance._audit_old_state = None

@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    if not is_audited(sender):
        return
    
    action = 'CREATE' if created else 'UPDATE'
    new_state = model_to_dict_sanitized(instance)
    old_state = getattr(instance, '_audit_old_state', None)
    
    log_audit(
        action=action,
        instance=instance,
        old_state=old_state,
        new_state=new_state
    )

@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    if not is_audited(sender):
        return
    
    log_audit(
        action='DELETE',
        instance=instance,
        old_state=model_to_dict_sanitized(instance)
    )
