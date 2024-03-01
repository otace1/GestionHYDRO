from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer

from enreg.models import *


class CargaisonSerializer(ModelSerializer):
    provenance = CountryField()
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


class UserSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = '__all__'

#
# class ProvenanceSerializer(serializers.Serializer):
#     provenance = CountryField(name_only=True)
