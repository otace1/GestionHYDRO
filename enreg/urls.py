from django.urls import path

from . import views

urlpatterns = [
    path('', views.GestionCargaison.affichageTableau, name='cargaison'),
    path('nouvelle/', views.GestionCargaison.enregistrementCargaison, name='nouvelle'),
    path('showqrcode/<int:pk>', views.GestionCargaison.showqrcode, name='showqrcode'),
    path('qrcode/', views.GestionCargaison.qrcodeprint, name='qrcode'),
]
