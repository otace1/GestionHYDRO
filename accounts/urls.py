from django.urls import path

from accounts import views

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('userslist/', views.listeutilisateurs, name='userslist'),
    path('detailsaffectation/<int:pk>', views.detailsaffectation, name='detailsaffectation'),
    path('retireraffectation/<int:pk>', views.retireraffectation, name='retireraffectation'),
    path('affectation_entrepot/', views.affectationentreprot, name='affectationentreprot'),
    path('affectation_ville/', views.affectationville, name='affectationville'),
    path('affectation_role/', views.affectationville, name='affectationville'),
    path('usersadd/', views.ajoututilisateurs, name='usersadd'),
    path('delete/<int:pk>', views.effacerutilisateurs, name='delete_user'),
    path('edit/<int:pk>', views.editionutilisateurs, name='edit'),

]
