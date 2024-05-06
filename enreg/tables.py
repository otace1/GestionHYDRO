import django_tables2 as tables

from .models import Cargaison

TEMPLATE = """
<a href="{%url 'showqrcode' record.pk%}" class="btn btn-warning" aria-hidden="true" target=_blank>IMPRESSION QRCODE</a> 
      
 """



class CargaisonTable(tables.Table):
    print = tables.TemplateColumn(TEMPLATE, verbose_name='ACTIONS')
    importateur = tables.Column(verbose_name='IMPORTATEUR')
    user = tables.Column(verbose_name='USER')
    volume = tables.Column(verbose_name='VOL.AMBIANT')
    # volume15 = tables.Column(verbose_name='VOL.15°C')
    # volume20 = tables.Column(verbose_name='VOL.20°C')
    # tonnagevide = tables.Column(verbose_name='TONNAGE VIDE')
    # tonnageair = tables.Column(verbose_name='TONNAGE AIR')
    entrepot = tables.Column(verbose_name='ENTREPOT DE DEST.')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    dateheurecargaison = tables.Column(verbose_name='DATE & HEURE')
    produit = tables.Column(verbose_name='PRODUIT')

    class Meta:
        # attrs = {
        #     "class": "table table-bordered table-striped",
        #     "id": "example1"
        # }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'importateur', 'entrepot', 'immatriculation', 'produit', 'volume','print']
        exclude = ['files_path','dateHeureAnalyseLabo','idcargaison','etatInspection' ,'valeurfacture', 'frontiere', 'origine', 'rapechctrl', 'requisitionack',
                   'typeunitetransport', 'controlOrganoleptique','dateDechargement','volume15',
                    'volume20', 'tonnagevide','toBeRefouler','toBeConsignated','isConsignated','isRefouler',
                    'tonnageair','transitaire',
                   'requisitiondackdate', 'numdos', 'numreq', 'voie', 'provenance', 'poids',
                   'etat', 'numdossier', 'user', 'codecargaison', 'qrcode', 'impression', 'numact', 'conformite',
                   'tampon', 'printactdate', 'l_control', 'before', 'after', 'declaration','numCertInspection']
