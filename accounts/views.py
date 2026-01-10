import base64
import datetime
import io
import json
import secrets
import string

from django.contrib.auth import (
    authenticate,
    login,
    logout,
)
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.db.models import Q, F
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from jsignature.utils import draw_signature
from openpyxl import Workbook

from accounts.models import *
from .services import log_action
from .forms import UserLoginForm, UserEdit, UserRegisterForm, Affectation_Entrepot, Affectation_Ville, SignatureForm, \
    Affectation_Role, Affectation_Labo
from .tables import ListeUtilisateurs, DetailsAffectation, DetailsVille, SignatureTable


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
                role = re.role_id

                # Roles frontière
                if role == 2:
                    return redirect('cargaison')
                else:
                    # Rôle administration
                    if role == 1 or role == 8:
                        return redirect('dashboard')
                    else:
                        # rôle HYDROCARBURES
                        if role == 7:
                            return redirect('tableaudeBordHydro')
                        else:
                            # rôle Encodeur entrepot
                            if role == 3:
                                return redirect('entrepot')
                            else:
                                # rôle reception au labo
                                if role == 4:
                                    return redirect('labo')
                                else:
                                    # rôle encodage labo
                                    if role == 5:
                                        return redirect('analyse')
                                    else:
                                        # rôle validation chef de service labo
                                        if role == 6:
                                            return redirect('validation1')
                                        else:
                                            # rôle validation chef de division labo
                                            if role == 10:
                                                return redirect('validation2')
                                            else:
                                                # rôle particulier Sans Labo
                                                if role == 9:
                                                    return redirect('entrepot')
                                                else:
                                                    if role == 11:
                                                        return redirect('codification')
                                                    else:
                                                        if role == 13:
                                                            return redirect('rapportActivite')

    # print('TEST LOGOUT')
    context = {
        'form': form
    }
    return render(request, template, context)


@login_required(login_url='login')
# Fontion pour logout les utilisateurs
def logout_user(request):

    # user = MyUser.objects.get(id=request.user)
    # UserActivityLog.objects.create(
    #     user=user,
    #     action="System logout",
    #     description="User logged out successfully",
    # )

    logout(request)
    return redirect('/')


@login_required(login_url='login')
# fonctions pour afficher la liste des utilisateurs
def listeutilisateurs(request):
    user = request.user
    role = user.role_id
    userForm = UserRegisterForm()
    affectationRol = Affectation_Role()
    affectationEntr = Affectation_Entrepot()
    affectationVil = Affectation_Ville()
    affectationLab = Affectation_Labo()
    sig_form = SignatureForm()

    if role == 1:
        template = 'accounts/userslist.html'
        context = {
            'form':userForm,
            'affectationRol':affectationRol,
            'affectationEntr':affectationEntr,
            'affectationVil':affectationVil,
            'affectationLab':affectationLab,
            'sig_form': sig_form,
            'roles': Roles.objects.all().order_by('role'),
        }
        return render(request, template,context)
    else:
        return redirect('logout')



