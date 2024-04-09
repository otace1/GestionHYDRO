from django.urls import path

from accounts import views

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('userslist/', views.listeutilisateurs, name='userslist'),
    path('listeutilisateursResponse/', views.listeutilisateursResponse, name='listeutilisateursResponse'),

    path('detailsAffectationUtilisateur/<int:pk>', views.detailsAffectationUtilisateur, name='detailsAffectationUtilisateur'),
    path('detailsAffectationLabo/<int:pk>', views.detailsAffectationLabo, name='detailsAffectationLabo'),

    path('detailsaffectation/<int:pk>', views.detailsaffectation, name='detailsaffectation'),
    path('retireraffectationEntrepot/<int:pk>', views.retireraffectationEntrepot, name='retireraffectationEntrepot'),
    path('retireraffectationville/<int:pk>', views.retireraffectationville, name='retireraffectationville'),
    path('retireraffectationLabo/<int:pk>', views.retireraffectationLabo, name='retireraffectationLabo'),
    path('affectation_entrepot/', views.affectationentreprot, name='affectationentreprot'),
    path('affectation_laboratoire/', views.affectationlabo, name='affectationlabo'),
    path('affectation_role/', views.affectationrole, name='affectationrole'),
    path('affectation_ville/', views.affectationville, name='affectationville'),
    path('affectation_signature/', views.affectation_signature, name='affectation_signature'),
    path('usersadd/', views.ajoututilisateurs, name='usersadd'),
    path('delete/<int:pk>', views.effacerutilisateurs, name='delete_user'),
    path('edit/<int:pk>', views.editionutilisateurs, name='edit'),


    path('addUser/', views.addUser, name='addUser'),
    path('ajoutSignature/', views.ajoutSignature, name='ajoutSignature'),
    path('listeSignature/<int:pk>', views.listeSignature, name='listeSignature'),
    path('getSignature/<int:pk>', views.getSignature, name='getSignature'),


    # Signature
    path('sign/<int:pk>', views.sign_it, name='sign_it'),

    path('createToken/<int:pk>', views.createToken, name='createToken'), # Create Token

    #Privacy Policy
    path('privacy/', views.privacyPolicy, name='privacyPolicy'),


]
