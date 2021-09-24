from django.contrib.auth import (
    authenticate,
    login,
    logout,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import *
from .forms import UserLoginForm, UserEdit, UserRegisterForm, Affectation_Entrepot, Affectation_Ville
from .tables import ListeUtilisateurs, DetailsAffectation



# Fonction pour authemntifier les utilisateurs
def login_user(request):
    template = 'accounts/login.html'
    next = request.GET.get('next')
    form = UserLoginForm(request.POST or None)
    username = password = ''

    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                re = request.user
                # Roles frontière
                if re.role_id == 2:
                    return redirect('cargaison')
                else:
                    # Rôle administration
                    if re.role_id == 1 or re.role_id == 8 :
                        return redirect('dashboard')
                    else:
                        # rôle HYDROCARBURES
                        if re.role_id == 7:
                            return redirect('dashboard')
                        else:
                            # rôle Encodeur entrepot
                            if re.role_id == 3 :
                                return redirect('entrepot')
                            else:
                                # rôle reception au labo
                                if re.role_id == 4:
                                    return redirect('labo')
                                else:
                                    # rôle encodage labo
                                    if re.role_id == 5:
                                        return redirect('analyse')
                                    else:
                                        # rôle validation chef de service labo
                                        if re.role_id == 6:
                                            return redirect('validation1')
                                        else:
                                            # rôle validation chef de division labo
                                            if re.role_id == 'v2':
                                                return redirect('validation2')
                                            else:
                                                # rôle particulier
                                                if re.role_id == 9 :
                                                    return redirect('entrepot')
    context = {
        'form': form
    }
    return render(request, template, context)


@login_required(login_url='login')
# Fontion pour logout les utilisateurs
def logout_user(request):
    logout(request)
    return redirect('/')


@login_required(login_url='login')
# fonctions pour afficher la liste des utilisateurs
def listeutilisateurs(request):
    user = request.user
    role = user.role_id
    if role == 1:
        template = 'accounts/userslist.html'
        table = ListeUtilisateurs(MyUser.objects.all())
        table.paginate(page=request.GET.get('page', 1), per_page=15)
        return render(request, template, {'users': table})
    else:
        return redirect('logout')


@login_required(login_url='login')
# fonction pour ajout des utilisateurs
def ajoututilisateurs(request):
    user = request.user
    role = user.role_id
    if role == 1:
        template = 'accounts/usersadd.html'
        if request.method == 'POST':
            form = UserRegisterForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('userslist')
        else:
            form = UserRegisterForm()
        return render(request, template, {'form': form})
    else:
        return redirect('logout')

@login_required(login_url='login')
# Fonction details des affectations entrepots
def detailsaffectation(request,pk):
    user = request.user
    role = user.role_id
    if role == 1:
        template = 'accounts/detailsaffectation.html'
        table = DetailsAffectation(AffectationEntrepot.objects.filter(username_id=pk))
        table.paginate(page=request.GET.get('page', 1), per_page=15)
        args = {'table':table}
        return render(request, template, args)
    else:
        return redirect('logout')


@login_required(login_url='login')
# Fonction pour editer les utilisateurs
def editionutilisateurs(request, pk):
    user = request.user
    role = user.role_id
    if role == 1:
        request.session['url'] = request.get_full_path()
        template = 'accounts/profile.html'
        instance = get_object_or_404(MyUser, id=pk)
        table = DetailsAffectation(AffectationEntrepot.objects.filter(username_id=pk))
        table.paginate(page=request.GET.get('page', 1), per_page=15)
        form = UserEdit(request.POST or None, instance=instance, prefix='user')
        form1 = Affectation_Entrepot()
        url = request.session['url']

        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            return redirect(url)

        args = {
            'form': form,
            'form1': form1,
            'table': table
        }
        return render(request, template, args)
    else:
        return redirect('logout')


@login_required(login_url='login')
# Fonction pour effacer un utilisateurs
def effacerutilisateurs(request, pk):
    user = request.user
    role = user.role_id
    if role == 1:
        object = MyUser.objects.get(id=pk)
        object.delete()
        return redirect('userslist')
    else:
        return redirect('logout')


@login_required(login_url='login')
# fonction pour affectation dans les entrepots
def affectationentreprot(request):
    user = request.user
    role = user.role_id
    if role == 1:
        url = request.session['url']
        template = 'accounts/profile.html'
        form = Affectation_Entrepot()
        if request.method == 'POST':
            username = request.POST['username']
            entrepot = request.POST['entrepot']
            p = AffectationEntrepot(username_id=username, entrepot_id=entrepot)
            p.save()
            return redirect(url)
        else:
            return render(request, template, {'form': form})
    else:
        return redirect('logout')


@login_required(login_url='login')
# fonction pour affectation dans les Ville
def affectationville(request):
    user = request.user
    role = user.role_id
    if role == 1:
        template = 'accounts/profileville.html'
        form = Affectation_Ville()
        if request.method == 'POST':
            username = request.POST['username']
            ville = request.POST['ville']
            p = AffectationVille(username_id=username, ville_id=ville)
            p.save()
            return redirect('affectationville')
        else:
            return render(request, template, {'form': form})
    else:
        return redirect('logout')


@login_required(login_url='login')
#Retrait des affectations entrepots
def retireraffectation(request, pk):
    user = request.user
    role = user.role_id
    if role == 1:
        url = request.session['url']
        object = AffectationEntrepot.objects.get(idaffectation_entrepot=pk)
        object.delete()
        return redirect(url)
    else:
        return redirect('logout')


