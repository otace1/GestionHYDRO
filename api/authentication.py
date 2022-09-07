from rest_framework.authentication import BaseAuthentication
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import exceptions
from .decodeJWTFirebaseToken import check_token
from django.contrib.auth import get_user_model
import firebase_admin
from firebase_admin import auth, credentials


class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        # Return the failure reason instead of an HttpResponse
        return reason


class SafeJWTAuthentication(BaseAuthentication):
    '''
        custom authentication class for DRF and JWT
        https://github.com/encode/django-rest-framework/blob/master/rest_framework/authentication.py
    '''

    def authenticate(self, request):

        if not firebase_admin._apps:
            cred = credentials.Certificate('./api/serviceAccount.json')
            default_app = firebase_admin.initialize_app(cred)

        User = get_user_model()
        authorization_header = request.headers.get('Authorization')

        if not authorization_header:
            return None
        try:
            access_token = authorization_header.split(' ')[1]
            payload = check_token(access_token)
            print(payload)
            uid = payload['uid']
            print(uid)
        except auth.ExpiredIdTokenError:
            raise exceptions.AuthenticationFailed('access_token expired')

        user = User.objects.filter(id=uid).first()
        if user is None:
            raise exceptions.AuthenticationFailed('User not found')

        # self.enforce_csrf(request)
        print(user)
        return (user, None)

    #
    # def enforce_csrf(self, request):
    #     """
    #     Enforce CSRF validation
    #     """
    #     check = CSRFCheck()
    #     # populates request.META['CSRF_COOKIE'], which is used in process_view()
    #     check.process_request(request)
    #     reason = check.process_view(request, None, (), {})
    #     print(reason)
    #     if reason:
    #         # CSRF failed, bail with explicit error message
    #         raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)
