import datetime

from django.db.models import *
from django.shortcuts import get_object_or_404

from enreg.models import *


# Numero de Dossier Annuel et unique
def numRappEch(pk, ville):
    """
    Génère un numéro automatique annuel et séquentiel pour le rapport d’échantillonnage,
    scindé par année ET par ville de l’entrepôt.
    """
    # Année de la cargaison
    carg = get_object_or_404(Cargaison, idcargaison=pk)
    year = carg.dateheurecargaison.date().year

    # Max existant pour (année, ville)
    agg = (
        Entrepot_echantillon.objects
        .filter(
            idcargaison__dateheurecargaison__year=year,
            idcargaison__entrepot__ville=ville
        )
        .aggregate(Max("numrappechauto"))
    )
    current_max = agg.get("numrappechauto__max")
    return 1 if current_max is None else int(current_max) + 1

