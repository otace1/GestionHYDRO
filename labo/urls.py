from django.urls import path
# from django.conf.urls import url
from . import views

urlpatterns = [
    path('', views.GestionLaboratoire.affichageenchantillon, name='labo'),
    path('echantillon/', views.GestionLaboratoire.affichageenchantillonResponse, name='affichageenchantillonResponse'),
    path('receptionRapports/', views.receptionRapports, name='receptionRapports'),
    path('receptionRapports/response/', views.receptionRapportsResponse, name='receptionRapportsResponse'),
    path('receptionRapports/filtres/', views.receptionRapportsResponseFiltres, name='receptionRapportsResponseFiltres'),
    path('reception/', views.GestionLaboratoire.receptionechantillon, name='reception'),
    path('modification/', views.GestionLaboratoire.modification, name='modification'),
    path('rechercheqr/', views.GestionLaboratoire.rechercheqrcode, name='rechercheqr'),
    path('recherchecode/', views.GestionLaboratoire.recherchecode, name='recherchecode'),
    path('analyse/', views.GestionAnalyse.affichageanalyse, name='analyse'),
    path('analyse/response/', views.responseAffichageanalyse, name='responseAffichageanalyse'), #Ajax


    path('rechercheenc1/', views.GestionAnalyse.rechercheencodage1, name='rechercheenc1'),
    path('rechercheenc2/', views.GestionAnalyse.rechercheencodage2, name='rechercheenc2'),

    path('recherchecq/', views.GestionImpressionLabo.recherchecq, name='recherchecq'),
    path('recherchecqr/', views.GestionImpressionLabo.recherchecqr, name='recherchecqr'),

    path('impression/', views.GestionImpressionLabo.affichagetableauimpression, name='impression'),
    path('impression/response/', views.responseAffichagetableauimpression, name='responseAffichagetableauimpression'),
    # path('impression/<int:pk>', views.GestionImpressionLabo.impressioncertificat, name='print'),
    path('impression/cq/', views.impressioncertificat, name='print'),
    path('reimpression/<int:pk>', views.GestionImpressionLabo.reimpressioncertificat, name='reprint'),
    path('ficheresultat/<int:pk>', views.GestionImpressionLabo.impressionficheresultat, name='fiche'),

    path('mogas/<int:pk>', views.GestionAnalyse.encodagemogas, name='mogas'),
    path('gasoil/<int:pk>', views.GestionAnalyse.encodagegasoil, name='gasoil'),
    path('jeta1/<int:pk>', views.GestionAnalyse.encodagejeta1, name='jeta1'),
    path('petrolelampant/<int:pk>', views.GestionAnalyse.encodagepetrole, name='petrole'),

    # Refaire
    path('mogasr/<int:pk>', views.GestionAnalyse.encodagemogasr, name='mogasr'),
    path('gasoilr/<int:pk>', views.GestionAnalyse.encodagegasoilr, name='gasoilr'),
    path('jeta1r/<int:pk>', views.GestionAnalyse.encodagejeta1r, name='jeta1r'),
    path('petrolelampantr/<int:pk>', views.GestionAnalyse.encodagepetroler, name='petroler'),

    # Liens des validations Labo
    path('validation1/', views.GestionValidation.affichagetableauvalidation1, name='validation1'),
    path('validation1Response/', views.affichagetableauvalidation1Response, name='affichagetableauvalidation1Response'), #Ajax Request
    path('codecq/<int:pk>', views.GestionValidation.codecertificat, name='codecq'),
    path('validation2/', views.GestionValidation.affichagetableauvalidation2, name='validation2'),
    path('validation2Response/', views.affichagetableauvalidation2Response, name='affichagetableauvalidation2Response'), #Ajax Request

    path('rapport/<int:pk>', views.GestionValidation.affichagerapportpdf, name='rapportvalidationpdf'),
    path('val/<int:pk>', views.GestionValidation.validationv1, name='validationv1'),
    path('conforme/', views.GestionValidation.conforme, name='conforme'),
    path('nonconforme/', views.GestionValidation.nonconforme, name='nonconforme'),
    path('refaire/', views.GestionValidation.refaire, name='refaire'),


    path('conforme2/', views.GestionValidation.conforme2, name='conforme2'),
    path('nonconforme2/', views.GestionValidation.nonconforme2, name='nonconforme2'),

    # Dashboard Laboratoire
    path('labdash/', views.labdashboard, name='labodashboard'),
    path('labdashrap/', views.labdashboardrapport, name='labodashboardrapport'),
    path('echantCount/', views.echantCount, name='echantCount'),
    path('echantAnalyse/', views.echantAnalyse, name='echantAnalyse'),

    # Qualification Produit
    path('nature/<int:pk>', views.natureProduitLabo, name='natureProduitLabo'),

    #Nouveau Form de Saisie des resultats
    path('saisieResultat/<int:pk>', views.saisieResultat, name='saisieResultat'),
    path('saisieResultatParametre/<int:pk>', views.saisieResultatParametre, name='saisieResultatParametre'),
    path('saisieResultatParametre/ajax/', views.saisieResultatParametreAjax, name='saisieResultatParametreAjax'),
    path('validationResulat/', views.validationResulat, name='validationResulat'),
    path('affichageDetailsResultatsGauche/<int:pk>', views.affichageDetailsResultats, name='affichageDetailsResultats'),
    path('affichageDetailsResultatsDroite/<int:pk>', views.affichageDetailsResultatsDroite, name='affichageDetailsResultatsDroite'),


    ###Second way of validation from the Chef Sce
    path('conformeM2/', views.conformeAjx, name='conformeAjx'),
    path('nonconformeM2/', views.nonconformeAjx, name='nonconformeAjx'),
    path('refaireM2/', views.refaireAjx, name='refaireAjx'),


    ###Second way of validation from the Chef Labo
    path('conformeM3/', views.conformeAjx2, name='conformeAjx2'),
    path('nonconformeM3/', views.nonconformeAjx2, name='nonconformeAjx2'),


    #Submission of Resulat by Ajax
    path('saisieResultat/ajx/', views.saisieResultatAjax, name='saisieResultatAjax'),

]
