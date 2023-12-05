import json

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage
from django.utils.encoding import force_str
from rest_framework.decorators import api_view, APIView, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions, exceptions
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.authtoken.models import Token
from rest_framework_api_key.models import APIKey
from django.shortcuts import get_object_or_404
from accounts.models import MyUser
from django.db.models import Q
from django_countries.data import COUNTRIES

from labo.codeLabo import codeLabo
from labo.numCq import numCq
from .infiniteScroll import CustomPagination, DateTimeEncoder
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model, authenticate
from django.http import QueryDict, JsonResponse, HttpResponse

from entrepot.numrappech import numRappEch
from entrepot.calculs import *
import uuid
import decimal
import datetime


# This for firebase Login system view Custom JWT
@api_view(['POST'])
@permission_classes([AllowAny])
def loginApiView(request):
    data = request.data
    username = data.get('username')
    password = data.get('password')
    print(username)
    print(password)
    response = Response()
    if (username is None) or (password is None):
        raise exceptions.AuthenticationFailed('The login details are incorrect or required')
    user = MyUser.objects.filter(username=username).first()
    if (user is None):
        raise exceptions.AuthenticationFailed('The login details are incorrect or required')
    if (not user.check_password(password)):
        raise exceptions.AuthenticationFailed('The login details are incorrect or required')

    access_token = user.token
    apiKey = Token.objects.filter(user=user).first()
    print(apiKey)
    apiKey = apiKey.key

    response.set_cookie(key="jwt", value=access_token, httponly=True)
    response.data = {
        'access_token': access_token,
        'apiKey': apiKey,
    }
    return response