@login_required(login_url='login')
@require_POST
def listeutilisateursResponse(request):
    user = request.user
    if user.role_id != 1:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # Base QuerySet
    base_qs = MyUser.objects.all()
    records_total = base_qs.count()

    # Get DataTables parameters
    try:
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 15))
    except (ValueError, TypeError):
        draw, start, length = 1, 0, 15

    # Filters
    search_value = request.POST.get('search[value]', '').strip()
    role_id = request.POST.get('role')
    status = request.POST.get('status')

    qs = base_qs

    if role_id:
        qs = qs.filter(role_id=role_id)

    if search_value:
        qs = qs.filter(
            Q(first_name__icontains=search_value) |
            Q(last_name__icontains=search_value) |
            Q(username__icontains=search_value)
        )
    
    records_filtered = qs.count()

    # Values to fetch
    qs = qs.values(
        'id', 'first_name', 'last_name', 'username', 'role__role', 'last_login',
        'fonction', 'poste', 'is_admin', 'is_staff'
    )

    # Export check
    export = request.POST.get('export')
    if export == 'excel':
        data = list(qs)
        workbook = Workbook()
        sheet = workbook.active
        
        # Headers
        header_row = ['ID UTILISATEUR', 'PRÉNOM', 'NOM', 'NOM D\'UTILISATEUR', 'NIVEAU DE DROITS', 'DERNIÈRE CONNEXION']
        sheet.append(header_row)

        # Data rows
        for row in data:
            sheet.append([
                row['id'],
                row['first_name'],
                row['last_name'],
                row['username'],
                row.get('role__role') or '-',
                row['last_login'].strftime('%d/%m/%Y %H:%M') if row['last_login'] else '-'
            ])

        excel_stream = io.BytesIO()
        workbook.save(excel_stream)
        excel_stream.seek(0)

        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="rapport_utilisateurs.xlsx"'
        return response

    # Pagination
    if length == -1:
        data = list(qs)
    else:
        data = list(qs[start:start + length])

    # Convert datetime to string for JSON serialization (optional, but good for consistency)
    # JsonResponse with DjangoJSONEncoder already does this, but we can do it manually if needed.

    return JsonResponse({
        'data': data,
        'draw': draw,
        'recordsTotal': records_total,
        'recordsFiltered': records_filtered,
    })



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
def addUser(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True},status=200)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors}, status=400)

    # Redirect for non-ajax requests or other HTTP methods
    return redirect('userslist')




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
        request.session['pk'] = pk
        template = 'accounts/profile.html'
        instance = get_object_or_404(MyUser, id=pk)
        table = DetailsAffectation(AffectationEntrepot.objects.filter(username_id=pk))
        # table1 = DetailsVille(AffectationVille.objects.filter(username__id=pk))
        table.paginate(page=request.GET.get('page', 1), per_page=15)
        # table1.paginate(page=request.GET.get('page', 1), per_page=15)
        form = UserEdit(request.POST or None, instance=instance, prefix='user')
        # form1 = Affectation_Entrepot()
        # form2 = Affectation_Ville()
        # form3 = SignatureForm(request.POST or None)
        url = request.session['url']

        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            return redirect(url)

        args = {
            'form': form,
            # 'form1': form1,
            'table': table,
            # 'table1': table1,
            # 'form2': form2,
            # 'form3':form3,
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
        try:
            # Check if the user exists
            user_to_delete = get_object_or_404(MyUser, id=pk)

            # Check for related records and delete if they exist
            if AffectationLaboratoire.objects.filter(userId=pk).exists():
                AffectationLaboratoire.objects.filter(userId=pk).delete()

            if AffectationVille.objects.filter(username_id=pk).exists():
                AffectationVille.objects.filter(username_id=pk).delete()

            if AffectationEntrepot.objects.filter(username_id=pk).exists():
                AffectationEntrepot.objects.filter(username_id=pk).delete()

            # Delete the user
            user_to_delete.delete()
            return JsonResponse({'status': 'Utilisateur et enregistrements associés supprimés avec succès'}, status=200)
        except MyUser.DoesNotExist:
            return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse(status=400)


@login_required(login_url='login')
@require_POST
def reset_password(request, pk):
    """
    Securely resets a user's password and returns the new temporary password.
    Restricted to Admin (role_id=1).
    """
    if request.user.role_id != 1:
        return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)

    try:
        target_user = get_object_or_404(MyUser, id=pk)

        # Generate a secure random password (14 characters)
        alphabet = string.ascii_letters + string.digits
        generated_password = ''.join(secrets.choice(alphabet) for i in range(14))

        # Update password using Django's best practices
        target_user.set_password(generated_password)
        target_user.save()

        # Audit logging
        log_action(
            request,
            action="PASSWORD_RESET",
            description=f"Admin a réinitialisé le mot de passe pour l'utilisateur : {target_user.username}",
            obj=target_user
        )

        return JsonResponse({
            'success': True,
            'password': generated_password,
            'username': target_user.username,
            'full_name': target_user.get_full_name()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



@login_required(login_url='login')
# fonction pour affectation dans les entrepots
def affectationentreprot(request):
    if request.method == 'POST':
        pk = request.POST.get('dataRow')
        entrepot = request.POST.get('entrepot')
        try:
            u = MyUser.objects.get(id=pk)
            e = Entrepot.objects.get(identrepot=entrepot)
            a = AffectationEntrepot(username=u, entrepot=e)
            a.save()
            return JsonResponse({'status': 200})
        except:
            return JsonResponse({'status': 400})




@login_required(login_url='login')
# fonction pour affectation dans les entrepots
def affectationlabo(request):
    if request.method == 'POST':
        pk = request.POST.get('dataRow')
        laboratoire = request.POST.get('laboratoire')
        print('TEST')
        try:
            user = MyUser.objects.get(id=pk)
            laboratoire = ListeLaboratoire.objects.get(idLaboratoire=laboratoire)
            ville = AffectationVille.objects.get(username_id=pk)
            ville = Ville.objects.get(idville=ville.ville_id)
            print('TEST')
            print(user.id)
            print(laboratoire.idLaboratoire)
            print(ville.idville)

            AffectationLaboratoire.objects.create(
                idLaboratoire=laboratoire,
                userId=user,
                ville=ville
            )

            # a = AffectationLaboratoire(
            #     idLaboratoire=laboratoire.idLaboratoire,
            #     userId=user.id,
            #     ville_id=ville.idville
            # )
            # a.save()
            return JsonResponse({'status': 200})
        except:
            return JsonResponse({'status': 400})

    return redirect('logout')




@login_required(login_url='login')
def affectationrole(request):
    if request.method == 'POST':
        try:
            pk = request.POST.get('dataRow')
            role = request.POST.get('role')
            u = MyUser.objects.get(id=pk)
            r = Roles.objects.get(idrole=role)
            u.role = r
            u.save(update_fields=['role'])
            return JsonResponse({'status': 200})
        except:
            return JsonResponse({'status': 400})




@login_required(login_url='login')
# fonction pour affectation dans les Ville
def affectationville(request):
    if request.method == 'POST':
        pk = request.POST.get('dataRow')
        ville = request.POST.get('ville')
        try:
            u = MyUser.objects.get(id=pk)
            v = Ville.objects.get(idville=ville)
            p = AffectationVille(username_id=u.id, ville_id=v.idville)
            p.save()
            return JsonResponse({'status': 200})
        except:
            return JsonResponse({'status': 400})



@login_required(login_url='login')
#Retrait des affectations entrepots
def retireraffectationEntrepot(request, pk):
    user = request.user
    role = user.role_id
    if role == 1:
        if request.method == 'GET':
            # print('TEST DELETE')
            # print(pk)
            object = AffectationEntrepot.objects.get(idaffectation_entrepot=pk)
            object.delete()
            return JsonResponse({'status': 200})
        else:
            return JsonResponse({'status': 400})
    else:
        return redirect('logout')



@login_required(login_url='login')
#Retrait des affectations entrepots
def retireraffectationLabo(request, pk):
    user = request.user
    role = user.role_id
    if role == 1:
        if request.method == 'GET':
            try:
                print('TEST DELETE')
                print(pk)
                o = AffectationLaboratoire.objects.get(
                    idAffectation=pk
                )
                o.delete()
                return JsonResponse({'status': 200})
            except:
                return JsonResponse({'status': 400})
        else:
            return JsonResponse({'status': 400})
    else:
        return redirect('logout')



@login_required(login_url='login')
# Retrait des affectations entrepots
def retireraffectationville(request, pk):
    user = request.user
    role = user.role_id
    if role == 1:
        try:
            object = AffectationVille.objects.get(idaffectation_ville=pk)
            object.delete()
            return JsonResponse({'status': 200})
        except AffectationVille.DoesNotExist:
            return JsonResponse({'status': 404, 'error': 'Assignment not found'})
        except Exception as e:
            return JsonResponse({'status': 500, 'error': str(e)})
    else:
        return redirect('logout')


@login_required(login_url='login')
def retireraffectationRole(request, pk):
    user = request.user
    role = user.role_id
    if role == 1:
        target_user = get_object_or_404(MyUser, id=pk)
        target_user.role = None
        target_user.save(update_fields=['role'])
        return JsonResponse({'status': 200})
    else:
        return JsonResponse({'status': 403})


@login_required(login_url='login')
# Affectation des signatures
def affectation_signature(request):
    template = 'accounts/profileville.html'
    table = SignatureTable(MyUser.objects.all())
    table.paginate(page=request.GET.get('page', 1), per_page=12)

    context = {
        'table': table,
    }
    return render(request, template, context)


@login_required(login_url='login')
def sign_it(request, pk):
    template = 'accounts/signit.html'
    form = SignatureForm()
    if form.is_valid():
        signature = form.cleaned_data.get('signature')
        if signature:
            # as an image
            signature_picture = draw_signature(signature)

    context = {'form': form}
    return render(request, template, context)


@login_required(login_url='login')
def createToken(request, pk):
    # Get the user instance or return a 404 if not found
    print('HIT')
    user = get_object_or_404(MyUser, pk=pk)

    # Check if a token already exists for the user
    if Token.objects.filter(user=user).exists():
        # Return a JsonResponse with an error message indicating token already exists
        print('TEST')
        print(Token.objects.filter(user=user))
        return JsonResponse({'error': 'Le jeton existe déjà pour cet utilisateur'}, status=400)
    else:
        # Create a new token for the user
        Token.objects.create(user=user)
        # Return a JsonResponse indicating successful token creation
        return JsonResponse({'message': 'Jeton créé avec succès'}, status=201)


@login_required(login_url='login')
@require_POST
def ajoutSignature(request):
    """
    Saves or updates a user signature.
    Supports both file upload and JSON data from jsignature.
    """
    if request.user.role_id != 1:
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    user_id = request.POST.get('dataRow')
    if not user_id:
        return JsonResponse({'error': 'ID utilisateur manquant'}, status=400)

    try:
        target_user = MyUser.objects.get(id=user_id)
    except MyUser.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)

    binary_data = None

    # Check if it's a drawn signature (jsignature JSON)
    signature_json = request.POST.get('signature')
    if signature_json:
        try:
            # Parse JSON string to Python list
            signature_data = json.loads(signature_json)
            # draw_signature converts list of lines to a PIL Image
            signature_img = draw_signature(signature_data)
            if signature_img:
                buffer = io.BytesIO()
                signature_img.save(buffer, format='PNG')
                binary_data = buffer.getvalue()
        except Exception as e:
            return JsonResponse({'error': f'Erreur lors du traitement de la signature dessinée : {str(e)}'}, status=400)

    # Check if it's an uploaded file
    elif 'image' in request.FILES:
        image_file = request.FILES['image']
        # Validate file size (e.g., max 2MB)
        if image_file.size > 2 * 1024 * 1024:
            return JsonResponse({'error': 'Fichier trop volumineux. La taille maximale est de 2 Mo.'}, status=400)
        # Validate file type
        if not image_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            return JsonResponse({'error': 'Type de fichier invalide. Veuillez télécharger un fichier PNG ou JPG.'}, status=400)
        binary_data = image_file.read()

    if not binary_data:
        return JsonResponse({'error': 'Aucune donnée de signature fournie'}, status=400)

    # Update or create
    SignaturesModel.objects.update_or_create(
        userId=target_user,
        defaults={'signatureData': binary_data}
    )

    return JsonResponse({'message': 'Signature enregistrée avec succès'}, status=200)


@login_required(login_url='login')
def getSignature(request, pk):
    """
    Fetches the signature for a user (pk is userId).
    """
    try:
        # Lookup by userId since it's OneToOne
        obj = SignaturesModel.objects.get(userId_id=pk)
        base64_data = base64.b64encode(obj.signatureData).decode('utf-8')
        return JsonResponse({
            'success': True,
            'base64_image': base64_data,
            'updated_at': obj.updated_at.strftime('%d/%m/%Y %H:%M')
        }, status=200)
    except SignaturesModel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Aucune signature trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)









