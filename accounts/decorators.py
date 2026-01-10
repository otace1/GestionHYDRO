from functools import wraps
from .services import log_action

def log_view_action(action, description="", obj_getter=None):
    """
    Optional decorator for views to log actions consistently.
    Usage:
    @log_view_action('EXPORT_DATA', 'User exported the data list')
    def my_view(request):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            # Only log if the request was successful
            if 200 <= response.status_code < 300:
                obj = None
                if obj_getter:
                    try:
                        obj = obj_getter(request, *args, **kwargs)
                    except Exception:
                        pass
                
                log_action(
                    request, 
                    action, 
                    description, 
                    obj=obj, 
                    http_status=response.status_code
                )
            return response
        return _wrapped_view
    return decorator
