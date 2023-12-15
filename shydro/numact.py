from django.db import transaction, connection

from enreg.models import *
from accounts.models import *
from datetime import datetime
from django.db.models import *
from datetime import datetime


# Numero de Dossier Annuel et unique
def num_cert_inspection(ville):
    current_year = datetime.now().year

    # max_value_query = Cargaison.objects.filter(
    #     dateheurecargaison__year=current_year,
    #     entrepot__ville__affectationville=ville,
    #     numCertInspection__isnull=False,
    # ).aggregate(Max('numCertInspection'))

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT MAX(numCertInspection)
            FROM enreg_cargaison
            WHERE YEAR(dateheurecargaison) = %s
              AND entrepot_id IN (
                SELECT identrepot
                FROM enreg_entrepot
                WHERE ville_id = %s
              )
              AND numCertInspection IS NOT NULL
        """, [current_year, ville])

        row = cursor.fetchone()
        num_cert_inspection_max = row[0]

    # print("NUM CERT")
    # print(num_cert_inspection_max)

    if num_cert_inspection_max is None:
        return 1
    else:
        return num_cert_inspection_max + 1














# from enreg.models import Cargaison
# from django.db import connection, transaction
# from django.db.models import Max
# from datetime import date
# import datetime
#
# #Numéro ACT calcul
# def numeroactcurrent(pk):
#
#     d = Cargaison.objects.get(idcargaison=pk)
#     d = d.dateheurecargaison
#     d = datetime.datetime.date(d)
#     d = d.year
#
#     c = Cargaison.objects.filter(dateheurecargaison__year=d).aggregate(Max('numact'))
#
#     if c.get('numact__max') == None:
#         numact = 1
#     else:
#         numact = c.get('numact__max')
#         numact = numact + 1
#
#     return numact
#
#






    #
    # a = connection.cursor()
    # a.execute('SELECT idcargaison \
    #            FROM hydro_occ.enreg_cargaison \
    #            WHERE numact= %s \
    #            AND  YEAR(dateheurecargaison)=YEAR(CURRENT_DATE)',[i,])
    # reponse = a.fetchall()
    # if reponse:
    #     return 1
    # else:
    #     a = connection.cursor()
    #     a.execute('SELECT idcargaison \
    #                 FROM hydro_occ.enreg_cargaison \
    #                 WHERE numact= %s \
    #                 AND YEAR(dateheurecargaison)=YEAR(DATE_SUB(CURDATE(), INTERVAL 1 YEAR))', [i, ])
    #
    #     reponse = a.fetchall()
    #     if reponse :
    #         return 1
    #     else:
    #         return 0


# def numeroactold(i):
#     a = connection.cursor()
#     a.execute('SELECT idcargaison \
#                           FROM hydro_occ.enreg_cargaison \
#                           WHERE numact= %s \
#                           AND YEAR(dateheurecargaison)=YEAR(DATE_SUB(CURDATE(), INTERVAL 1 YEAR))', [i, ])
#
#     reponse = a.fetchall()
#     if reponse:
#         return 1
#     else:
#         return 0

