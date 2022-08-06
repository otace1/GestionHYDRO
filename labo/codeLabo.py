from enreg.models import *
from accounts.models import *
from django.db.models import *
from django.contrib.auth.decorators import login_required
import datetime


def codeLabo(v, pk):
    # user = request.user
    # id = user.id
    ville = v
    c = Entrepot_echantillon.objects.get(idcargaison=pk)
    c = c.dateechantillonage
    # month = datetime.datetime.month(c)
    # year = datetime.datetime.year(c)
    code = LaboReception.objects.filter(datereceptionlabo__month=c.month, datereceptionlabo__year=c.year,
                                        idcargaison__idcargaison__entrepot__ville=ville).aggregate(Max('codelabo'))
    codelabo = code.get('codelabo__max')
    if codelabo == None:
        codelabo = 1
        return codelabo
    else:
        codelabo = code.get('codelabo__max')
        codelabo = int(codelabo)
        codelabo = codelabo + 1
        return codelabo
