from django.urls import path

from .views import *

urlpatterns = [
    path('add/cargo/', AddCargo.as_view(), name='addCargo_api'),
    path('voie/', TypeVoie.as_view(), name='voie_api'),
    path('frontiere/', NomFrontiere.as_view(), name='frontiere_api'),
    path('unite/', TypeUnite.as_view(), name='unite_api'),
    path('provenance/', Provenance.as_view(), name='provenance_api'),
    path('fournisseur/', NomFournisseur.as_view(), name='fournisseur_api'),
    path('entrepot/', NomEntrepot.as_view(), name='entrepot_api'),
    path('produit/', TypeProduit.as_view(), name='produit_api'),
    path('qrcode/<int:pk>/cargo/qrcode/', GetQrcode.as_view(), name='getqrcode_api'),

    # Listing
    path('list/cargo/', GetCargoList.as_view(), name='getcargolist_api'),

    # Compteur
    path('compteur/cargo/', GetCargoCount.as_view(), name='getcargocount_api'),

    # Auth
    path('auth/user/', AuthUserApiView.as_view(), name='auth'),
    path('auth/user/login/', loginApiView, name='apiLoginToken'),

    #Verification API
    path('verificationQrCode/', verificationQrCode, name='verificationQrCode'),

    #ShowPer user saved Data
    path('showDataSaved/', showDataSaved, name='showDataSaved'),

]
