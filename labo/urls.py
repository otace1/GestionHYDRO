from django.urls import path
# from django.conf.urls import url
from . import views

urlpatterns = [
    path('', views.GestionLaboratoire.affichageenchantillon, name='labo'),
    path('refaireAffichage/', views.affichageAnalyseRefaire, name='affichageAnalyseRefaire'),
    path('refaireAffichageResponse/', views.affichageAnalyseRefaireResponse, name='affichageAnalyseRefaireResponse'),
    path('echantillon/', views.GestionLaboratoire.affichageenchantillonResponse, name='affichageenchantillonResponse'),
    path('receptionRapports/', views.receptionRapports, name='receptionRapports'),
    path('receptionRapportsGenerate/', views.receptionRapportsGenerate, name='receptionRapportsGenerate'),
    path('receptionRapports/response/', views.receptionRapportsResponse, name='receptionRapportsResponse'),
    path('receptionRapports/response/export/', views.receptionRapportsResponse, name='receptionRapportsResponseExport'),
    path('receptionRapports/filtres/', views.receptionRapportsResponseFiltres, name='receptionRapportsResponseFiltres'),
    path('receptionRapports/filtres/export/', views.receptionRapportsResponseFiltres, name='receptionRapportsResponseFiltresExport'),
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
    # Alias required by frontend: provides the same JSON as validation1Response under the name 'affichagetableauvalidation1'
    path('validation1/response/', views.affichagetableauvalidation1Response, name='affichagetableauvalidation1'),
    # Filter endpoint for Validation 1 (POST/GET with pagination + filters)
    path('validation1/filters/', views.affichagetableauvalidation1Filtres, name='affichagetableauvalidation1Filtres'),

    path('echantillonRecus/', views.echantillonRecus, name='echantillonRecus'),
    path('echantillonRecus/response/', views.echantillonRecusResponse, name='echantillonRecusResponse'),

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
    path('labdashrap/synthese/', views.labdashboardrapport_synthese, name='labodashboardrapport_synthese'),
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

    #Correction Nature
    path('correctionNature/', views.correctionNature, name='correctionNature'),

    #Correction Nature
    path('clearSaisie/', views.clearSaisie, name='clearSaisie'),


    #Different Rapport et Compteur Labo
    path('enchAttenteReception/', views.enchAttenteReception, name='enchAttenteReception'),
    path('enchAttenteReception2/', views.enchAttenteReception2, name='enchAttenteReception2'),
    path('enchAttenteReceptionExport/', views.enchAttenteReceptionExport, name='enchAttenteReceptionExport'),
    path('enchAttenteReceptionExport2/', views.enchAttenteReceptionExport2, name='enchAttenteReceptionExport2'),
    path('enchAttenteResultat/', views.enchAttenteResultat, name='enchAttenteResultat'),
    path('enchAttenteResultat2/', views.enchAttenteResultat2, name='enchAttenteResultat2'),
    path('enchAttenteResultatExport/', views.enchAttenteResultatExport, name='enchAttenteResultatExport'),
    path('enchAttenteResultatExport2/', views.enchAttenteResultatExport2, name='enchAttenteResultatExport2'),
    path('enchAttenteValidation/', views.enchAttenteValidation, name='enchAttenteValidation'),
    path('enchAttenteValidation2/', views.enchAttenteValidation2, name='enchAttenteValidation2'),
    path('enchPrintedCert/', views.enchPrintedCert, name='enchPrintedCert'),
    path('enchPrintedCert2/', views.enchPrintedCert2, name='enchPrintedCert2'),
    path('enchPrintedCertExport/', views.enchPrintedCertExport, name='enchPrintedCertExport'),
    path('enchPrintedCertExport2/', views.enchPrintedCertExport2, name='enchPrintedCertExport2'),


    #Rapport au niveaux des acteurs du labo
    path('rapportCq/', views.rapportCq, name='rapportCq'),
    path('rapportCq2/', views.rapportCq2, name='rapportCq2'),
    path('rapportCq/response/', views.rapportCqResponse, name='rapportCqResponse'),
    path('rapportCqResponse/response/export/', views.rapportCqResponse, name='rapportCqResponseExport'),
    path('rapportCQExport/', views.rapportCQExport, name='rapportCQExport'),

    path('rapportCqfiltres/filtres/', views.rapportCqfiltres, name='rapportCqfiltres'),
    path('rapportCqfiltres2/filtres/', views.rapportCqfiltres2, name='rapportCqfiltres2'),
    path('rapportCqfiltres/response/', views.rapportCqfiltresResponse, name='rapportCqfiltresResponse'),
    path('rapportCqfiltresResponseExport', views.rapportCqfiltresResponseExport, name='rapportCqfiltresResponseExport'),

    # path('rapportActiviteFiltrePost/', views.rapportActiviteFiltrePost, name='rapportActiviteFiltrePost'),
    # path('checkExportTaskStatus/<str:task_id>', views.checkExportTaskStatus, name='checkExportTaskStatus'),

    path('bulkConforme1/', views.bulkConforme1, name='bulkConforme1'),
    path('bulkNonConforme1/', views.bulkNonConforme1, name='bulkNonConforme1'),
    path('bulkRefaire1/', views.bulkRefaire1, name='bulkRefaire1'),

    path('bulkConforme2/', views.bulkConforme2, name='bulkConforme2'),
    path('bulkNonConforme2/', views.bulkNonConforme2, name='bulkNonConforme2'),
    path('bulkRefaire2/', views.bulkRefaire2, name='bulkRefaire2'),

    path('impressionCertificatBulk/', views.impressionCertificatBulk, name='impressionCertificatBulk'),

]
