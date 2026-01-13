from django.urls import path

from accounts import views

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('userslist/', views.listeutilisateurs, name='userslist'),
    path('listeutilisateursResponse/', views.listeutilisateursResponse, name='listeutilisateursResponse'),

    path('detailsAffectationUtilisateur/<int:pk>', views.detailsAffectationUtilisateur, name='detailsAffectationUtilisateur'),
    path('detailsAffectationLabo/<int:pk>', views.detailsAffectationLabo, name='detailsAffectationLabo'),
    path('detailsAffectationVille/<int:pk>', views.detailsAffectationVille, name='detailsAffectationVille'),
    path('detailsAffectationRole/<int:pk>', views.detailsAffectationRole, name='detailsAffectationRole'),

    path('detailsaffectation/<int:pk>', views.detailsaffectation, name='detailsaffectation'),
    path('retireraffectationEntrepot/<int:pk>', views.retireraffectationEntrepot, name='retireraffectationEntrepot'),
    path('retireraffectationville/<int:pk>', views.retireraffectationville, name='retireraffectationville'),
    path('retireraffectationLabo/<int:pk>', views.retireraffectationLabo, name='retireraffectationLabo'),
    path('retireraffectationRole/<int:pk>', views.retireraffectationRole, name='retireraffectationRole'),
    path('affectation_entrepot/', views.affectationentreprot, name='affectationentreprot'),
    path('affectation_laboratoire/', views.affectationlabo, name='affectationlabo'),
    path('affectation_role/', views.affectationrole, name='affectationrole'),
    path('affectation_ville/', views.affectationville, name='affectationville'),
    path('affectation_signature/', views.affectation_signature, name='affectation_signature'),
    path('usersadd/', views.ajoututilisateurs, name='usersadd'),
    path('delete/<int:pk>', views.effacerutilisateurs, name='delete_user'),
    path('reset-password/<int:pk>/', views.reset_password, name='reset_password'),
    path('edit/<int:pk>', views.editionutilisateurs, name='edit'),


    path('addUser/', views.addUser, name='addUser'),
    path('ajoutSignature/', views.ajoutSignature, name='ajoutSignature'),
    path('getSignature/<int:pk>/', views.getSignature, name='getSignature'),


    # Signature
    path('sign/<int:pk>', views.sign_it, name='sign_it'),

    path('createToken/<int:pk>/', views.createToken, name='createToken'), # Create Token

    #Privacy Policy
    path('privacy/', views.privacyPolicy, name='privacyPolicy'),
    path('help/', views.help_guide, name='help_guide'),

    path('activityLog/', views.activityLog, name='activityLog'),
    path('activityLogResponse/', views.activityLogResponse, name='activityLogResponse'),
    path('activityLogPurge/', views.activityLogPurge, name='activityLogPurge'),
    path('task-status/<str:task_id>/', views.get_task_status, name='task_status'),
    path('session-keep-alive/', views.session_keep_alive, name='session_keep_alive'),


]
