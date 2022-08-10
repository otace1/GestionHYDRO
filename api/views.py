from django.shortcuts import render
from rest_framework.decorators import api_view, APIView
from rest_framework.response import Response
from rest_framework import status
from enreg.models import *
from .serializers import *

import uuid


class AddCargo(APIView):
    queryset = Cargaison.objects.all()
    serializer_class = CargaisonSerializer

    def post(self, request):
        serializer = CargaisonSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save(commit=False)
            qrcode = str(uuid.uuid4())
            instance.etat = "En attente requisition"
            instance.qrcode = qrcode
            context = {'qrcode': qrcode}
            instance.save()
            return Response(context, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        data = Cargaison.objects.all()
        serializer = CargaisonSerializer(data, many=True)
        return Response(serializer.data)
