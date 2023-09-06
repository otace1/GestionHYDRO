from django.db import transaction

from enreg.models import *
from accounts.models import *
from datetime import datetime
from django.db.models import *
from datetime import datetime


# Numero de Dossier Annuel et unique
def numDossier(ville):
    current_date = datetime.now()
    current_year = current_date.year
    query = f'''
            SELECT c.idcargaison, MAX(c.numdos) as last_code
            FROM enreg_cargaison c
            JOIN enreg_entrepot e ON c.entrepot_id = e.identrepot
            JOIN enreg_ville v ON e.ville_id = v.idville
            WHERE YEAR(c.dateheurecargaison) = {current_year}
            AND v.idville = {ville}
        '''

    last_code_result = Cargaison.objects.raw(query)
    last_code = None

    for result in last_code_result:
        last_code = result.last_code

    # print('LAST CODE:')
    # print(last_code)

    return last_code


    #
    # max_numdos_query = Cargaison.objects.filter(dateheurecargaison__year=year_value,
    #                                             entrepot__ville__idville=ville).order_by('-numdos').first()
    #
    # if max_numdos_query:
    #     max_numdos = max_numdos_query.numdos
    # else:
    #     max_numdos = 0
    #
    # return max_numdos




    #
    #
    #
    # for result in last_code_result:
    #     last_code = result.last_code
    #
    # # print('LAST CODE:')
    # # print(last_code)







