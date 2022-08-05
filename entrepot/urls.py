from django.urls import path
from . import views

urlpatterns = [
    path('', views.GestionEchantillonage.tableauechantillonnage, name='entrepot'),
    path('echantilloner/', views.GestionEchantillonage.echantilloner, name='echantilloner'),
    path('rechercher/', views.GestionEchantillonage.rechercheqrcode, name='rechercher'),
    path('rechercherre/', views.GestionEchantillonage.rechercherre, name='rechercherre'),
    path('dechargement/', views.GestionDechargement.tableaudechargement, name='dechargement'),
    path('rapport/<int:pk>', views.ImpressionRapport, name='rapport'),

    # Compteur
    path('c1/', views.GestionEchantillonage.c1, name='c1'),
    path('c2/', views.GestionEchantillonage.c2, name='c2'),

    path('echantillonage/<int:pk>', views.echantillonage, name='echantillonage'),  # Echantillonnage nouveau formulaire
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
    # Shore
    path('shore/<int:pk>', views.shorebefore, name='shore'),
    path('shoreinspection/', views.shoreinspectionbefore, name='shore-inspection'),
    path('shoredetails/<int:pk>', views.shoredetails, name='shore-details'),
    path('shoredelete/<int:pk>', views.shoredelete, name='shore-delete'),
    path('shoreupdate/<int:pk>', views.shoreupdate, name='shore-update'),

]
