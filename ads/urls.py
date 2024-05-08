from django.urls import path

from ads import views

urlpatterns = [

    path('', views.Dashboard.chartjs, name='dashboard'),

    # path('statistiques/', views.Dashboard.statistiquesimportations, name='statistiques'),
    path('statj/', views.statj, name='statj'),
    path('statProduct/', views.statproduction, name='statProd'),
    path('statEncaissement/', views.statencaissement, name='statencaissement'),
    path('export_import/', views.export_excel, name='export_import'),
    path('export_prod/', views.export_excel_prod, name='export_excel_prod'),
    path('export_enc/', views.export_excel_encaiss, name='export_excel_encaiss'),
    path('syntimpor/', views.synthese_importation, name='synthese_importation'),
    path('syntprod/', views.synthese_production, name='synthese_production'),
    path('syntencai/', views.synthese_encaissement, name='synthese_encaissement'),

    path('entrepot/', views.gestionentrepot, name='gest_entrepot'),
    path('entrepot/add/', views.addentrepot, name='add_entrepot'),
    path('entrepot/del/<int:pk>', views.deleteentrepot, name='del_entrepot'),
    path('entrepot/edit/<int:pk>', views.editentrepot, name='edit_entrepot'),

    path('importateur/add/', views.addimportateur, name='add_importateur'),
    path('importateur/', views.gestionimportateur, name='gest_importateur'),
    path('importateur/del<int:pk>', views.deleteimportateur, name='del_importateur'),
    path('importateur/edit<int:pk>', views.editimportateur, name='edit_importateur'),

    path('frontiere/', views.gestionfrontiere, name='gest_frontiere'),
    path('frontiere/add', views.addfrontiere, name='add_frontiere'),
    path('frontiere/del/<int:pk>', views.delfrontiere, name='del_frontiere'),
    path('frontiere/edit/<int:pk>', views.editfrontiere, name='edit_frontiere'),

    path('produit/add', views.addproduit, name='add_produit'),
    path('produit/', views.gestionproduit, name='gest_produit'),
    path('produit/del/<int:pk>', views.delproduit, name='del_produit'),
    path('produit/edit/<int:pk>', views.editproduit, name='edit_produit'),

    path('upload-cvs/cargaison', views.uploadcargaison, name='upload_cargaison'),
    path('upload-cvs/sydonia', views.uploadsydonia, name='upload_sydonia'),
    path('upload-cvs/importateur', views.uploadimportateur, name='upload_importateur'),
    path('upload-cvs/entrepot', views.uploadentrepot, name='upload_entrepot'),
    path('upload-cvs/ville', views.uploadville, name='upload_ville'),

    path('rapport/brut/', views.rapportBrut, name='rapportBrut'),
    path('rapport/brutEx/', views.rapportBrutExport, name='rapportBrutExport'),
    path('rapport/filtres/', views.rapportFiltres, name='rapportFiltres'),
    path('rapport/brutJ/', views.rapportBrutJournalier, name='rapportBrutJournalier'),
    path('rapport/response/', views.rapportBrutResponse, name='rapportBrutResponse'),
    path('rapport/responseExport/', views.rapportBrutResponse, name='exportRapportBrutResponse'),
    path('rapport/export/', views.rapportBrutResponseExport, name='rapportBrutResponseExport'),

    path('rapport/brut/echantillonnage/', views.rapportBrutEchantillonnage, name='rapportBrutEchantillonnage'),
    path('rapport/brut/analyse/', views.rapportBrutAnalyse, name='rapportBrutAnalyse'),

    path('rapport/brut/inspection/', views.rapportBrutInspection, name='rapportBrutInspection'),
    path('chartJs/', views.chartJsGraph, name='chartJs'),

    path('rapport/brut/dechargement/', views.rapportBrutDechargement, name='rapportBrutDechargement'),

    path('response/brut/journalier/', views.responseBrutJournalier, name='responseBrutJournalier'),
    path('response/brut/journalier/', views.responseBrutJournalier, name='exportBrutJournalier'),
    path('response/brut/echantillonnage/', views.responseRapportBrutEchantillonnage, name='responseRapportBrutEchantillonnage'),
    path('response/brut/echantillonnage/', views.responseRapportBrutEchantillonnage, name='exportBrutEchantillonnage'),
    path('response/brut/analyse/', views.responseRapportBrutAnalyse, name='responseRapportBrutAnalyse'),
    path('response/brut/analyse/', views.responseRapportBrutAnalyse, name='exportRapportBrutAnalyse'),
    path('response/brut/inspection/', views.responseRapportBrutInspection, name='responseRapportBrutInspection'),
    path('response/brut/inspection/', views.responseRapportBrutInspection, name='exportRapportBrutInspection'),
    path('response/brut/dechargement/', views.responseRapportBrutDechargement, name='responseRapportBrutDechargement'),
    path('response/brut/dechargement/', views.responseRapportBrutDechargement, name='exportRapportBrutDechargement'),
    path('response/brut/attenteReception/', views.rapportAttenteReception, name='rapportAttenteReception'),
    path('response/brut/attenteReception/rsp/', views.responseRapportattenteReception, name='responseRapportattenteReception'),


    path('response/latest/', views.lastRecords, name='lastRecords'),
    path('response/products/', views.productCount, name='productCount'),
    path('response/topImporters/', views.topImporters, name='topImporters'),


    path('document/getDocuments/', views.getDocuments, name='getDocuments'),





]
