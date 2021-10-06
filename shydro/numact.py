from enreg.models import Cargaison
from django.db import connection, transaction
from django.db.models import Max
from datetime import date
import datetime

#Numéro ACT calcul
def numeroactcurrent(pk):

    d = Cargaison.objects.get(idcargaison=pk)
    d = d.dateheurecargaison
    d = datetime.datetime.date(d)
    d = d.year

    c = Cargaison.objects.filter(dateheurecargaison__year=d).aggregate(Max('numact'))

    if c.get('numact__max') == None:
        numact = 1
    else:
        numact = c.get('numact__max')
        numact = numact + 1

    return numact








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

