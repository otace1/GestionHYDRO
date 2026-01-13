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
        User = get_user_model()
        authorization_header = request.headers.get('Authorization')

        if not authorization_header:
            return None
        try:
            # Expecting 'Bearer <token>'
            parts = authorization_header.split(' ')
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return None
            
            access_token = parts[1]
            payload = check_token(access_token)
            
            # Firebase ID token payload contains 'uid' (Firebase UID)
            # and potentially other claims.
            uid = payload['uid']
        except auth.ExpiredIdTokenError:
            raise exceptions.AuthenticationFailed('Firebase ID token has expired')
        except auth.InvalidIdTokenError:
            raise exceptions.AuthenticationFailed('Invalid Firebase ID token')
        except auth.CertificateFetchError:
            raise exceptions.AuthenticationFailed('Could not fetch certificates to verify token')
        except Exception as e:
            # For other errors, don't expose details but log them if needed
            print(f"Authentication error: {str(e)}")
            raise exceptions.AuthenticationFailed('Authentication failed')

        # We assume the user ID in our database corresponds to the Firebase UID.
        # If the mobile app uses our API to login first, we should ensure the UIDs match.
        user = User.objects.filter(id=uid).first()
        if user is None:
            # Fallback to username search if ID doesn't match Firebase UID 
            # (though id=uid is what was there before)
            raise exceptions.AuthenticationFailed('User not found in local database')

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
