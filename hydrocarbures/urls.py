from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from accounts.views import login_user
from rest_framework.routers import DefaultRouter
from api.views import UserViewSerializer
from django.contrib import admin

# Customizing the Django admin site
admin.site.site_header = 'TrackFlow +'
admin.site.index_title = 'TrackFlow Backend Administration'
admin.site.site_title = 'TrackFlow +'


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                      # path('sentry-debug/', trigger_error),
                      path('admin/', admin.site.urls),
                      path('ads/', include('ads.urls')),
                      path('cargaison/', include('enreg.urls')),
                      path('shydro/', include('shydro.urls')),
                      path('entrepot/', include('entrepot.urls')),
                      path('labo/', include('labo.urls')),
                      path('accounts/', include('accounts.urls')),
                      path('facturations/', include('facturations.urls')),
                      path('', login_user),
                      # path('__reload__/', include("django_browser_reload.urls")),

                      # Api
                      path('api/', include("api.urls")),
                      # path('verification/', include("verification.urls")),

                      # Progress Bar
                      path('celery-progress/', include('celery_progress.urls')),

                  ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:

    urlpatterns = [
        # path('__debug__/', include(debug_toolbar.urls)),
        # path('sentry-debug/', trigger_error),
        path('admin/', admin.site.urls),
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
        # path('verification/', include("verification.urls")),

        # Progress Bar
        path('celery-progress/', include('celery_progress.urls')),

    ]


router = DefaultRouter()
router.register('user', UserViewSerializer, basename='user')

urlpatterns += router.urls


