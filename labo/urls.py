from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [

    path('', views.GestionLaboratoire.affichageenchantillon, name='labo'),
    path('reception/', views.GestionLaboratoire.receptionechantillon, name='reception'),
    path('modification/', views.GestionLaboratoire.modification, name='modification'),
    path('rechercheqr/', views.GestionLaboratoire.rechercheqrcode, name='rechercheqr'),
    path('recherchecode/', views.GestionLaboratoire.recherchecode, name='recherchecode'),
    path('analyse/', views.GestionAnalyse.affichageanalyse, name='analyse'),

    path('rechercheenc1/', views.GestionAnalyse.rechercheencodage1, name='rechercheenc1'),
    path('rechercheenc2/', views.GestionAnalyse.rechercheencodage2, name='rechercheenc2'),

    path('recherchecq/', views.GestionImpressionLabo.recherchecq, name='recherchecq'),
    path('recherchecqr/', views.GestionImpressionLabo.recherchecqr, name='recherchecqr'),

    path('impression/', views.GestionImpressionLabo.affichagetableauimpression, name='impression'),
    path('impression/<int:pk>', views.GestionImpressionLabo.impressioncertificat, name='print'),
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
    path('codecq/<int:pk>', views.GestionValidation.codecertificat, name='codecq'),
    path('validation2/', views.GestionValidation.affichagetableauvalidation2, name='validation2'),

    path('rapport/<int:pk>', views.GestionValidation.affichagerapportpdf, name='rapportvalidationpdf'),
    path('val/<int:pk>', views.GestionValidation.validationv1, name='validationv1'),
    path('val2/<int:pk>', views.GestionValidation.conforme, name='conforme'),
    path('val3/<int:pk>', views.GestionValidation.nonconforme, name='nonconforme'),
    path('ref/<int:pk>', views.GestionValidation.refaire, name='refaire'),

    path('val4/<int:pk>', views.GestionValidation.conforme2, name='conforme2'),
    path('val5/<int:pk>', views.GestionValidation.nonconforme2, name='nonconforme2'),

    # Dashboard Laboratoire
    path('labdash/', views.labdashboard, name='labodashboard'),
    path('labdashrap/', views.labdashboardrapport, name='labodashboardrapport'),

]
