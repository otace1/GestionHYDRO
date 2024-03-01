from datetime import datetime

from django.db.models import *

from accounts.models import *
from enreg.models import *


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


def generate_labo_code(ville_id):
    current_date = datetime.now()
    current_month = current_date.month

    query = f'''
            SELECT l.idcargaison_id, c.idcargaison, MAX(l.codelabo) as last_code
            FROM enreg_laboreception l
            JOIN enreg_cargaison c ON l.idcargaison_id = c.idcargaison
            JOIN enreg_entrepot e ON c.entrepot_id = e.identrepot
            JOIN enreg_ville v ON e.ville_id = v.idville
            WHERE MONTH(l.datereceptionlabo) = {current_month}
            AND v.idville = {ville_id}
            GROUP BY l.idcargaison_id, c.idcargaison
        '''

    last_code_result = Cargaison.objects.raw(query)
    last_code = None

    for result in last_code_result:
        last_code = result.last_code

    print('LAST CODE:')
    print(last_code)

    return last_code




# def verification(num,ville):
#     current_date = datetime.now()
#     last_month = (current_date.month - 1) % 12 or 12
#     last_year = current_date.year - 1 if current_date.month == 1 else current_date.year
#
#     last_code = LaboReception.objects.filter(
#         datereceptionlabo__year__in=[current_date.year, last_year],
#         datereceptionlabo__month__in=[current_date.month, last_month],
#         idcargaison__idcargaison__entrepot__ville=ville
#     ).aggregate(Max('codelabo'))['codelabo__max']
#
#     if last_code is None:
#         if num != 1:
#             num = 1
#     else:
#         if num != last_code + 1:
#             num = last_code + 1
#     return num