from django.urls import path

from .views import *

urlpatterns = [
    path('add/cargo/', AddCargo.as_view(), name='addCargo'),
    path('voie/', TypeVoie.as_view(), name='voie'),
    path('frontiere/', NomFrontiere.as_view(), name='frontiere'),
    path('unite/', TypeUnite.as_view(), name='unite'),
    path('provenance/', Provenance.as_view(), name='provenance'),
    path('fournisseur/', NomFournisseur.as_view(), name='fournisseur'),
    path('entrepot/', NomEntrepot.as_view(), name='entrepot'),
    path('produit/', TypeProduit.as_view(), name='produit'),
    path('qrcode/<int:pk>/cargo/qrcode/', GetQrcode.as_view(), name='getqrcode'),

    # Listing
    path('list/cargo/', GetCargoList.as_view(), name='getcargolist'),

    # Compteur
    path('compteur/cargo/', GetCargoCount.as_view(), name='getcargocount'),

]