class AddCargo(APIView):
    queryset = Cargaison.objects.all()
    serializer_class = CargaisonSerializer

    def post(self, request):
        user = request.user.id

        data = request.data
        voie = Voie.objects.get(nomvoie=data['voie'])
        voie = voie.idvoie
        frontiere = Ville.objects.get(nomville=data['frontiere'])
        frontiere = frontiere.idville
        typeunitetransport = TypeUniteTransport.objects.get(unitetransport=data['typeunitetransport'])
        typeunitetransport = typeunitetransport.idunite
        provenance = data['provenance']
        # Get the key of the provenance value in dict
        a = COUNTRIES
        key = [k for k, v in a.items() if v == provenance]
        provenance = key[0]
        print('VOIE: ',data['voie'])
        print('FRONTIERE: ',data['frontiere'])
        print('UNITE: ',data['typeunitetransport'])
        print('PROVE: ',data['provenance'])
        print('IMPORT: ',data['importateur'])
        print('ENTREPOT: ',data['entrepot'])
        print('PROD: ',data['produit'])


        importateur = Importateur.objects.get(nomimportateur=data['importateur'])
        importateur = importateur.idimportateur
        entrepot = Entrepot.objects.get(nomentrepot=data['entrepot'])
        entrepot = entrepot.identrepot
        immatriculation = data['immatriculation']
        produit = Produit.objects.get(nomproduit=data['produit'])
        produit = produit.idproduit
        volume = decimal.Decimal(data['volume'])
        volume15 = data['volume15']
        volume20 = data['volume20']
        tonnagevide = data['tonnagevide']
        tonnageair = data['tonnageair']
        declaration = data['declaration']
        transitaire = data['transitaire']

        if volume15:
            if volume20:
                if tonnagevide:
                    if tonnageair:
                        volume15 = decimal.Decimal(data['volume15'])
                        volume20 = decimal.Decimal(data['volume20'])
                        tonnagevide = decimal.Decimal(data['tonnagevide'])
                        tonnageair = decimal.Decimal(data['tonnageair'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'volume15': volume15,
                            'volume20': volume20,
                            'tonnagevide': tonnagevide,
                            'tonnageair': tonnageair,
                            'declaration': declaration,
                            'transitaire':transitaire,
                            'user': user,
                        }
                    else:
                        volume15 = decimal.Decimal(data['volume15'])
                        volume20 = decimal.Decimal(data['volume20'])
                        tonnagevide = decimal.Decimal(data['tonnagevide'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'volume15': volume15,
                            'volume20': volume20,
                            'tonnagevide': tonnagevide,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
                else:
                    if tonnageair:
                        volume15 = decimal.Decimal(data['volume15'])
                        volume20 = decimal.Decimal(data['volume20'])
                        tonnageair = decimal.Decimal(data['tonnageair'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'volume15': volume15,
                            'volume20': volume20,
                            'tonnageair': tonnageair,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
                    else:
                        volume15 = decimal.Decimal(data['volume15'])
                        volume20 = decimal.Decimal(data['volume20'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'volume15': volume15,
                            'volume20': volume20,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
            else:
                if tonnagevide:
                    if tonnageair:
                        volume15 = decimal.Decimal(data['volume15'])
                        tonnagevide = decimal.Decimal(data['tonnagevide'])
                        tonnageair = decimal.Decimal(data['tonnageair'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'volume15': volume15,
                            'tonnagevide': tonnagevide,
                            'tonnageair': tonnageair,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
                    else:
                        volume15 = decimal.Decimal(data['volume15'])
                        tonnagevide = decimal.Decimal(data['tonnagevide'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'volume15': volume15,
                            'tonnagevide': tonnagevide,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
                else:
                    if tonnageair:
                        volume15 = decimal.Decimal(data['volume15'])
                        tonnageair = decimal.Decimal(data['tonnageair'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'volume15': volume15,
                            'tonnageair': tonnageair,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
                    else:
                        volume15 = decimal.Decimal(data['volume15'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'volume15': volume15,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
        else:
            if volume20:
                if tonnagevide:
                    if tonnageair:
                        volume20 = decimal.Decimal(data['volume20'])
                        tonnagevide = decimal.Decimal(data['tonnagevide'])
                        tonnageair = decimal.Decimal(data['tonnageair'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'volume20': volume20,
                            'tonnagevide': tonnagevide,
                            'tonnageair': tonnageair,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
                    else:
                        volume20 = decimal.Decimal(data['volume20'])
                        tonnagevide = decimal.Decimal(data['tonnagevide'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'volume20': volume20,
                            'tonnagevide': tonnagevide,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
                else:
                    if tonnageair:
                        volume20 = decimal.Decimal(data['volume20'])
                        tonnageair = decimal.Decimal(data['tonnageair'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'volume20': volume20,
                            'tonnageair': tonnageair,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
                    else:
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
            else:
                if tonnagevide:
                    if tonnageair:
                        tonnagevide = decimal.Decimal(data['tonnagevide'])
                        tonnageair = decimal.Decimal(data['tonnageair'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'tonnagevide': tonnagevide,
                            'tonnageair': tonnageair,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
                    else:
                        tonnagevide = decimal.Decimal(data['tonnagevide'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'tonnagevide': tonnagevide,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
                else:
                    if tonnageair:
                        tonnageair = decimal.Decimal(data['tonnageair'])
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'tonnageair': tonnageair,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }
                    else:
                        data = {
                            'voie': voie,
                            'frontiere': frontiere,
                            'typeunitetransport': typeunitetransport,
                            'provenance': provenance,
                            'importateur': importateur,
                            'entrepot': entrepot,
                            'immatriculation': immatriculation,
                            'produit': produit,
                            'volume': volume,
                            'declaration': declaration,
                            'transitaire': transitaire,
                            'user': user,
                        }

        serializer = CargaisonSerializer(data=data)
        if serializer.is_valid():
            # data = serializer.data
            qrcode = str(uuid.uuid4())
            etat = "En attente requisition"
            serializer.save(qrcode=qrcode, etat=etat)
            context = {'qrcode': qrcode}
            return Response(context, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):

        data = Cargaison.objects.all().order_by('dateheurecargaison')
        serializer = CargaisonSerializer(data, many=True)
        return Response(serializer.data)


class TypeVoie(APIView):
    queryset = Voie.objects.all()
    serializer_class = VoieSerializer

    # permission_classes = [HasAPIKey]

    def get(self, request):
        data = Voie.objects.all()
        serializer = VoieSerializer(data, many=True)
        return Response(serializer.data)


class NomFrontiere(APIView):
    queryset = Ville.objects.all().order_by('nomville')
    serializer_class = FrontiereSerializer

    # permission_classes = [HasAPIKey]

    def get(self, request):
        data = Ville.objects.all().order_by('nomville')
        serializer = FrontiereSerializer(data, many=True)
        return Response(serializer.data)


class TypeUnite(APIView):
    queryset = TypeUniteTransport.objects.all()
    serializer_class = UniteSerializer

    def get(self, request):
        data = TypeUniteTransport.objects.all()
        serializer = UniteSerializer(data, many=True)
        return Response(serializer.data)


class NomFournisseur(APIView):
    queryset = Importateur.objects.all().order_by('nomimportateur')
    serializer_class = FournisseurSerializer

    # permission_classes = [HasAPIKey]

    def get(self, request):
        data = Importateur.objects.all().order_by('nomimportateur')
        serializer = FournisseurSerializer(data, many=True)
        return Response(serializer.data)


class NomEntrepot(APIView):
    queryset = Entrepot.objects.all().order_by('nomentrepot')
    serializer_class = EntrepotSerializer

    # permission_classes = [HasAPIKey]

    def get(self, request):
        data = Entrepot.objects.all().order_by('nomentrepot')
        serializer = EntrepotSerializer(data, many=True)
        return Response(serializer.data)


class TypeProduit(APIView):
    queryset = Produit.objects.all()
    serializer_class = ProduitSerializer

    # permission_classes = [HasAPIKey]

    def get(self, request):
        data = Produit.objects.all()
        print(data)
        serializer = ProduitSerializer(data, many=True)
        return Response(serializer.data)


class GetQrcode(APIView):
    queryset = Cargaison.objects.all()
    serializer_class = CargaisonSerializer

    def get(self, request, pk):
        data = Cargaison.objects.get(idcargaison=pk)
        data = data.qrcode
        context = {'qrcode': data}
        return Response(context, status=status.HTTP_200_OK)


class Provenance(APIView):
    queryset = Cargaison.objects.all()

    # permission_classes = [HasAPIKey]
    # serializer_class = CargaisonSerializer
    def get(self, request):
        data = list(map(force_str, COUNTRIES.values()))  # Convert __proxy__ to regular strings
        json_data = json.dumps(data, ensure_ascii=False)
        response = JsonResponse(json.loads(json_data), safe=False)
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response
        # data = list(map(force_str, COUNTRIES.values()))  # Convert __proxy__ to regular strings
        # json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        # response = JsonResponse(json_data, safe=False)
        # response['Content-Type'] = 'application/json; charset=utf-8'
        # return response
        # data = list(COUNTRIES.values())  # Convert dict_values to a list
        # json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        # response = JsonResponse(json_data, safe=False)
        # response['Content-Type'] = 'application/json; charset=utf-8'
        # return response
        # data = COUNTRIES.values()
        # context = {'provenance': data}
        # return Response(context, status=status.HTTP_200_OK)


class GetCargoList(APIView):
    queryset = Cargaison.objects.all()
    serializer_class = CargaisonSerializer

    # permission_classes = [HasAPIKey]
    def get(self, request):
        data = Cargaison.objects.all()
        serializer = CargaisonSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetCargoCount(APIView):
    queryset = Cargaison.objects.all()
    serializer_class = CargaisonSerializer

    def get(self, request):
        y = datetime.date.today()
        year = y.year
        month = y.month
        annual = Cargaison.objects.filter(dateheurecargaison__year=year).count()
        monthly = Cargaison.objects.filter(dateheurecargaison__month=month).count()
        context = {
            'annual': annual,
            'monthly': monthly
        }
        return Response(context, status=status.HTTP_200_OK)


class UserViewSerializer(viewsets.ModelViewSet):
    # permission_classes = [HasAPIKey]
    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()


class AuthUserApiView(GenericAPIView):
    # permission_classes = [HasAPIKey]
    def get(self, request):
        user = request.user
        serializer = UserSerializer(get_user_model())
        return Response({'user': serializer.data})


@api_view(['POST'])
def verificationQrCode(request):
    context = request.data['qrCode']
    try:
        c=Cargaison.objects.get(qrcode=context)
        try:
            e=Entrepot_echantillon.objects.get(idcargaison=c)
            dateEchantillonnage = e.dateechantillonage
        except:
            dateEchantillonnage = "Pas d'infos"

        try:
            l=LaboReception.objects.get(idcargaison=c)
            dateReceptionLabo = l.datereceptionlabo
        except:
            dateReceptionLabo = "Pas d'infos"

        try:
            i=Inspection.objects.get(idcargaison=c)
            dateInspection = i.dateinspection
        except:
            dateInspection = "Pas d'infos"

        data = {
                    'date':c.dateheurecargaison,
                    'fournisseur':c.importateur.nomimportateur,
                    'entrepot': c.entrepot.nomentrepot,
                    'volume':c.volume,
                    'dateEchantillonnage':dateEchantillonnage,
                    'dateReceptionLabo':dateReceptionLabo,
                    'dateHeureAnalyseLabo':c.dateHeureAnalyseLabo,
                    'dateDechargement':c.dateDechargement,
                    'dateInspection':dateInspection,
                }
    except:
        data = {
                    'date':"Pas d'infos",
                    'fournisseur':"Pas d'infos",
                    'entrepot': "Pas d'infos",
                    'volume':"Pas d'infos",
                    'dateEchantillonnage':"Pas d'infos",
                    'dateReceptionLabo':"Pas d'infos",
                    'dateHeureAnalyseLabo':"Pas d'infos",
                    'dateDechargement':"Pas d'infos",
                    'dateInspection':"Pas d'infos",
                }
        return Response(data, status=status.HTTP_404_NOT_FOUND)
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def showDataSaved(request):
    user = request.user.id
    c = Cargaison.objects.filter(user=user).order_by('-dateheurecargaison')
    list = []
    for data in c:
        context = {
            "dateheurecargaison":data.dateheurecargaison,
            "importateur":data.importateur.nomimportateur,
            "entrepot":data.entrepot.nomentrepot,
            "immatriculation":data.immatriculation,
            "volume":data.volume,
        }
        list.append(context)
    return Response(list, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attenteEchantillonnage(request):
    user = request.user.id
    c = Cargaison.objects.filter(etat="En attente d'echantillonage", entrepot__affectationentrepot__username_id=user).count()
    context = {'count':c}
    return Response(context, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attenteInspection(request):
    user = request.user.id
    c = Cargaison.objects.filter(etatInspection=True, entrepot__affectationentrepot__username_id=user).count()
    context = {'count':c}
    return Response(context, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attenteDechargement(request):
    user = request.user.id
    c = Cargaison.objects.filter(
                Q(etat='En attente de dechargement') | Q(Q(etat='Conforme aux exigences'))).filter(
                entrepot__affectationentrepot__username_id=user).count()
    context = {'count':c}
    return Response(context, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attenteRequisition(request):
    user = request.user.id
    c = Cargaison.objects.filter(etat='En attente requisition',entrepot__affectationentrepot__username_id=user).count()
    context = {'count':c}
    return Response(context, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attenteRequisitionListe(request):
    user = request.user.id
    c = Cargaison.objects.filter(etat="En attente requisition").filter(entrepot__affectationentrepot__username_id=user).order_by('-dateheurecargaison')

    # Apply pagination
    paginator = CustomPagination()
    paginated_cargaisons = paginator.paginate_queryset(c, request)

    serializer = CargaisonSerializer(paginated_cargaisons, many=True)
    return paginator.get_paginated_response(serializer.data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scanEchantillonnage(request):
    user = request.user.id
    qrCode = request.data['qrCode']
    try:
        c=Cargaison.objects.get(qrcode=qrCode,entrepot__affectationentrepot__username_id=user)
        if c.etat == "En attente d'echantillonage":
            context = {'id':c.idcargaison}
            return Response(context,status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scanInspection(request):
    user = request.user.id
    qrCode = request.data['qrCode']
    try:
        c=Cargaison.objects.get(qrcode=qrCode)
        # qs = Cargaison.objects.filter(etatInspection=True, entrepot__affectationentrepot__username_id=user).order_by(
        #     '-dateheurecargaison')
        if c.etatInspection is True:
            context = {'id':c.idcargaison}
            return Response(context,status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scanDechargement(request):
    user = request.user.id
    qrCode = request.data['qrCode']
    try:
        c=Cargaison.objects.get(qrcode=qrCode)
        # qs = Cargaison.objects.filter(Q(etat='Conforme aux exigences') | Q(etat='En attente de dechargement'),
        #                               Q(voie__idvoie=1) | Q(voie__idvoie=2) | Q(voie__idvoie=3), before=False,
        #                               entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
        if c.etat == "En attente de dechargement" or c.etat == 'Conforme aux exigences':
            context = {'id':c.idcargaison}
            return Response(context,status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enregistrementEchantillonnage(request):
    # user = request.user.id
    id = request.data['id']
    matriculeAgent = request.data['matriculeAgent']
    methodeUtilisee = request.data['methodeUtilisee']
    qte = request.data['qte']
    try:
        c=Cargaison.objects.get(idcargaison=id)
        ville = c.entrepot.ville
        numrappech = numRappEch(id,ville)
        numrappechauto = numrappech
        c.rapechctrl = 1
        c.etatInspection = True
        c.etat = "Echantillonner"
        c.save(update_fields=['etat', 'rapechctrl', 'etatInspection'])
        e = Entrepot_echantillon(idcargaison=c, numrappechauto=numrappechauto, matricule=matriculeAgent,
                                 methodeutilisee=methodeUtilisee, qte=qte)
        e.save()
        context = {
            'qrCode':c.qrcode,
            'numDossier':c.numdos,
            'numRappEch': numrappech,
            'nomClient':c.importateur.nomimportateur,
            'entrepot': c.entrepot.nomentrepot,
            'qteLabo': qte,
            'natureMarchandise':'PRODUIT PETROLIER',
            'marqueProduit': c.produit.nomproduit,
            'qteMarchandise': c.volume,
            'origine':c.provenance.name,
            'immatriculation':c.immatriculation,
            'methodeEchantillonnage':methodeUtilisee,
            'matriculeAgent':matriculeAgent,
        }
        return Response(context,status=status.HTTP_200_OK)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cargaisonEchantillonnageList(request):
    user = request.user.id
    data = Cargaison.objects.filter(etat="En attente d'echantillonage",
                                    entrepot__affectationentrepot__username_id=user).order_by('-dateheurecargaison')

    # Configure pagination
    page_size = int(request.GET.get('pagination', 5))  # You can adjust this value according to your preference
    requested_page = int(request.GET.get('page', 1))
    # Handle the case where requested_page is 0
    if requested_page <= 0:
        requested_page = 1

    paginator = Paginator(data, page_size)
    paginated_data = paginator.get_page(requested_page)

    result_list = []

    for values in paginated_data:
        context = {
            "id": values.idcargaison,
            "numdos": values.numdos,
            "requisition": values.numreq,
            "dateheurecargaison": values.dateheurecargaison.date(),
            "importateur": values.importateur.nomimportateur,
            "immatriculation": values.immatriculation,
            "produit": values.produit.nomproduit,
            "volume": values.volume,
        }
        result_list.append(context)

    response_data = {
        "last_response": result_list,
    }

    return Response(response_data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cargaisonListeDechargement(request):
    user = request.user.id
    data = Cargaison.objects.filter(etat='Conforme aux exigences',before=False,
                                              entrepot__affectationentrepot__username_id=user).order_by('-dateheurecargaison')


    # Configure pagination
    page_size = int(request.GET.get('pagination', 5))  # You can adjust this value according to your preference
    requested_page = int(request.GET.get('page', 1))
    # Handle the case where requested_page is 0
    if requested_page <= 0:
        requested_page = 1

    start_index = (requested_page - 1) * page_size
    end_index = requested_page * page_size

    paginated_data = data[start_index:end_index]
    result_list = []

    for values in paginated_data:
        context = {
            "id": values.idcargaison,
            "numdos": values.numdos,
            "requisition": values.numreq,
            "dateheurecargaison": values.dateheurecargaison.date(),
            "importateur": values.importateur.nomimportateur,
            "immatriculation": values.immatriculation,
            "produit": values.produit.nomproduit,
            "volume": values.volume,
        }
        result_list.append(context)

    response_data = {
        "last_response": result_list,
    }

    return Response(response_data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cargaisonInspectionList(request):
    user = request.user.id
    data = Cargaison.objects.filter(etatInspection=True, entrepot__affectationentrepot__username_id=user).order_by('-dateheurecargaison')

    # Configure pagination
    page_size = int(request.GET.get('pagination', 5))  # You can adjust this value according to your preference
    requested_page = int(request.GET.get('page', 1))
    # Handle the case where requested_page is 0
    if requested_page <= 0:
        requested_page = 1

    start_index = (requested_page - 1) * page_size
    end_index = requested_page * page_size

    paginated_data = data[start_index:end_index]
    result_list = []

    for values in paginated_data:
        context = {
            "id": values.idcargaison,
            "numdos": values.numdos,
            "requisition": values.numreq,
            "dateheurecargaison": values.dateheurecargaison.date(),
            "importateur": values.importateur.nomimportateur,
            "immatriculation": values.immatriculation,
            "produit": values.produit.nomproduit,
            "volume": values.volume,
        }
        result_list.append(context)

    response_data = {
        "last_response": result_list,
    }

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cargaisonRequisitionList(request):
    user = request.user.id
    data = Cargaison.objects.filter(
        etat="En attente requisition",
        entrepot__affectationentrepot__username_id=user
    ).order_by('-dateheurecargaison')

    # Configure pagination
    page_size = int(request.GET.get('pagination', 5))  # You can adjust this value according to your preference
    requested_page = int(request.GET.get('page', 1))
    # Handle the case where requested_page is 0
    if requested_page <= 0:
        requested_page = 1

    start_index = (requested_page - 1) * page_size
    end_index = requested_page * page_size

    paginated_data = data[start_index:end_index]
    result_list = []

    for values in paginated_data:
        context = {
            "id": values.idcargaison,
            "dateheurecargaison": values.dateheurecargaison.date(),
            "importateur": values.importateur.nomimportateur,
            "immatriculation": values.immatriculation,
            "produit": values.produit.nomproduit,
            "volume": values.volume,
        }
        result_list.append(context)

    response_data = {
        "last_response": result_list,
    }

    return Response(response_data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sealsInspection(request):
    id = request.data['id']
    manifoldnumber = request.data['manifoldnumber']
    sealstate = request.data['sealstate']
    cargaison = Cargaison.objects.get(idcargaison=id)
    sealState = SealState.objects.get(sealstate=sealstate)
    a = InspectionSeal(manifoldnumber=manifoldnumber,sealstate=sealState,idcargaison=cargaison)
    a.save()
    context = {
        'id':id
    }
    return Response(context,status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tankerInspection(request):
    id = request.data['id']
    cargaison = Cargaison.objects.get(idcargaison=id)
    densite = request.data['densite']
    temperature = request.data['temperature']
    try:
        innageIn = request.data['innageIn']
    except:
        innageIn = 'N/A'
    volumeIn = request.data['volumeIn']
    tempIn = request.data['volumeIn']
    weightIn = request.data['volumeIn']

    try:
        i = Inspection(idcargaison=cargaison,dens=densite,temp=temperature,innagein=innageIn, volumein=volumeIn, tempin=tempIn,weightin=weightIn)
        i.save()
    except:
        data = Inspection.objects.get(idcargaison=cargaison)
        data.dens = densite
        data.temp = temperature
        data.innagein = innageIn
        data.volumein = volumeIn
        data.tempin = tempIn
        data.weightin = weightIn
        data.save(update_fields=['dens', 'temp', 'innagein', 'volumein', 'tempin', 'weightin'])

    context = {
        'id':id
    }
    return Response(context,status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def compartimentInspection(request):
    id = request.data['id']
    inspection = Inspection.objects.get(idcargaison=id)
    tempComp = request.data['tempComp']
    compartDenom = request.data['compartDenom']
    sealNumber = request.data['sealNumber']
    sealState = request.data['sealState']
    sealState = SealState.objects.get(sealstate=sealState)
    innage = request.data['innage']

    # Check if 'meterafter' is a valid number or convert it to 0 if it's None or empty.
    if innage is None or not str(innage).isnumeric():
        innage = 0

    gov = request.data['gov']

    #Calcul dens a 15
    densite = inspection.dens
    temperature = inspection.temp
    d = densite15(temperature,densite) #Den a 15
    v = vcf(d,tempComp) #VFC
    g = gsv(v, gov) #GSV
    m = mtv(g,d) #MTV
    a = mta(g,d) #MTA

    compartimentData = Compartiment(idinspection=inspection,tempcomp=tempComp,compart=compartDenom,sealNumber=sealNumber,innage=innage,sealstate=sealState,
                                    gsv=g,vcf=v,mtv=m,mta=a,gov=gov)
    compartimentData.save()
    context = {
        'id':id
    }
    return Response(context,status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marquageInspection(request):
    id = request.data['id']
    c = Cargaison.objects.get(idcargaison=id)
    c.etatInspection = 0
    c.save(update_fields=['etatInspection'])
    context = {
        'id': id
    }
    return Response(context, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rapportInspection(request):
    id = request.data['id']

    cargaison = Cargaison.objects.get(idcargaison=id)
    inspection = Inspection.objects.get(idcargaison=id)
    if inspection.meterbefore is None:
        inspection.meterbefore = 0
    if inspection.meterafter is None:
        inspection.meterafter = 0
    seal = InspectionSeal.objects.filter(idcargaison=id)
    if Resultat.objects.filter(idcargaison_id=id).exists():
        resultat_data = Resultat.objects.get(idcargaison_id=id)

    compartiment = Compartiment.objects.filter(
        idinspection=inspection.idinspection)  # Filter Database for all the save compartiment
    govTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('gov', flat=True)), 3))  # gov Total Tanker
    gsvTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('gsv', flat=True)), 3))  # gsv Total Tanker
    mtaTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('mta', flat=True)), 3))  # mta Total Tanker
    mtvTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('mtv', flat=True)), 3))  # mtv Total Tanker
    vcfTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('vcf', flat=True)), 3))  # vcf Total Tanker
    print('OK OK')
    print('VCF PRINT')
    print(vcfTotal)

    densite = densite15(inspection.temp, inspection.dens)  # densite 15c
    govMeter = round((inspection.meterafter - inspection.meterbefore) / 1000, 3)  # govmeter
    vcfMeter = vcf(densite, inspection.temp)  # vcfMeter
    gsvMeter = gsv(vcfMeter, govMeter)  # gsvMeter
    mtaMeter = mta(gsvMeter, densite)  # mta Meter

    govLt = float(cargaison.volume)  # gov LT
    vcfLt = vcf(densite, inspection.temp)  # VCF LT
    gsvLt = (cargaison.volume15)  # GSV LT
    if gsvLt is None:
        gsvLt = 0
    # gsvLt = gsv(vcfLt, govLt)  # GSV LT
    mtvLt = (cargaison.tonnagevide)  # MTV LT
    if mtvLt is None:
        mtvLt = 0
    # mtvLt = mtv(gsvLt, densite)  # MTV LT
    mtaLt = (cargaison.tonnageair)  # MTA LT
    if mtaLt is None:
        mtaLt = 0
    # mtaLt = mta(gsvLt, densite)  # MTA LT

    govLtTanker = round((govLt - float(govTotal)), 3)  # Difference LT/Tanker
    gsvLtTanker = round((float(gsvLt) - float(gsvTotal)), 3)  # Difference GSV LT/Tanker
    mtvLtTanker = round((float(mtvLt) - float(mtvTotal)), 3)  # Difference mtv LT/Tanker
    mtaLtTanker = round((float(mtaLt) - float(mtaTotal)), 3)  # Difference mtv LT/Tanker
    prLtTanker = round((govLtTanker * 100) / govLt, 3)
    if gsvLt == 0:
        gsvLt = 1
    prGsvLtTanker = round((gsvLtTanker * 100) / float(gsvLt), 3)
    if mtaLt == 0:
        mtaLt = 1
    prMtaLtTanker = round((mtaLtTanker / (float(mtaLt)) * 100), 3)
    if mtvLt == 0:
        mtvLt = 1
    prMtvLtTanker = round((mtvLtTanker / (float(mtvLt)) * 100), 3)

    govTankerMeter = float(govTotal) - float(govMeter)  # Difference Tanker/Meter
    gsvTankerMeter = float(gsvTotal) - float(gsvMeter)  # Difference GSV Tanker/Meter
    mtaTankerMeter = round((float(mtaTotal) - mtaMeter), 3)  # Difference MTA Tanker/Meter
    prTankerMeter = round((govTankerMeter * 100) / float(govTotal), 3)

    govLtMeter = govLt - govMeter  # Diff LT/Meter
    gsvLtMeter = round((float(gsvLt) - gsvMeter), 3)  # Diff GSV LT/Meter
    mtaLtMeter = float(mtaLt) - mtaMeter  # Diff mta LT/Meter
    if govLt == 0:
        govLt = 1
    prLtMeter = round((govLtMeter * 100) / govLt, 3)
    if gsvLt == 0:
        gsvLt = 1
    prGsvLtMeter = round((gsvLtMeter * 100) / float(gsvLt), 3)
    if mtaLt == 0:
        mtaLt = 1
    prMtaLtMeter = round((mtaLtMeter * 100) / float(mtaLt), 3)

    # Certified Quantity
    if govMeter > 0:
        govMax = govMeter
        gsvMax = gsvMeter
        mtaMax = mtaMeter
    else:
        if float(govTotal) > 0:
            govMax = govTotal
            gsvMax = gsvTotal
            mtaMax = mtaTotal
        else:
            if govLt > 0:
                govMax = govLt
                gsvMax = gsvLt
                mtaMax = mtaLt

    # govMax = round((max(govTotal, govMeter, govLt)),3)  # Max value of GOV
    # gsvMax = round((max(gsvTotal, gsvMeter, gsvLt)),3)  # Max value of GSV
    # mtaMax = round((max(mtaTotal, mtaMeter, mtaLt)),3)  # Max value of MTA

    fraisOcc = round((11 * float(gsvMax)), 3)  # Frais occ a Payer


    context = {
        'qrCode':cargaison.qrcode,
        'immatriculation':cargaison.immatriculation,
        'entrance':cargaison.frontiere.nomville,
        'dateArrivee':cargaison.dateheurecargaison.date(),
        'origin':cargaison.provenance.name,
        'produit':cargaison.produit.nomproduit,
        'dateInspection':inspection.dateinspection.date(),
        'fournisseur':cargaison.importateur.nomimportateur,
        'entrepot':cargaison.entrepot.nomentrepot,
        #Jaugeage
        'govTotal':govTotal,
        'densite':densite,
        'gsvTotal':gsvTotal,
        'mtaTotal':mtaTotal,
        'mtvTotal':mtvTotal,
        'vcfTotal':vcfTotal,
        #LT
        'govLt':govLt,
        'gsvLt':gsvLt,
        'mtvLt':mtvLt,
        'mtaLt':mtaLt,
        #Meter
        'govMeter':govMeter,
        'gsvMeter':gsvMeter,
        #certified Qty
        'govMax':govMax,
        'gsvMax':gsvMax,
        'mtaMax':mtaMax,
        #Frais
        'fraisOcc':fraisOcc,
    }
    return Response(context, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dechargementCargaison(request):
    id = request.data['id']
    meterafter = request.POST['meterafter']
    meterbefore = request.POST['meterbefore']

    # Check if 'meterafter' is a valid number or convert it to 0 if it's None or empty.
    if meterafter is None or not str(meterafter).isnumeric():
        meterafter = 0

    if meterbefore is None or not str(meterbefore).isnumeric():
        meterbefore = 0

    try:
        cargaison = Cargaison.objects.get(idcargaison=id)
        inspection = Inspection.objects.get(idcargaison_id=cargaison)

        inspection.meterafter = meterafter
        inspection.save(update_fields=['meterafter', 'meterbefore'])
        cargaison.etat = 'Cargaison dechargee'
        cargaison.dateDechargement = datetime.datetime.today()
        cargaison.save(update_fields=['etat', 'dateDechargement'])

        context = {
            'id':id
        }
        return Response(context, status=status.HTTP_200_OK)
    except ObjectDoesNotExist:
        context = {
            'id':id
        }
        return Response(context,status=status.HTTP_400_BAD_REQUEST)

#
# ReceptionLabo

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def receptionEchantillonLabo(request):
    try:
        qrCode = request.data.get('qrCode')  # Use get() to safely retrieve the value
        if not qrCode:
            return Response({'error': 'qrCode is missing in the request data'}, status=status.HTTP_400_BAD_REQUEST)

        cargaison = get_object_or_404(Cargaison, qrcode=qrCode, etat='Echantillonner')
        cargaisonEntrepot = get_object_or_404(Entrepot_echantillon, idcargaison=cargaison)

        ville = get_object_or_404(Entrepot, identrepot=cargaison.entrepot_id).ville_id

        # Generate the automatic CQ number
        numcertificatqualite = numCq(ville)

        # Change the state of the cargaison
        cargaison.etat = "Analyse Labo en cours"
        cargaison.save(update_fields=['etat'])

        # Save the instruction in the LaboReception table
        codelabo = codeLabo(ville)
        LaboReception.objects.create(
            idcargaison=cargaisonEntrepot, codelabo=codelabo, numcertificatqualite=numcertificatqualite, datereceptionlabo=datetime.datetime.now()
        )
        context = {'codeLabo': codelabo}
        return Response(context, status=status.HTTP_200_OK)
    except Cargaison.DoesNotExist:
        return Response({'error': 'Cargaison not found for the given qrCode'}, status=status.HTTP_404_NOT_FOUND)
    except Entrepot.DoesNotExist:
        return Response({'error': 'Entrepot not found for the given qrCode'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