@login_required(login_url='login')
def detailsAffectationUtilisateur(request,pk):
    # qs = MyUser.objects.filter(id=pk).annotate(
    #     roleaff=F('role__role'),
    #     nomentrepot=F('affectationentrepot__entrepot__nomentrepot'),
    #     denominationLaboratoire=F('affectationlaboratoire__idLaboratoire__denominationLaboratoire'),
    #     nomville=F('affectationentrepot__entrepot__ville__nomville')
    # ).values(
    #     'id',
    #     'first_name',
    #     'last_name',
    #     'roleaff',
    #     'nomentrepot',
    #     'denominationLaboratoire',
    #     'nomville'
    # )

    qs = AffectationEntrepot.objects.filter(username_id=pk).values(
        'username_id','idaffectation_entrepot',
        'username__first_name',
        'username__last_name',
        'username__role__role',
        'entrepot__nomentrepot',
        'entrepot__ville'
    )

    # Number of items to show per page
    items_per_page = 15

    # Initialize the Paginator with the QuerySet and the number of items per page
    paginator = Paginator(qs, items_per_page)

    # Get the current page number from the request's GET parameters
    draw = int(request.GET.get('draw', 1))  # Get the draw value for proper AJAX handling
    start = int(request.GET.get('start', 0))  # Get the starting index for pagination
    length = int(request.GET.get('length', items_per_page))  # Get the number of items per page

    # Calculate the current page number based on start and length
    current_page = (start // length) + 1

    try:
        # Get the current page from the Paginator
        page = paginator.page(current_page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), return an empty JSON response.
        return JsonResponse({'data': [], 'draw': draw, 'recordsTotal': 0, 'recordsFiltered': 0})

    # Convert the page object to a list of dictionaries
    data = list(page)

    # Return JSON response with the data
    return JsonResponse({
        'data': data,
        'draw': draw,
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
    })




@login_required(login_url='login')
def detailsAffectationLabo(request,pk):
    qs = AffectationLaboratoire.objects.filter(userId=pk).values(
        'userId_id',
        'userId__first_name',
        'userId__last_name',
        'userId__role__role',
        'idLaboratoire__denominationLaboratoire',
        'idAffectation'
    )

    # Number of items to show per page
    items_per_page = 15

    # Initialize the Paginator with the QuerySet and the number of items per page
    paginator = Paginator(qs, items_per_page)

    # Get the current page number from the request's GET parameters
    draw = int(request.GET.get('draw', 1))  # Get the draw value for proper AJAX handling
    start = int(request.GET.get('start', 0))  # Get the starting index for pagination
    length = int(request.GET.get('length', items_per_page))  # Get the number of items per page

    # Calculate the current page number based on start and length
    current_page = (start // length) + 1

    try:
        # Get the current page from the Paginator
        page = paginator.page(current_page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), return an empty JSON response.
        return JsonResponse({'data': [], 'draw': draw, 'recordsTotal': 0, 'recordsFiltered': 0})

    # Convert the page object to a list of dictionaries
    data = list(page)

    # Return JSON response with the data
    return JsonResponse({
        'data': data,
        'draw': draw,
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
    })



@login_required(login_url='login')
def detailsAffectationVille(request,pk):
    qs = AffectationVille.objects.filter(username_id=pk).values(
        'username_id',
        'username__first_name',
        'username__last_name',
        'username__role__role',
        'ville__nomville',
        'idaffectation_ville',
    )

    # Number of items to show per page
    items_per_page = 15

    # Initialize the Paginator with the QuerySet and the number of items per page
    paginator = Paginator(qs, items_per_page)

    # Get the current page number from the request's GET parameters
    draw = int(request.GET.get('draw', 1))  # Get the draw value for proper AJAX handling
    start = int(request.GET.get('start', 0))  # Get the starting index for pagination
    length = int(request.GET.get('length', items_per_page))  # Get the number of items per page

    # Calculate the current page number based on start and length
    current_page = (start // length) + 1

    try:
        # Get the current page from the Paginator
        page = paginator.page(current_page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), return an empty JSON response.
        return JsonResponse({'data': [], 'draw': draw, 'recordsTotal': 0, 'recordsFiltered': 0})

    # Convert the page object to a list of dictionaries
    data = list(page)

    # Return JSON response with the data
    return JsonResponse({
        'data': data,
        'draw': draw,
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
    })


@login_required(login_url='login')
def detailsAffectationRole(request, pk):
    target_user = get_object_or_404(MyUser, id=pk)
    data = []
    if target_user.role:
        data.append({
            'id': target_user.id,
            'role_name': target_user.role.role,
        })
    return JsonResponse({'data': data})


@login_required(login_url='login')
def privacyPolicy(request):
    template = 'privacyPolicy.html'
    context = {}
    return render(request,template,context)



@login_required(login_url='login')
def activityLog(request):
    template = 'activityLog.html'
    context = {}
    return render(request,template,context)


@login_required(login_url='login')
def activityLogResponse(request):
    """
    Enhanced activity log endpoint that primarily reads from AuditLog.
    Supports advanced filtering and optimized pagination for DataTables.
    """
    # Source toggle: default to AuditLog
    source = request.GET.get('source', 'audit')
    
    if source == 'activity':
        qs = UserActivityLog.objects.all().select_related('user')
        records_total = UserActivityLog.objects.count()
    else:
        qs = AuditLog.objects.all().select_related('actor')
        records_total = AuditLog.objects.count()

    # Advanced Filters
    q = request.GET.get('q') or request.GET.get('search[value]', '')
    user_filter = request.GET.get('user')
    action_filter = request.GET.get('action')
    module_filter = request.GET.get('module')
    ip_filter = request.GET.get('ip')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    only_mine = request.GET.get('only_mine') == '1'
    level_filter = request.GET.get('level')

    if source == 'activity':
        if q:
            qs = qs.filter(
                Q(user__username__icontains=q) |
                Q(username_snapshot__icontains=q) |
                Q(action__icontains=q) |
                Q(description__icontains=q) |
                Q(module__icontains=q) |
                Q(ip_address__icontains=q)
            )
        if user_filter:
            qs = qs.filter(Q(user__username__icontains=user_filter) | Q(username_snapshot__icontains=user_filter))
        if action_filter:
            qs = qs.filter(action__icontains=action_filter)
        if module_filter:
            qs = qs.filter(module__icontains=module_filter)
        if only_mine:
            qs = qs.filter(user=request.user)
    else:
        # AuditLog filters
        if q:
            qs = qs.filter(
                Q(actor__username__icontains=q) |
                Q(actor_username_snapshot__icontains=q) |
                Q(action__icontains=q) |
                Q(model_name__icontains=q) |
                Q(object_repr__icontains=q) |
                Q(ip_address__icontains=q)
            )
        if user_filter:
            qs = qs.filter(Q(actor__username__icontains=user_filter) | Q(actor_username_snapshot__icontains=user_filter))
        if action_filter:
            qs = qs.filter(action__icontains=action_filter)
        if module_filter:
            qs = qs.filter(model_name__icontains=module_filter)
        if only_mine:
            qs = qs.filter(actor=request.user)

    if ip_filter:
        qs = qs.filter(ip_address__icontains=ip_filter)
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)
    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)
    if level_filter:
        qs = qs.filter(status__icontains=level_filter)

    # Count after filtering
    records_filtered = qs.count()

    # Pagination
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 15))

    qs = qs.order_by('-timestamp')[start:start + length]

    # Format data
    data_list = []
    for log in qs:
        if source == 'activity':
            data_list.append({
                'id': log.id,
                'user__username': log.username_snapshot or (log.user.username if log.user else 'System'),
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'action': log.action,
                'description': log.description,
                'module': log.module or '',
                'ip_address': log.ip_address or '',
                'status': log.status,
            })
        else:
            # For AuditLog, construct description
            desc = f"{log.action} on {log.model_name}: {log.object_repr}"
            if log.action == 'UPDATE' and log.changes:
                changed_fields = ", ".join(log.changes.keys())
                desc += f" (Fields: {changed_fields})"
            
            data_list.append({
                'id': log.id,
                'user__username': log.actor_username_snapshot or (log.actor.username if log.actor else 'System'),
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'action': log.action,
                'description': desc,
                'module': log.model_name,
                'ip_address': log.ip_address or '',
                'status': log.status,
                'changes': log.changes,
                'new_state': log.new_state,
                'old_state': log.old_state,
                'request_id': log.request_id,
            })

    return JsonResponse({
        'draw': draw,
        'recordsTotal': records_total,
        'recordsFiltered': records_filtered,
        'data': data_list,
    })



