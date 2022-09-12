from rest_framework.decorators import api_view, APIView, permission_classes
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions, exceptions
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.authtoken.models import Token
from rest_framework_api_key.models import APIKey
from accounts.models import MyUser
from django_countries.data import COUNTRIES
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model, authenticate
import uuid
import decimal
import datetime


# This for firebase Login system view Custom JWT
@api_view(['POST'])
@permission_classes([AllowAny])
def loginApiView(request):
    data = request.data
    username = data['username']
    password = data['password']
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
        print(provenance)
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
                            'tonnageair': tonnageair
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
                            'tonnageair': tonnageair
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
                            'tonnageair': tonnageair
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
                            'tonnageair': tonnageair
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
                            'tonnageair': tonnageair
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
                            'tonnageair': tonnageair
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
                            'tonnageair': tonnageair
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
                            'tonnageair': tonnageair
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

        data = Cargaison.objects.all()
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

    # permission_classes = [HasAPIKey]

    # def post(self, request):
    #     serializer = UniteSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     else:
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        data = COUNTRIES.values()
        context = {'provenance': data}
        return Response(context, status=status.HTTP_200_OK)


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

    # permission_classes = [HasAPIKey]

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
