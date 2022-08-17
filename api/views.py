import django_countries.data
from django.shortcuts import render
from rest_framework.decorators import api_view, APIView
from rest_framework.response import Response
from rest_framework import status
from enreg.models import Voie, Ville, TypeUniteTransport, Importateur, Entrepot, Produit
from django_countries.fields import CountryField
from django_countries.data import COUNTRIES
from .serializers import *
import uuid


class AddCargo(APIView):
    queryset = Cargaison.objects.all()
    serializer_class = CargaisonSerializer

    def post(self, request):
        serializer = CargaisonSerializer(data=request.data)
        if serializer.is_valid():

            qrcode = str(uuid.uuid4())
            etat = "En attente requisition"
            instance = serializer.save(qrcode=qrcode, etat=etat)
            instance.save()
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

    def get(self, request):
        data = Voie.objects.all()
        serializer = VoieSerializer(data, many=True)
        return Response(serializer.data)


class NomFrontiere(APIView):
    queryset = Ville.objects.all()
    serializer_class = FrontiereSerializer

    def get(self, request):
        data = Ville.objects.all()
        serializer = FrontiereSerializer(data, many=True)
        return Response(serializer.data)


class TypeUnite(APIView):
    queryset = TypeUniteTransport.objects.all()
    serializer_class = UniteSerializer

    def post(self, request):
        serializer = UniteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        data = TypeUniteTransport.objects.all()
        serializer = UniteSerializer(data, many=True)
        return Response(serializer.data)


class NomFournisseur(APIView):
    queryset = Importateur.objects.all()
    serializer_class = FournisseurSerializer

    def get(self, request):
        data = Importateur.objects.all()
        serializer = FournisseurSerializer(data, many=True)
        return Response(serializer.data)


class NomEntrepot(APIView):
    queryset = Entrepot.objects.all()
    serializer_class = EntrepotSerializer

    def get(self, request):
        data = Entrepot.objects.all()
        serializer = EntrepotSerializer(data, many=True)
        return Response(serializer.data)


class TypeProduit(APIView):
    queryset = Produit.objects.all()
    serializer_class = ProduitSerializer

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
    def get(self, request):
        data = COUNTRIES.values()
        context = {'provenance': data}
        return Response(context, status=status.HTTP_200_OK)


class GetCargoList(APIView):
    def get(self, request):
        data = Cargaison.objects.all()
        serializer = CargaisonSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetCargoCount(APIView):
    def get(self, request):
        data = Cargaison.objects.all().count()
        context = {'count': data}
        return Response(context, status=status.HTTP_200_OK)
