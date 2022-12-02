from rest_framework.decorators import api_view, APIView, permission_classes
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions, exceptions
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.authtoken.models import Token
from rest_framework_api_key.models import APIKey
from accounts.models import MyUser
from django.db.models import Q
from django_countries.data import COUNTRIES
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model, authenticate

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
                            'tonnageair': tonnageair,
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
    c = Cargaison.objects.filter(user=user)
    list = []
    for data in c:
        context = {
            "dateheurecargaison":data.dateheurecargaison,
            "importateur":data.importateur.nomimportateur,
            "entrepot":data.entrepot.nomentrepot,
            "immatriculation":data.immatriculation,
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
def attenteRequisitionListe(request):
    user = request.user.id
    c = Cargaison.objects.filter(etat="En attente requisition").filter(entrepot__affectationentrepot__username_id=user).order_by('-dateheurecargaison')
    serializer = CargaisonSerializer(c, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
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


@api_view(['GET'])
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
            'numDossier':c.numdos,
            'numRappEch': numrappech,
            'nomClient':c.importateur.nomimportateur,
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




