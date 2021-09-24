from django.urls import path, include
from ads import views

urlpatterns = [

    path('', views.Dashboard.chartjs, name='dashboard'),

    path('statistiques/', views.Dashboard.statistiquesimportations, name='statistiques'),
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

]
