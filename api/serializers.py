from django.contrib.auth import get_user_model
from rest_framework import serializers
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


# class VoieSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Voie
#         fields = ['idvoie', 'nomvoie']

class VilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ville
        fields = ['idville', 'nomville', 'province']

class TypeUniteTransportSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeUniteTransport
        fields = ['idunite', 'unitetransport']

class ImportateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Importateur
        fields = ['idimportateur', 'nomimportateur', 'adresseimportateur', 'nifimportateur', 'email']

# class EntrepotSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Entrepot
#         fields = ['identrepot', 'nomentrepot', 'adresseentrepot', 'ville']
#
# class ProduitSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Produit
#         fields = ['idproduit', 'nomproduit']
#
# class CargaisonSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Cargaison
#         fields = [
#             'idcargaison', 'voie', 'importateur', 'produit', 'frontiere', 'provenance',
#             'entrepot', 'volume', 'immatriculation', 'dateheurecargaison', 'qrcode',
#             'etat', 'numdossier', 'codecargaison', 'numact', 'numCertInspection',
#             'conformite', 'impression', 'user', 'tampon', 'requisitionack',
#             'requisitiondackdate', 'numdos', 'numreq', 'rapechctrl', 'typeunitetransport',
#             'volume15', 'volume20', 'tonnagevide', 'tonnageair', 'before', 'after',
#             'declaration', 'transitaire', 'etatInspection', 'dateHeureAnalyseLabo',
#             'dateDechargement', 'toBeRefouler', 'toBeConsignated', 'isConsignated',
#             'isRefouler', 'controlLiquidation', 'partialLiquidattion', 'files_path'
#         ]
#         read_only_fields = ['idcargaison', 'dateheurecargaison', 'qrcode']
#

