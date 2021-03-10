from django.contrib import admin
from django.contrib.auth import views
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings
from accounts.views import login_user

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
        # path('adloc/', admin.site.urls),
        path('ads/',include('ads.urls')),
        path('cargaison/', include('enreg.urls')),
        path('shydro/', include('shydro.urls')),
        path('entrepot/', include('entrepot.urls')),
        path('labo/', include('labo.urls')),
        path('accounts/', include('accounts.urls')),
        path('facturations/', include('facturations.urls')),
        path('',login_user)

    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


