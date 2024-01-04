from django.db import transaction

from enreg.models import *
from accounts.models import *
from datetime import datetime
from django.db.models import *
from datetime import datetime


def numDossier(ville,pk):
    current_date = datetime.now()
    current_year = current_date.year

    # Get the record
    record = Cargaison.objects.get(idcargaison=pk)

    # Check if the record's year is equal to the current year
    if record.dateheurecargaison.year == current_year:
        print('CURRENT YEAR')
        last_code_result_current = Cargaison.objects.filter(
            dateheurecargaison__year=current_year,
            entrepot__ville__idville=ville
        ).aggregate(last_code=Max('numdos'))

        # Use the 'get' method to retrieve the 'last_code' value
        last_code = last_code_result_current.get('last_code', 0)
        if last_code is None:
            last_code = 0
        return last_code + 1


    # Check if the record's year is equal to the previous year
    if record.dateheurecargaison.year == current_year - 1:
        print('PAST YEAR')
        last_code_result_previous = Cargaison.objects.filter(
            dateheurecargaison__year=current_year -1,
            entrepot__ville__idville=ville
        ).aggregate(last_code=Max('numdos'))

        # Use the 'get' method to retrieve the 'last_code' value
        last_code = last_code_result_previous.get('last_code', 0)
        if last_code is None:
            last_code = 0
        return last_code + 1






