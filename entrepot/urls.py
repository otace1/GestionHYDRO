from django.urls import path
from . import views


urlpatterns = [

    path('', views.GestionEchantillonage.tableauechantillonnage, name='entrepot'),
    path('echantilloner/', views.GestionEchantillonage.echantilloner, name='echantilloner'),
    path('rechercher/', views.GestionEchantillonage.rechercheqrcode, name='rechercher'),
    path('dechargement/', views.GestionDechargement.tableaudechargement, name='dechargement'),
    path('decharger/', views.GestionDechargement.dechargementcargaison, name='decharger'),
    # path('cargaisondech/', views.GestionRapport.cargaisondecharger, name='rapport'),

    #Compteur
    path('c1/', views.GestionEchantillonage.c1, name='c1'),
    path('c2/', views.GestionEchantillonage.c2, name='c2')


]