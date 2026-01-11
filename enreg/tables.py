import django_tables2 as tables
from django.utils.translation import gettext_lazy as _
from .models import Cargaison

ACTIONS_TEMPLATE = """
{% load i18n %}
<button class="btn btn-info btn-sm btn-cargaison-details" data-id="{{ record.pk }}" title="{% trans 'Détails' %}">
    <i class="fas fa-eye mr-1"></i> {% trans "Détails" %}
</button>
"""

class CargaisonTable(tables.Table):
    dateheurecargaison = tables.DateTimeColumn(format='d M Y, H:i', verbose_name=_('DATE & HEURE'))
    declaration = tables.Column(verbose_name=_('DÉCLARATION'))
    importateur = tables.Column(accessor='nom_importateur', verbose_name=_('IMPORTATEUR'))
    entrepot = tables.Column(accessor='nom_entrepot', verbose_name=_('ENTREPÔT'))
    immatriculation = tables.Column(verbose_name=_('IMMATRICULATION'))
    produit = tables.Column(accessor='nom_produit', verbose_name=_('PRODUIT'))
    volume = tables.TemplateColumn('{{ record.volume }} L', verbose_name=_('VOLUME'))
    actions = tables.TemplateColumn(ACTIONS_TEMPLATE, verbose_name=_('ACTIONS'), orderable=False)

    class Meta:
        model = Cargaison
        template_name = "django_tables2/bootstrap4.html"
        fields = ('dateheurecargaison', 'declaration', 'importateur', 'entrepot', 'immatriculation', 'produit', 'volume', 'actions')
        sequence = ('dateheurecargaison', 'declaration', 'importateur', 'entrepot', 'immatriculation', 'produit', 'volume', 'actions')
