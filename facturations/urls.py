from django.urls import path
from . import views


urlpatterns = [

    path('', views.facturations, name='facturations'),
    path('appurements/', views.facturationsResponse, name='facturationsResponse'),
    path('partial/', views.partial, name='partial'),
    path('partial/respons/', views.partialResponse, name='partialResponse'),
    path('partial/respons/data/', views.partialResponseData, name='partialResponseData'),
    path('saisiebl/', views.saisiebl, name='saisiebl'),
    path('rapports/', views.rapports, name='rapports'),
    path('rapports/response/', views.rapportsResponse, name='rapportsResponse'),
    path('appureration/', views.appureration, name='appuration'),
    path('recherchert1/', views.filtret1, name='filtret1'),
    path('detailsappureration/<int:pk>', views.detailsappuration, name='detailsappuration'),

]
