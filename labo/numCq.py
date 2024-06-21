from datetime import datetime as dt
from accounts.models import *
from enreg.models import *
from django.db.models import Max, F

# def numCq(v):
#     current_date = dt.now()
#     current_year = current_date.year
#
#     query = f'''
#                 SELECT l.idcargaison_id, c.idcargaison, MAX(l.numcertificatqualite) as last_code
#                 FROM enreg_laboreception l
#                 JOIN enreg_cargaison c ON l.idcargaison_id = c.idcargaison
#                 JOIN enreg_entrepot e ON c.entrepot_id = e.identrepot
#                 JOIN enreg_ville v ON e.ville_id = v.idville
#                 WHERE YEAR(l.datereceptionlabo) = {current_year}
#                 AND v.idville = {v}
#                 GROUP BY l.idcargaison_id, c.idcargaison
#             '''
#
#     last_code_result = Cargaison.objects.raw(query)
#     last_code = None
#
#     for result in last_code_result:
#         last_code = result.last_code
#
#     return last_code

def numCq(v):
    current_date = dt.now()
    current_year = current_date.year

    # Perform the ORM query
    result = (
        LaboReception.objects.filter(datereceptionlabo__year=current_year,
                                     idcargaison__idcargaison__entrepot__ville=v)
        .aggregate(max_code=Max('numcertificatqualite'))
    )

    last_code = result['max_code']

    if last_code:
        new_code = last_code + 1
    else:
        new_code = 1

    # print('DEBUG LAST CODE')
    # print(new_code)

    return new_code
