from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from accounts.views import login_user
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.routers import DefaultRouter
from api.views import UserViewSerializer
from .views import MyTokenObtainPairView

#
# def trigger_error(request):
#     division_by_zero = 1 / 0

if settings.DEBUG:
    import debug_toolbar

urlpatterns = [
                  path('__debug__/', include(debug_toolbar.urls)),
                  # path('sentry-debug/', trigger_error),
                  path('ads/', include('ads.urls')),
                  path('cargaison/', include('enreg.urls')),
                  path('shydro/', include('shydro.urls')),
                  path('entrepot/', include('entrepot.urls')),
                  path('labo/', include('labo.urls')),
                  path('accounts/', include('accounts.urls')),
                  path('facturations/', include('facturations.urls')),
                  path('', login_user),
                  path('__reload__/', include("django_browser_reload.urls")),

                  # Api
                  path('api/', include("api.urls")),

                  # Auth
                  path('api-auth/', include('rest_framework.urls')),
                  path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

router = DefaultRouter()
router.register('user', UserViewSerializer, basename='user')

urlpatterns += router.urls

# userAccessToken
