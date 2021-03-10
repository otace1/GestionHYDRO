from django.urls import path
from . import views


urlpatterns = [

    path('', views.facturations, name='facturations'),
    path('saisiebl/', views.saisiebl, name='saisiebl'),
    path('appureration/', views.appureration, name='appuration'),
    path('detailsappureration/<int:pk>', views.detailsappuration, name='detailsappuration'),


]