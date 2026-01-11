from django.urls import path

from . import views

urlpatterns = [
    path('', views.showTableauTemplate, name='cargaison'),
    # path('', views.GestionCargaison.affichageTableau, name='cargaison'),
    path('getCargaison/', views.getCargaison, name='getCargaison'),
    path('nouvelle/', views.GestionCargaison.enregCargaison, name='nouvelle'),
    path('cargaison/create-form/', views.cargaison_create_form, name='cargaison_create_form'),
    path('cargaison/create/', views.cargaison_create, name='cargaison_create'),
    path('showqrcode/<int:pk>', views.GestionCargaison.showqrcode, name='showqrcode'),
    path('qrcode/', views.GestionCargaison.qrcodeprint, name='qrcode'),
    path('cargaison/<int:pk>/details/', views.cargaison_details_partial, name='cargaison_details_partial'),
    path('cargaison/<int:pk>/qrcode/download/', views.cargaison_qrcode_download, name='cargaison_qrcode_download'),
]
