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
    path('enAttenteDechargement/', views.enAttenteDechargement, name='enAttenteDechargement'),
    path('enAttenteResultatLabo/', views.enAttenteResultatLabo, name='enAttenteResultatLabo'),
    path('enAttenteReceptionLabo/', views.enAttenteReceptionLabo, name='enAttenteReceptionLabo'),
    path('enAttenteInspection/', views.enAttenteInspection, name='enAttenteInspection'),
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
    path('regularisationDestination/', views.regularisationDestination, name='regularisationDestination'),
    path('changementNature/', views.changementNature, name='changementNature'),
    path('changementImportateur/', views.changementImportateur, name='changementImportateur'),
    path('transbordement/', views.transbordement, name='transbordement'),
    path('pertes/<int:pk>', views.pertes, name='pertes'),

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
    #





]
