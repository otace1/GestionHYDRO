import django_tables2 as tables

from .models import Cargaison

TEMPLATE = """
<a href="{%url 'showqrcode' record.pk%}" class="fa fa-print fa-2x" aria-hidden="true" target=_blank></a> 
      
 """


class CargaisonTable(tables.Table):
    Print = tables.TemplateColumn(TEMPLATE, verbose_name='')
    user = tables.Column(verbose_name='USER')
    dateheurecargaison = tables.Column(verbose_name='DATE & HEURE')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped",
                 "id": "cargaison"}
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'importateur', 'produit', 'volume', 'entrepot', 'numbtfh', 'immatriculation',
                    'numdeclaration', 'manifestdgda', 't1e', 't1d']
        exclude = ['idcargaison', 'valeurfacture', 'frontiere', 'origine', 'rapechctrl', 'requisitionack',
                   'requisitiondackdate', 'numdos', 'numreq', 'numbtfh', 'fournisseur', 'tempcargaison', 'voie',
                   'densitecargaison', 'declarant', 'provenance', 'idchauffeur', 'poids', 'nationalite', 'nomchauffeur',
                   'etat', 'volume_decl15', 'numdossier', 'user', 'codecargaison', 'transporteur', 'qrcode',
                   'impression', 'numact', 'conformite', 'tampon', 'printactdate', 'l_control']
