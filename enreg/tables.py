import django_tables2 as tables

from .models import Cargaison

TEMPLATE = """
<a href="{%url 'showqrcode' record.pk%}" class="fa fa-print fa-2x" aria-hidden="true" target=_blank></a> 
      
 """


class CargaisonTable(tables.Table):
    Print = tables.TemplateColumn(TEMPLATE, verbose_name='')
    importateur = tables.Column(verbose_name='IMPORTATEUR')
    user = tables.Column(verbose_name='USER')
    volume = tables.Column(verbose_name='VOL.AMBIANT')
    volume15 = tables.Column(verbose_name='VOL.15°C')
    volume20 = tables.Column(verbose_name='VOL.20°C')
    tonnagevide = tables.Column(verbose_name='TONNAGE VIDE')
    tonnageair = tables.Column(verbose_name='TONNAGE AIR')
    entrepot = tables.Column(verbose_name='ENTREPOT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    dateheurecargaison = tables.Column(verbose_name='DATE & HEURE')
    produit = tables.Column(verbose_name='PRODUIT')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped",
                 "id": "cargaison"}
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'importateur', 'produit', 'volume', 'volume15', 'volume20', 'tonnagevide',
                    'tonnageair', 'entrepot', 'immatriculation']
        exclude = ['idcargaison', 'valeurfacture', 'frontiere', 'origine', 'rapechctrl', 'requisitionack',
                   'typeunitetransport',
                   'requisitiondackdate', 'numdos', 'numreq', 'voie', 'provenance', 'poids',
                   'etat', 'numdossier', 'user', 'codecargaison', 'qrcode', 'impression', 'numact', 'conformite',
                   'tampon', 'printactdate', 'l_control']
