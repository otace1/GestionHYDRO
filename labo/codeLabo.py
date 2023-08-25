from enreg.models import *
from accounts.models import *
from django.db.models import *
from django.contrib.auth.decorators import login_required
from datetime import datetime


def codeLabo(v):
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


def generate_labo_code(ville):
    current_date = datetime.now()
    last_month = (current_date.month - 1) % 12 or 12
    last_year = current_date.year - 1 if current_date.month == 1 else current_date.year

    last_code = LaboReception.objects.filter(
        datereceptionlabo__year__in=[current_date.year, last_year],
        datereceptionlabo__month__in=[current_date.month, last_month],
        idcargaison__idcargaison__entrepot__ville=ville
    ).aggregate(Max('codelabo'))['codelabo__max']

    return last_code + 1 if last_code is not None else 1



def verification(num,ville):
    current_date = datetime.now()
    last_month = (current_date.month - 1) % 12 or 12
    last_year = current_date.year - 1 if current_date.month == 1 else current_date.year

    last_code = LaboReception.objects.filter(
        datereceptionlabo__year__in=[current_date.year, last_year],
        datereceptionlabo__month__in=[current_date.month, last_month],
        idcargaison__idcargaison__entrepot__ville=ville
    ).aggregate(Max('codelabo'))['codelabo__max']

    if last_code is None:
        if num != 1:
            num = 1
    else:
        if num != last_code + 1:
            num = last_code + 1
    return num