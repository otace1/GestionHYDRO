import datetime

from django.db.models import *

from enreg.models import *


# Numero de Dossier Annuel et unique
def numRappEch(pk, ville):
    d = Cargaison.objects.get(idcargaison=pk)
    d = d.dateheurecargaison
    d = datetime.datetime.date(d)
    d = d.year
    # c = Cargaison.objects.filter(dateheurecargaison__year=d, entrepot__ville=ville).aggregate(Max('numdos'))
    c = Entrepot_echantillon.objects.filter(idcargaison__dateheurecargaison__year=d,
                                            idcargaison__entrepot__ville=ville).aggregate(Max('numrappechauto'))

    if c.get('numrappechauto__max') == None:
        numrappechauto = 1
    else:
        numrappechauto = c.get('numrappechauto__max')
        numrappechauto = numrappechauto + 1
    return numrappechauto
