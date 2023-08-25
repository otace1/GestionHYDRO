from django.db import transaction

from enreg.models import *
from accounts.models import *
from datetime import datetime
from django.db.models import *


# Numero de Dossier Annuel et unique
def numDossier(pk, ville):
    # Fetch the Cargaison object using the primary key
    cargaison = Cargaison.objects.get(idcargaison=pk)

    # Extract the year from the cargo's date and time
    year_value = cargaison.dateheurecargaison.year

    max_numdos_query = Cargaison.objects.filter(dateheurecargaison__year=year_value,
                                                entrepot__ville__idville=ville).order_by('-numdos').first()

    if max_numdos_query:
        max_numdos = max_numdos_query.numdos
    else:
        max_numdos = 0

    return max_numdos


# def verificationNumDossier(pk,num,ville):
#     # Fetch the Cargaison object using the primary key
#     cargaison = Cargaison.objects.get(idcargaison=pk)
#
#     # Extract the year from the cargo's date and time
#     year_value = cargaison.dateheurecargaison.year
#
#     # Query the database for the maximum numdos value for the given year and ville
#     max_numdos = Cargaison.objects.filter(dateheurecargaison__year=year_value, entrepot__ville__idville=ville).aggregate(
#         Max('numdos'))['numdos__max']
#
#     if max_numdos is None:
#         if num != 1:
#             num = 1
#     else:
#         if num != max_numdos + 1:
#             num = max_numdos + 1
#
#     return num




