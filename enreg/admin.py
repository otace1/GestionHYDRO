from django.contrib import admin

from .models import *
from accounts.models import *

# Register your models here.

admin.site.register(Voie)
admin.site.register(Cargaison)
admin.site.register(Entrepot)
admin.site.register(Ville)
admin.site.register(Produit)
admin.site.register(Importateur)
admin.site.register(Entrepot_echantillon)
admin.site.register(LaboReception)
admin.site.register(Resultat)
admin.site.register(TypeUniteTransport)
admin.site.register(Nationalites)
admin.site.register(Dechargement)
admin.site.register(SealState)
admin.site.register(InspectionSeal)
admin.site.register(Inspection)
admin.site.register(Compartiment)
admin.site.register(ShoreTank)
admin.site.register(ParametresProduits)
admin.site.register(AffectationParametre)
admin.site.register(ResultatAnalyse)
admin.site.register(ListeLaboratoire)
admin.site.register(AffectationLaboratoire)
