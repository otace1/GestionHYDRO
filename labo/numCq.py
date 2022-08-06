from enreg.models import *
from accounts.models import *
from django.db.models import *
from django.contrib.auth.decorators import login_required
import datetime


def numCq(v, pk):
    # user = request.user
    # id = user.id
    ville = v
    c = Entrepot_echantillon.objects.get(idcargaison=pk)
    c = c.dateechantillonage
    # month = datetime.datetime.month(c)
    # year = datetime.datetime.year(c)
    numcertificatqualite = LaboReception.objects.filter(datereceptionlabo__year=c.year,
                                                        idcargaison__idcargaison__entrepot__ville=ville).aggregate(
        Max('numcertificatqualite'))
    numcertificatqualite = numcertificatqualite.get('numcertificatqualite__max')
    if numcertificatqualite == None:
        numcertificatqualite = 1
        return numcertificatqualite
    else:
        numcertificatqualite = numcertificatqualite + 1
        return numcertificatqualite
