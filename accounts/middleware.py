import threading
import uuid
from django.utils.deprecation import MiddlewareMixin

# Using threading.local for now to maintain consistency with previous implementation,
# but adding request_id support.
_thread_locals = threading.local()

def get_current_request():
    return getattr(_thread_locals, 'request', None)

def get_current_request_id():
    return getattr(_thread_locals, 'request_id', None)

class RequestStoreMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate or retrieve a request_id for correlation
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.request_id = request_id
        
        _thread_locals.request = request
        _thread_locals.request_id = request_id
        
        try:
            response = self.get_response(request)
            if hasattr(response, 'headers'):
                response['X-Request-ID'] = request_id
            return response
        finally:
            if hasattr(_thread_locals, 'request'):
                del _thread_locals.request
            if hasattr(_thread_locals, 'request_id'):
                del _thread_locals.request_id
