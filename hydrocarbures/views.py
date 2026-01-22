

# class AuthUserApiView(GenericAPIView):
#     permission_classes = (permissions.IsAuthenticated,)
#
#
# class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)
#
#         # Add custom claims
#         token["sub"] = settings.SIMPLE_JWT.get("USER_ID_CLAIM", "")
#         # When the serializer is called token['exp'] does not reflect the settings.ACCES_TOKEN_LIFETIME
#         # and is set to now + 1day,thus we subtract a day to get iat
#         token["iat"] = token["exp"] - (60 * 60 * 24)
#         token["claims"] = {"is_admin": user.is_admin, "is_staff": user.is_staff}
#         token['username'] = user.username
#         # token['role'] = user.role
#         # ...
#         return token
#
#
# class MyTokenObtainPairView(TokenObtainPairView):
#     serializer_class = MyTokenObtainPairSerializer
