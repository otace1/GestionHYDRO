from rest_framework.serializers import ModelSerializer
from django_countries.serializer_fields import CountryField
from rest_framework import serializers
from enreg.models import *


class CargaisonSerializer(ModelSerializer):
    class Meta:
        model = Cargaison
        fields = '__all__'


class VoieSerializer(ModelSerializer):
    class Meta:
        model = Voie
        fields = '__all__'


class UniteSerializer(ModelSerializer):
    class Meta:
        model = TypeUniteTransport
        fields = '__all__'


class FrontiereSerializer(ModelSerializer):
    class Meta:
        model = Ville
        fields = '__all__'


class FournisseurSerializer(ModelSerializer):
    class Meta:
        model = Importateur
        fields = '__all__'


class EntrepotSerializer(ModelSerializer):
    class Meta:
        model = Entrepot
        fields = '__all__'


class ProduitSerializer(ModelSerializer):
    class Meta:
        model = Produit
        fields = '__all__'

#
# class ProvenanceSerializer(serializers.Serializer):
#     provenance = CountryField(name_only=True)
