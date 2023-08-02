from enreg.models import *
from accounts.models import *
from django.db.models import *
from django.contrib.auth.decorators import login_required
from datetime import datetime


def codeLabo(v, pk):
    ville = v
    # Get the current date
    current_date = datetime.now()
    code = LaboReception.objects.filter(
        datereceptionlabo__month=current_date.month,
        datereceptionlabo__year=current_date.year,
        idcargaison__idcargaison__entrepot__ville=ville
    ).aggregate(Max('codelabo'))

    codelabo = code.get('codelabo__max')
    if codelabo is None:
        codelabo = 1
    else:
        codelabo = int(codelabo) + 1

    return codelabo
