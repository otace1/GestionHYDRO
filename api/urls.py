from django.urls import path

from .views import *

urlpatterns = [

    #Module Frontiere
    path('add/cargo/', AddCargo.as_view(), name='addCargo_api'),
    path('voie/', TypeVoie.as_view(), name='voie_api'),
    path('frontiere/', NomFrontiere.as_view(), name='frontiere_api'),
    path('unite/', TypeUnite.as_view(), name='unite_api'),
    path('provenance/', Provenance.as_view(), name='provenance_api'),
    path('fournisseur/', NomFournisseur.as_view(), name='fournisseur_api'),
    path('entrepot/', NomEntrepot.as_view(), name='entrepot_api'),
    path('produit/', TypeProduit.as_view(), name='produit_api'),
    path('qrcode/<int:pk>/cargo/qrcode/', GetQrcode.as_view(), name='getqrcode_api'), #Get QRCode
    # Listing
    # path('list/cargo/', GetCargoList.as_view(), name='getcargolist_api'),
    # Compteur
    # path('compteur/cargo/', GetCargoCount.as_view(), name='getcargocount_api'),
    path('auth/user/', AuthUserApiView.as_view(), name='auth'),     # Auth
    path('auth/user/login/', loginApiView, name='apiLoginToken'),       # Auth
    path('verificationQrCode/', verificationQrCode, name='verificationQrCode'),     #Verification API
    path('showDataSaved/', showDataSaved, name='showDataSaved'),     #ShowPer user saved Data

    #Module Entrepot
    path('attenteEchantillonnage/', attenteEchantillonnage, name='attenteEchantillonnage'),  # ShowPer user saved Data
    path('attenteInspection/', attenteInspection, name='attenteInspection'),  # ShowPer user saved Data
    path('attenteDechargement/', attenteDechargement, name='attenteDechargement'),  # ShowPer user saved Data
    path('attenteRequisitionListe/', attenteRequisitionListe, name='attenteRequisitionListe'),  # ShowPer user saved Data
    path('enregistrementEchantillonnage/', enregistrementEchantillonnage, name='enregistrementEchantillonnage'),  # ShowPer user saved Data

]
