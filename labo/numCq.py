from django.db import transaction

from enreg.models import *
from accounts.models import *
from django.db.models import *
from django.contrib.auth.decorators import login_required
from datetime import datetime


def numCq(v):
    current_date = datetime.now()
    current_year = current_date.year

    query = f'''
                SELECT l.idcargaison_id, c.idcargaison, MAX(l.numcertificatqualite) as last_code
                FROM enreg_laboreception l
                JOIN enreg_cargaison c ON l.idcargaison_id = c.idcargaison
                JOIN enreg_entrepot e ON c.entrepot_id = e.identrepot
                JOIN enreg_ville v ON e.ville_id = v.idville
                WHERE YEAR(l.datereceptionlabo) = {current_year}
                AND v.idville = {v}
            '''

    last_code_result = Cargaison.objects.raw(query)
    last_code = None

    for result in last_code_result:
        last_code = result.last_code

    # print('LAST CODE:')
    # print(last_code)

    return last_code



    # with transaction.atomic():
    #     # Fetch the current maximum numcertificatqualite value while acquiring a lock
    #     max_cert_query = LaboReception.objects.filter(
    #         datereceptionlabo__year=year_value,
    #         idcargaison__idcargaison__entrepot__ville=v
    #     ).order_by('-numcertificatqualite').first()
    #
    #     if max_cert_query:
    #         numcertificatqualite = max_cert_query.numcertificatqualite
    #     else:
    #         numcertificatqualite = 0
    # return numcertificatqualite


# def verificationCQ(num,ville,pk):
#     c = Entrepot_echantillon.objects.get(idcargaison=pk)
#     year_value = c.dateechantillonage.year
#
#     last_code = LaboReception.objects.filter(
#         datereceptionlabo__year=year_value,
#         idcargaison__idcargaison__entrepot__ville=ville
#     ).aggregate(Max('numcertificatqualite'))['numcertificatqualite__max']
#
#     if last_code is None:
#         if num != 1:
#             num = 1
#     else:
#         if num != last_code + 1:
#             num = last_code + 1
#     return num