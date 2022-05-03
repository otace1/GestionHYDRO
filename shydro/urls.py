from django.urls import path, re_path
# from django.conf.urls import re_
from . import views

urlpatterns = [

    path('', views.GestionCodification.affichageTableau, name='codification'),
    path('details/<int:pk>', views.GestionCodification.linedetails, name='details'),
    path('update/<int:pk>', views.GestionCodification.lineupdate, name='update'),
    #
    path('numdoss/<int:pk>', views.GestionCodification.numreq, name='numreq'),
    path('codecam/<int:pk>', views.GestionCodification.codecam, name='codecam'),

    path('', views.GestionResultatLabo.affichagetableauresultat, name='laboresult'),
    path('avaries/', views.GestionResultatLabo.affichagetableauavarie, name='avarie'),

    path('act/', views.GestionDecharger.gestionact, name='gestionact'),
    path('act/<int:pk>', views.GestionDecharger.printact, name='printact'),
    path('react/<int:pk>', views.GestionDecharger.reprintact, name='reprintact'),
    path('rechercheact/', views.GestionDecharger.rechercheact, name='rechercheact'),


    path('go/<int:pk>', views.GestionDecharger.godechargement, name='go'),

    # path('delete/<int:pk>', views.GestionCodification.linedelete, name='delete'),
    # path('search/',views.GestionCodification.search,name='search'),


]