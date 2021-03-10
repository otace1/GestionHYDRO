from django.contrib import admin

from .models import Cargaison, Entrepot, Ville, Produit, Importateur, Voie, Entrepot_echantillon, LaboReception, \
    Resultat

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
