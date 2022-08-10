from rest_framework.serializers import ModelSerializer
from enreg.models import *


class CargaisonSerializer(ModelSerializer):
    class Meta:
        model = Cargaison
        fields = '__all__'
