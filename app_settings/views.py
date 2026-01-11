from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, get_user_model
from .forms import UserProfileForm, BureauDGDAForm, BanqueForm, LiquidationModelForm
from enreg.models import Cargaison, Importateur, Entrepot, BureauDGDA, Banques, LiquidationModel
import django
import sys
import platform

User = get_user_model()

@login_required(login_url='login')
def app_settings(request):
    user = request.user
    
    profile_form = UserProfileForm(instance=user)
    password_form = PasswordChangeForm(user=user)
    bureau_form = BureauDGDAForm()
    banque_form = BanqueForm()
    modele_form = LiquidationModelForm()
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = UserProfileForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Votre profil a été mis à jour avec succès.")
                return redirect('app_settings')
        
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, "Votre mot de passe a été changé avec succès.")
                return redirect('app_settings')
            else:
                messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        
        elif 'clear_cache' in request.POST:
            if user.is_admin:
                cache.clear()
                messages.success(request, "Le cache système a été vidé.")
            else:
                messages.error(request, "Vous n'avez pas les permissions pour effectuer cette action.")
            return redirect('app_settings')

        # Reference Data Management
        elif 'add_bureau' in request.POST:
            if user.is_admin:
                form = BureauDGDAForm(request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Bureau ajouté avec succès.")
                return redirect('/settings/?tab=referentials')
        
        elif 'edit_bureau' in request.POST:
            if user.is_admin:
                instance = get_object_or_404(BureauDGDA, pk=request.POST.get('pk'))
                form = BureauDGDAForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Bureau mis à jour.")
                return redirect('/settings/?tab=referentials')

        elif 'delete_bureau' in request.POST:
            if user.is_admin:
                instance = get_object_or_404(BureauDGDA, pk=request.POST.get('pk'))
                instance.delete()
                messages.success(request, "Bureau supprimé.")
            return redirect('/settings/?tab=referentials')

        elif 'add_banque' in request.POST:
            if user.is_admin:
                form = BanqueForm(request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Banque ajoutée avec succès.")
                return redirect('/settings/?tab=referentials')

        elif 'edit_banque' in request.POST:
            if user.is_admin:
                instance = get_object_or_404(Banques, pk=request.POST.get('pk'))
                form = BanqueForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Banque mise à jour.")
                return redirect('/settings/?tab=referentials')

        elif 'delete_banque' in request.POST:
            if user.is_admin:
                instance = get_object_or_404(Banques, pk=request.POST.get('pk'))
                instance.delete()
                messages.success(request, "Banque supprimée.")
            return redirect('/settings/?tab=referentials')

        elif 'add_modele' in request.POST:
            if user.is_admin:
                form = LiquidationModelForm(request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Modèle de liquidation ajouté.")
                return redirect('/settings/?tab=referentials')

        elif 'edit_modele' in request.POST:
            if user.is_admin:
                instance = get_object_or_404(LiquidationModel, pk=request.POST.get('pk'))
                form = LiquidationModelForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Modèle mis à jour.")
                return redirect('/settings/?tab=referentials')

        elif 'delete_modele' in request.POST:
            if user.is_admin:
                instance = get_object_or_404(LiquidationModel, pk=request.POST.get('pk'))
                instance.delete()
                messages.success(request, "Modèle supprimé.")
            return redirect('/settings/?tab=referentials')

    # System info
    system_info = {
        'django_version': django.get_version(),
        'python_version': sys.version,
        'os': platform.system() + " " + platform.release(),
        'server_time': django.utils.timezone.now(),
    }
    
    # Statistics for admins
    stats = {}
    bureaus = []
    banques = []
    modeles = []
    
    if user.is_admin:
        stats = {
            'cargaisons_count': Cargaison.objects.count(),
            'importateurs_count': Importateur.objects.count(),
            'entrepots_count': Entrepot.objects.count(),
            'users_count': User.objects.count(),
        }
        bureaus = BureauDGDA.objects.all().order_by('codebureau')
        banques = Banques.objects.all().order_by('nombanque')
        modeles = LiquidationModel.objects.all().order_by('liquidationModel')
    
    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'bureau_form': bureau_form,
        'banque_form': banque_form,
        'modele_form': modele_form,
        'bureaus': bureaus,
        'banques': banques,
        'modeles': modeles,
        'system_info': system_info,
        'stats': stats,
        'active_tab': request.GET.get('tab', 'profile')
    }
    
    return render(request, 'app_settings.html', context)