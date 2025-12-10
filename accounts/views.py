import base64
import io

from django.contrib.auth import (
    authenticate,
    login,
    logout, update_session_auth_hash,
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.db.models import Q, F
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from jsignature.utils import draw_signature
from xlsxwriter import Workbook

from accounts.models import *
from .forms import UserLoginForm, UserEdit, UserRegisterForm, Affectation_Entrepot, Affectation_Ville, SignatureForm, \
    Affectation_Role, Affectation_Labo, CustomPasswordChangeForm
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

                #Activity Log
                UserActivityLog.objects.create(
                    user=re,
                    action="System login",
                    description="User logged in successfully",
                )

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
    userForm = UserRegisterForm(request.POST)
    affectationRol = Affectation_Role()
    affectationEntr = Affectation_Entrepot()
    affectationVil = Affectation_Ville()
    affectationLab = Affectation_Labo()

    if role == 1:
        template = 'accounts/userslist.html'
        context = {
            'form':userForm,
            'affectationRol':affectationRol,
            'affectationEntr':affectationEntr,
            'affectationVil':affectationVil,
            'affectationLab':affectationLab,
        }
        return render(request, template,context)
    else:
        return redirect('logout')



@login_required(login_url='login')
# fonctions pour afficher la liste des utilisateurs
def listeutilisateursResponse(request):
    user = request.user
    role = user.role_id

    if role == 1:
        qs = MyUser.objects.all().values(
            'id','first_name','last_name','username','role__role','last_login'
                                        )
        # Get the search value from the request's GET parameters
        search_value = request.GET.get('search[value]', '')

        # Apply search filter to the QuerySet
        if search_value:
            qs = qs.filter(
                Q(first_name__icontains=search_value) |
                Q(last_name__icontains=search_value) |
                Q(username__icontains=search_value)
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

        # Check if it's an AJAX request and if the export flag is set
        # Check if it's an AJAX request and if the export flag is set
        export = request.GET.get('export', None)
        if export == 'excel':
            # Retrieve all data (no lazy pagination) and store it in a list
            data = list(qs)

            # Create a new Excel workbook
            workbook = Workbook()
            sheet = workbook.active

            # Write headers to the Excel file
            header_row = ['USER ID', 'FIRST NAME', 'LAST NAME', 'USERNAME', 'APP.RIGHT LVL', 'DERNIERE CONNEXION']

            # Combine header and data rows using zip
            all_rows = [header_row] + [
                [
                    row['id'],
                    row['first_name'],
                    row['last_name'],
                    row['username'],
                    row['role__role'],
                    row['last_login'],
                ] for row in data
            ]

            # Write data rows to the Excel file
            for row in all_rows:
                sheet.append(row)

            # Create an in-memory stream to hold the Excel file data
            excel_stream = io.BytesIO()
            workbook.save(excel_stream)
            excel_stream.seek(0)

            # Prepare the response to return the Excel file
            response = HttpResponse(excel_stream,
                                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="rapport.xlsx"'
            return response

        # Return JSON response with the data
        return JsonResponse({
            'data': data,
            'draw': draw,
            'recordsTotal': paginator.count,
            'recordsFiltered': paginator.count,
        })
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
            return JsonResponse({'status': 'User and related records deleted successfully'}, status=200)
        except MyUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse(status=400)



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
        url = request.session['url']
        object = AffectationVille.objects.get(idaffectation_ville=pk)
        object.delete()
        return redirect('userslist')
    else:
        return redirect('logout')


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
        return JsonResponse({'error': 'Token already exists for this user'}, status=400)
    else:
        # Create a new token for the user
        Token.objects.create(user=user)
        # Return a JsonResponse indicating successful token creation
        return JsonResponse({'message': 'Token created successfully'}, status=201)


@login_required(login_url='login')
def ajoutSignature(request):
    if request.method == 'POST' and request.FILES.get('image') and request.POST.get('dataRow'):
        image_file = request.FILES['image']
        tr_id = request.POST['dataRow']
        try:
            MyUser.objects.get(id=tr_id)
            return JsonResponse({'error': 'Invalid request'}, status=400)
        except:
            # Save the base64 encoded image data to the database along with the tr_id
            SignaturesModel.objects.create(signatureData=image_file.read(), userId_id=tr_id)
            return JsonResponse({'message': 'Signature uploaded successfully'}, status=200)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required(login_url='login')
def getSignature(request,pk):
    try:
        # Assuming your model has a field named 'image_data' where base64 data is stored
        obj = SignaturesModel.objects.get(idSignature=pk)

        # Fetch the base64 data from the model
        base64_data = base64.b64encode(obj.signatureData).decode('utf-8')  # Encode bytes to base64 string

        # Return the base64 data in a JSON response
        return JsonResponse({'base64_image': base64_data}, status=200)

    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Object not found'}, status=404)

    except Exception as e:
        print('SIGNATURE')
        print(e)
        return JsonResponse({'error': str(e)}, status=500)



@login_required(login_url='login')
def listeSignature(request,pk):
    qs = SignaturesModel.objects.filter(userId=pk).values(
        'idSignature',
        'userId__first_name',
        'userId__last_name'
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
    qs = UserActivityLog.objects.all().order_by('-timestamp').values(
        'id',
        'user__username',
        'timestamp',
        'action',
        'description'
    )

    # Get the search value from the request's GET parameters
    search_value = request.GET.get('search[value]', '')

    # Apply search filter to the QuerySet
    if search_value:
        qs = qs.filter(
            Q(user__username__icontains=search_value) |
            Q(action__icontains=search_value) |
            Q(description__icontains=search_value)
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


@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keeps the user logged in after password change
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})
