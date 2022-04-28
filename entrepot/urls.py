from django.urls import path
from . import views

urlpatterns = [
    path('', views.GestionEchantillonage.tableauechantillonnage, name='entrepot'),
    path('echantilloner/', views.GestionEchantillonage.echantilloner, name='echantilloner'),
    path('rechercher/', views.GestionEchantillonage.rechercheqrcode, name='rechercher'),
    path('rechercherre/', views.GestionEchantillonage.rechercherre, name='rechercherre'),
    path('dechargement/', views.GestionDechargement.tableaudechargement, name='dechargement'),
    # path('decharger/<int:pk>', views.GestionDechargement.dechargementcargaison, name='decharger'),
    path('rapport/<int:pk>', views.ImpressionRapport, name='rapport'),

    # Compteur
    path('c1/', views.GestionEchantillonage.c1, name='c1'),
    path('c2/', views.GestionEchantillonage.c2, name='c2'),

    path('echantillonage/<int:pk>', views.echantillonage, name='echantillonage'),  # Echantillonnage nouveau formulaire
    path('decharger/<int:pk>', views.dechargement, name='decharger'),  # Echantillonnage nouveau formulaire

    # Rapport d'echantillonage
    path('rapportechantillonage/<int:pk>', views.rapportechantillonage, name='rapportechantillonage'),
    path('printcert/<int:pk>', views.impressionCert, name='printcert'),

]
