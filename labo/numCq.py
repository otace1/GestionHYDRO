from django.db import transaction

from enreg.models import *
from accounts.models import *
from django.db.models import *
from django.contrib.auth.decorators import login_required
import datetime


def numCq(v, pk):
    c = Entrepot_echantillon.objects.get(idcargaison=pk)
    year_value = c.dateechantillonage.year

    with transaction.atomic():
        # Fetch the current maximum numcertificatqualite value while acquiring a lock
        max_cert_query = LaboReception.objects.filter(
            datereceptionlabo__year=year_value,
            idcargaison__idcargaison__entrepot__ville=v
        ).order_by('-numcertificatqualite').first()

        if max_cert_query:
            numcertificatqualite = max_cert_query.numcertificatqualite
        else:
            numcertificatqualite = 0

        # Generate the next numcertificatqualite value and update it atomically
        next_numcertificatqualite = numcertificatqualite + 1
        LaboReception.objects.filter(
            datereceptionlabo__year=year_value,
            idcargaison__idcargaison__entrepot__ville=v
        ).update(numcertificatqualite=F('numcertificatqualite') + 1)

    return next_numcertificatqualite


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