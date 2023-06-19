from django.urls import path

from . import views

urlpatterns = [
    path('', views.showTableauTemplate, name='cargaison'),
    # path('', views.GestionCargaison.affichageTableau, name='cargaison'),
    path('getCargaison/', views.getCargaison, name='getCargaison'),
    path('nouvelle/', views.GestionCargaison.enregCargaison, name='nouvelle'),
    path('showqrcode/<int:pk>', views.GestionCargaison.showqrcode, name='showqrcode'),
    path('qrcode/', views.GestionCargaison.qrcodeprint, name='qrcode'),
]
