from django.urls import path

# from django.conf.urls import re_
from . import views

urlpatterns = [

    path('', views.GestionCodification.affichageTableau, name='codification'),
    path('response/responseAffichageTableau/', views.GestionCodification.responseAffichageTableau, name='responseAffichageTableau'), #Json Response
    path('details/<int:pk>', views.linedetails, name='details'),
    path('update/<int:pk>', views.lineupdate, name='update'),
    #
    # path('numdoss/<int:pk>', views.numreq, name='numreq'),
    path('numdoss/', views.numreq, name='numreq'),
    path('codecam/<int:pk>', views.codecam, name='codecam'),

    path('', views.GestionResultatLabo.affichagetableauresultat, name='laboresult'),
    path('affichageNonConforme/', views.GestionResultatLabo.affichageNonConforme, name='affichageNonConforme'),

    path('act/', views.GestionDecharger.gestionact, name='gestionact'),
    path('act/<int:pk>', views.GestionDecharger.printact, name='printact'),
    path('react/<int:pk>', views.GestionDecharger.reprintact, name='reprintact'),
    path('rechercheact/', views.GestionDecharger.rechercheact, name='rechercheact'),

    path('go/<int:pk>', views.GestionDecharger.godechargement, name='go'),

    path('enAttenteEchantillonnage/', views.enAttenteEchantillonnage, name='enAttenteEchantillonnage'),
    path('enAttenteEchantillonnage1/', views.enAttenteEchantillonnage1, name='enAttenteEchantillonnage1'),
    path('enAttenteDechargement/', views.enAttenteDechargement, name='enAttenteDechargement'),
    path('enAttenteDechargement1/', views.enAttenteDechargement1, name='enAttenteDechargement1'),
    path('enAttenteResultatLabo/', views.enAttenteResultatLabo, name='enAttenteResultatLabo'),
    path('enAttenteResultatLabo1/', views.enAttenteResultatLabo1, name='enAttenteResultatLabo1'),
    path('enAttenteReceptionLabo/', views.enAttenteReceptionLabo, name='enAttenteReceptionLabo'),
    path('enAttenteReceptionLabo1/', views.enAttenteReceptionLabo1, name='enAttenteReceptionLabo1'),
    path('enAttenteInspection/', views.enAttenteInspection, name='enAttenteInspection'),
    path('enAttenteInspection1/', views.enAttenteInspection1, name='enAttenteInspection1'),
    path('rapportActivite/', views.rapportActivite, name='rapportActivite'),
    path('responseRapportActivite/', views.responseRapportActivite, name='responseRapportActivite'), #Json response
    path('exportResponseRapportActivite/', views.responseRapportActivite, name='exportResponseRapportActivite'), #Json response
    path('rapportActiviteExport/', views.rapportActivite, name='rapportActiviteExport'),
    path('rapportActiviteFiltre/', views.rapportActiviteFiltre, name='rapportActiviteFiltre'),

    path('rapportActiviteFiltrePost/', views.rapportActiviteFiltrePost, name='rapportActiviteFiltrePost'),
    path('checkExportTaskStatus/<str:task_id>', views.checkExportTaskStatus, name='checkExportTaskStatus'),

    path('rapportRe/<int:pk>', views.rapportRe, name='rapportRe'),
    path('rapportIs/<int:pk>', views.rapportIs, name='rapportIs'),

    path('consignation/<int:pk>', views.consignation, name='consignation'),


    path('regularisation/', views.regularisation, name='regularisation'),
    path('regularisation_response/', views.regularisation_response, name='regularisation_response'),
    path('regularisationDestination/', views.regularisationDestination, name='regularisationDestination'),
    path('changementNature/', views.changementNature, name='changementNature'),
    path('changementImportateur/', views.changementImportateur, name='changementImportateur'),
    path('transbordement/', views.transbordement, name='transbordement'),
    path('del_record/', views.del_record, name='del_record'), #Delete one record by confirming an leaving logs

    path('regularisation/cargaison/', views.regularisationCargaison, name='regularisationCargaison'),
    path('regularisation/importateur/', views.regularisationImportateur, name='regularisationImportateur'),
    path('regularisation/entrepot/', views.regularisationEntrepot, name='regularisationEntrepot'),

    path('regularisation/recherche/', views.regularisationRecherche, name='regularisationRecherche'),

    path('recherche/rapportActivite/', views.rechercheRapportActivite, name='rechercheRapportActivite'),

    # re-Inspecter
    path('reInspecter/', views.reInspecter, name='reInspecter'),

    # Impression RApport
    path('impressionRappEch/', views.impressionRappEch, name='impressionRappEch'),
    path('impressionRappInsp/', views.impressionRappInsp, name='impressionRappInsp'),
    # path('impressionRappEssaie/', views.impressionRappEssaie, name='impressionRappEssaie'),

    #Celery Task Test
    path('tasks/', views.tasks, name='tasks'),

    path('gestionGo/', views.gestionGo, name='gestionGo'),
    path('gestionGoResponse/', views.gestionGoResponse, name='gestionGoResponse'),


    path('tableaudeBordHydro/', views.tableaudeBordHydro, name='tableaudeBordHydro'),

    path('lastrecordShydro/', views.lastrecordShydro, name='lastrecordShydro'),
    path('topImportersShydro/', views.topImportersShydro, name='topImportersShydro'),
    path('productCountShydro/', views.productCountShydro, name='productCountShydro'),
    path('kpiDetailsShydro/', views.kpiDetailsShydro, name='kpiDetailsShydro'),


    path('afficherDossImport/', views.afficherDossImport, name='afficherDossImport'),

    # Data Sanitizing
    path('dataSanitizing/', views.dataSanitizing, name='dataSanitizing'),
    path('data_duplicate/', views.data_duplicate, name='data_duplicate'),
    path('data_merge/', views.data_merge, name='data_merge'),


    # path('rapportActivite/data/', views.rapportActiviteData, name='rapportActiviteData'),

    # Generic reporting endpoints (used by rapportActiviteFirst.html)
    path('second/list/', views.reporting_second_list, name='your_second_endpoint_list'),
    path('second/delete/', views.reporting_second_delete, name='your_second_endpoint_delete'),
    path('second/example/', views.reporting_example_submit, name='your_example_endpoint'),

    # Rapport Activité detailed table (replicates DjangoTables2 RapportActivite)
    path('second/rapport-activite/', views.reporting_rapport_activite_list, name='your_rapport_activite_list'),





]
