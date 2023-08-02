from enreg.models import *
from accounts.models import *
import datetime
from django.db.models import *


# Numero de Dossier Annuel et unique
def numDossier(pk, ville):
    print(pk)
    print(ville)
    d = Cargaison.objects.get(idcargaison=pk)
    date_value = d.dateheurecargaison.date()  # Extract the date value without time
    year_value = date_value.year

    c = Cargaison.objects.filter(dateheurecargaison__year=year_value, entrepot__ville__idville=ville).aggregate(Max('numdos'))
    print(c.get('numdos__max'))

    if c.get('numdos__max') is None:
        numdos = 1
    else:
        numdos = int(c.get('numdos__max')) + 1
        print(numdos)

    return numdos

    #
    # d = Cargaison.objects.get(idcargaison=pk)
    # d = d.dateheurecargaison
    # d = datetime.datetime.date(d)
    # d = d.year
    # c = Cargaison.objects.filter(dateheurecargaison__year=d, entrepot__ville=ville).aggregate(Max('numdos'))
    #
    # if c.get('numdos__max') == None:
    #     numdos = 1
    # else:
    #     numdos = c.get('numdos__max')
    #     numdos = numdos + 1
    # return numdos
