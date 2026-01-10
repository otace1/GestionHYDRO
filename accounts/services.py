import json
import logging
import datetime
import threading
from contextlib import contextmanager
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models as django_models
from django.db import utils as db_utils
from .models import UserActivityLog, AuditLog
from .middleware import get_current_request, get_current_request_id

logger = logging.getLogger(__name__)

SENSITIVE_FIELDS = {
    'password', 'token', 'otp', 'secret', 'authorization', 'card',
    'csrfmiddlewaretoken', 'access', 'refresh', 'api_key', 'passphrase',
    'private_key', 'pin'
}

_audit_context = threading.local()

@contextmanager
def audit_scope(action=None, extra=None):
    """
    Context manager to enrich audit logs within a scope.
    """
    old_action = getattr(_audit_context, 'action', None)
    old_extra = getattr(_audit_context, 'extra', {})
    
    _audit_context.action = action
    _audit_context.extra = {**old_extra, **(extra or {})}
    
    try:
        yield
    finally:
        _audit_context.action = old_action
        _audit_context.extra = old_extra

def get_audit_scope():
    return {
        'action': getattr(_audit_context, 'action', None),
        'extra': getattr(_audit_context, 'extra', {})
    }

def sanitize_data(data):
    """Recursively sanitize sensitive fields in a dictionary or list."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if any(s in k.lower() for s in SENSITIVE_FIELDS):
                sanitized[k] = '********'
            else:
                sanitized[k] = sanitize_data(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    return data

def model_to_dict_sanitized(instance):
    """
    Convert model instance to dict and sanitize sensitive fields.
    Handles FileFields by storing only the name.
    """
    if instance is None:
        return None
    
    data = {}
    opts = instance._meta
    for f in opts.concrete_fields:
        try:
            value = f.value_from_object(instance)
            
            # Sanitize sensitive fields by name
            if any(s in f.name.lower() for s in SENSITIVE_FIELDS):
                data[f.name] = '********'
            # Handle FileFields
            elif isinstance(f, django_models.FileField):
                data[f.name] = str(value) if value else None
            # Handle Date/Time
            elif isinstance(value, (datetime.date, datetime.datetime)):
                data[f.name] = value.isoformat()
            # Truncate very long text
            elif isinstance(value, str) and len(value) > 2000:
                data[f.name] = value[:2000] + '... [TRUNCATED]'
            else:
                data[f.name] = value
        except Exception:
            data[f.name] = "[ERROR CAPTURING VALUE]"
            
    return data

def get_changes(old_state, new_state):
    """
    Compare two states and return a dict of changes: {field: {from: X, to: Y}}
    """
    changes = {}
    if not old_state or not new_state:
        return changes
    
    # Use all keys from both states
    all_keys = set(old_state.keys()) | set(new_state.keys())
    
    for key in all_keys:
        old_val = old_state.get(key)
        new_val = new_state.get(key)
        
        if old_val != new_val:
            changes[key] = {'from': old_val, 'to': new_val}
            
    return changes

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def _fill_actor_data(data, request):
    """Helper to fill actor details from request."""
    data.update({
        'actor_type': 'system',
        'actor_username_snapshot': 'System',
    })
    
    if request:
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            data['actor'] = user
            data['actor_username_snapshot'] = user.username
            data['actor_type'] = 'user'
        else:
            data['actor_username_snapshot'] = 'Anonymous'
            data['actor_type'] = 'api' if 'api' in request.path.lower() else 'user'
            
        data.update({
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        })
        if hasattr(request, 'session') and request.session.session_key:
            data['session_key'] = request.session.session_key

def log_action(request=None, action=None, description="", *, user=None, module=None, obj=None, status="success", http_status=None, extra=None):
    """
    Centralized logging function for UserActivityLog.
    """
    try:
        log_data = {
            'action': action,
            'description': description,
            'status': status,
            'http_status_code': http_status,
            'extra': extra or {},
            'username_snapshot': 'System',
        }

        if user:
            log_data['user'] = user
            log_data['username_snapshot'] = user.username
        
        if module:
            log_data['module'] = module

        if request:
            req_user = getattr(request, 'user', None)
            if not user and req_user and req_user.is_authenticated:
                log_data['user'] = req_user
                log_data['username_snapshot'] = req_user.username
            elif not user and (not req_user or not req_user.is_authenticated):
                log_data['username_snapshot'] = 'Anonymous'

            log_data.update({
                'request_method': request.method,
                'path': request.path,
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            })
            
            if hasattr(request, 'session') and request.session.session_key:
                log_data['session_key'] = request.session.session_key

            if request.GET:
                log_data['query_params'] = sanitize_data(request.GET.dict())

            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    if request.content_type == 'application/json':
                        body = json.loads(request.body)
                    else:
                        body = request.POST.dict()
                    log_data['request_body_summary'] = sanitize_data(body)
                except Exception:
                    pass

        if obj and hasattr(obj, '_meta'):
            log_data.update({
                'object_type': obj._meta.model_name,
                'object_id': str(getattr(obj, 'pk', '')),
                'object_repr': str(obj)[:255],
            })
            if not module:
                log_data['module'] = obj._meta.app_label
        elif not module and request:
            path_parts = [p for p in request.path.split('/') if p]
            if path_parts:
                log_data['module'] = path_parts[0]

        UserActivityLog.objects.create(**log_data)

    except Exception as e:
        logger.error(f"Error in UserActivityLog logging: {e}", exc_info=True)

_table_exists_cache = {}

def table_exists(table_name):
    if table_name in _table_exists_cache:
        return _table_exists_cache[table_name]
    try:
        from django.db import connection
        exists = table_name in connection.introspection.table_names()
        # Only cache True, so we re-check if False (until it's created)
        if exists:
            _table_exists_cache[table_name] = True
        return exists
    except Exception:
        return False

def log_audit(action, instance, old_state=None, new_state=None, status='success', error_message=None, extra=None):
    """
    Logs a data change event to AuditLog.
    """
    try:
        if not getattr(settings, 'AUDIT_LOG_ENABLED', True):
            return
            
        # Check if table exists to avoid breaking transactions during migrations
        if not table_exists('accounts_auditlog'):
            return

        request = get_current_request()
        request_id = get_current_request_id()
        scope = get_audit_scope()
        
        # Override action if scope defines it
        final_action = scope['action'] or action
        
        audit_data = {
            'action': final_action,
            'app_label': instance._meta.app_label,
            'model_name': instance._meta.model_name,
            'object_pk': str(instance.pk),
            'object_repr': str(instance)[:255],
            'status': status,
            'error_message': error_message,
            'extra': {**scope['extra'], **(extra or {})},
            'request_id': request_id,
        }
        
        _fill_actor_data(audit_data, request)

        if action == 'UPDATE':
            if old_state and new_state:
                audit_data['changes'] = get_changes(old_state, new_state)
            if not audit_data.get('changes'):
                return # No changes, skip logging
        elif action == 'CREATE':
            audit_data['new_state'] = new_state or model_to_dict_sanitized(instance)
        elif action == 'DELETE':
            audit_data['old_state'] = old_state or model_to_dict_sanitized(instance)
            
        AuditLog.objects.create(**audit_data)
        
    except db_utils.OperationalError as e:
        if 'no such table' in str(e).lower():
            # Expected during initial migrations
            pass
        else:
            logger.error(f"Operational error in AuditLog logging: {e}")
    except Exception as e:
        logger.error(f"Error in AuditLog logging: {e}", exc_info=True)

def log_bulk_audit(queryset, action, changes=None, extra=None):
    """
    Log a bulk operation on a queryset.
    """
    try:
        if not getattr(settings, 'AUDIT_LOG_ENABLED', True):
            return
            
        # Check if table exists to avoid breaking transactions during migrations
        if not table_exists('accounts_auditlog'):
            return

        count = queryset.count()
        model = queryset.model
        request = get_current_request()
        request_id = get_current_request_id()
        scope = get_audit_scope()
        
        audit_data = {
            'action': action,
            'app_label': model._meta.app_label,
            'model_name': model._meta.model_name,
            'object_pk': 'MULTIPLE',
            'object_repr': f"Bulk {action} on {count} {model._meta.verbose_name_plural}",
            'changes': changes,
            'extra': {
                'query': str(queryset.query),
                'count': count,
                **scope['extra'],
                **(extra or {})
            },
            'request_id': request_id,
        }
        
        _fill_actor_data(audit_data, request)
        AuditLog.objects.create(**audit_data)
        
    except Exception as e:
        logger.error(f"Error in bulk AuditLog logging: {e}", exc_info=True)
