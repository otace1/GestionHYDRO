from rest_framework.authentication import get_authorization_header, BaseAuthentication
from rest_framework import exceptions


class JWTAuthentication(BaseAuthentication):

    def authenticate(self, request):
        auth_header = get_authorization_header(request)
        auth_data = auth_header.decode('utf-8')
        auth_token = auth_data.split(" ")

        if len(auth_token) != 2:
            raise exceptions.AuthenticationFailed('Token not valid')

        token = auth_token[1]

        return super().authenticate(request)
