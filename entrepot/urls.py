from django.urls import path
from . import views

urlpatterns = [
    path('', views.tableauechantillonnage, name='entrepot'),
    path('pending/', views.cargaisons_pending, name='cargaisons_pending'),
    # path('cargaison/status/', views.cargaisons_status_requisition, name='cargaisons_status_requisition'),
    path('sampling/', views.record_sampling, name='record_sampling'),

    #Ajout recent
    path("sampling/<int:pk>/report.pdf", views.sampling_report_pdf, name="sampling_report"),

    # path('echantilloner/', views.GestionEchantillonage.echantilloner, name='echantilloner'),
    # path('rechercher/', views.GestionEchantillonage.rechercheqrcode, name='rechercher'),
    # path('rechercherre/', views.GestionEchantillonage.rechercherre, name='rechercherre'),
    # path('dechargement/', views.GestionDechargement.tableaudechargement, name='dechargement'),
    # path('dechargement/response', views.GestionDechargement.tableauDechargementResponse, name='tableauDechargementResponse'),
    # path('rapport/<int:pk>', views.impressionRapport, name='rapport'),
    path('rapport/<int:pk>', views.impressionRapport, name='rapport'),
    path('impressionRe/<int:pk>', views.impressionRe, name='impressionRe'),

    # # Compteur
    # path('c1/', views.GestionEchantillonage.c1, name='c1'),
    # path('c2/', views.GestionEchantillonage.c2, name='c2'),

    # path('echantillonage/', views.echantillonage, name='echantillonage'),  # Echantillonnage nouveau formulaire
    # path('decharger/<int:pk>', views.dechargement, name='decharger'),  # Echantillonnage nouveau formulaire

    # Rapport d'echantillonage
    path('rapportechantillonage/<int:pk>', views.rapportechantillonage, name='rapportechantillonage'),
    path('printcert/<int:pk>', views.impressionCert, name='printcert'),

    # Seals Inspections
    path('seal/', views.sealinspection, name='seal-inspection'),
    path('detailseals/<int:pk>', views.detailseals, name='seal-details'),
    path('seals/<int:pk>', views.seals, name='seals'),
    path('choicetype/<int:pk>', views.choiceoftype, name='choiceoftype'),
    path('delete/<int:pk>', views.sealsdelete, name='sealsdelete'),
    path('update/<int:pk>', views.updateseals, name='sealsupdate'),

    # Tanker Inspection
    path('tanker/', views.tankerinspection, name='tanker-inspection'),
    path('compartiment/<int:pk>', views.compartiment, name='compartiment'),
    path('detailscompartiment/<int:pk>', views.detailscompartiment, name='compartiment-details'),
    path('compartimentinspection/', views.compartimentinspection, name='compartiment-inspection'),
    path('compartiment/delete/<int:pk>', views.compartimentdelete, name='compartimentdelete'),
    path('compartiment/update/<int:pk>', views.updatecompartiment, name='compartimentupdate'),
    path('meterafter/', views.meterafter, name='meterafter'),

    #Fonction for Kalemie particularity
    path('appurement_vol/', views.appurement_vol, name='appurement_vol'),


    # Shore
    path('shore/<int:pk>', views.shoreinspection, name='shore'),
    path('shore/inspection/', views.shore, name='shore-insp'),
    path('shore/tank/<int:pk>', views.shoretankbefore, name='shore-inspection'),
    path('shoredetails/<int:pk>', views.shoredetails, name='shore-details'),
    path('shoredelete/<int:pk>', views.shoredelete, name='shore-delete'),
    path('shoreupdate/<int:pk>', views.shoreupdate, name='shore-update'),

    # Shore After
    path('shore/inspection/after', views.shoreafter, name='shore-insp-after'),
    path('shore/tank/after/<int:pk>', views.shoretankafter, name='shore-inspection-after'),
    path('shoredetails/after/<int:pk>', views.shoredetailsafter, name='shore-details-after'),
    path('shoredelete/after/<int:pk>', views.shoredeleteafter, name='shore-delete-after'),
    path('shoreupdate/after/<int:pk>', views.shoreupdateafter, name='shore-update-after'),

    # Rapports
    path('inspection/', views.tableaurapports, name='tableaurapports'),
    path('inspection/response/', views.responseTableauRapports, name='responseTableauRapports'),

    # Report Validity Check
    # path('check/', views.reportCheck, name='reportCheck'),
    #
    # Nature du produit
    # path('nature/<int:pk>', views.natureProduit, name='natureProduit'),

    path('nonconforme/', views.affichageProduitNonConforme, name='affichageProduitNonConforme'),  # Non conforme
    path('affichageEnAttenteRequisition/', views.affichageEnAttenteRequisition, name='affichageEnAttenteRequisition'),
    # En attente de requisition

    #Correction de la non conformite declarative
    # path('correctionNonConformite/<int:pk>', views.correctionNonConformite, name='correctionConformiteProduit'),  # Non conforme

    #Inspection
    path('inspection/<int:pk>', views.inspection, name='inspection'),
    path('affichageInspection/', views.affichageInspection, name='affichageInspection'), #En Attente d'inspection
    path('marquageInspectionWeb/', views.marquageInspectionWeb, name='marquageInspectionWeb'), #Marquer comme Inspecter

    #View pdf data
    path('view_pdf/', views.view_pdf, name='view_pdf'),

    #NonConformeGestion
    path('consignatedOk/<int:pk>', views.consignatedOk, name='consignatedOk'),
    path('refouleOk/<int:pk>', views.refouleOk, name='refouleOk'),


    #Ajout
    path("workbench/", views.workbench_list, name="workbench_list"),
    # Separate endpoints per KPI card
    path("workbench/requisition/", views.workbench_requisition, name="wb_requisition"),
    path("workbench/inspection/", views.workbench_inspection, name="wb_inspection"),
    path("workbench/conformes/", views.workbench_conformes, name="wb_conformes"),
    path("workbench/reports/", views.workbench_reports, name="wb_reports"),

    # path("inspection/compartiment/<int:pk>/details/", views.compartiment, name="compartiment-details"),
    # Wizard POST + Start page
    path("inspection/wizard/<int:pk>/post/", views.inspection_wizard_post, name="inspection_wizard_post"),
    path("inspection/wizard/<int:pk>/finalize/", views.inspection_wizard_finalize, name="inspection_wizard_finalize"),
    path("inspection/start/<int:pk>/", views.inspection_start, name="inspection_start"),
    # Allow no-trailing-slash variant (some environments strip it)
    path("inspection/start/<int:pk>", views.inspection_start),



]
