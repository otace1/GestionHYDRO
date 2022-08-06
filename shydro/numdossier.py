from enreg.models import *
from accounts.models import *
import datetime
from django.db.models import *


# Numero de Dossier Annuel et unique
def numDossier(pk, ville):
    d = Cargaison.objects.get(idcargaison=pk)
    d = Cargaison.objects.get(idcargaison=pk)
    d = d.dateheurecargaison
    d = datetime.datetime.date(d)
    d = d.year
    c = Cargaison.objects.filter(dateheurecargaison__year=d, entrepot__ville=ville).aggregate(Max('numdos'))

    if c.get('numdos__max') == None:
        numdos = 1
    else:
        numdos = c.get('numdos__max')
        numdos = numdos + 1
    return numdos
