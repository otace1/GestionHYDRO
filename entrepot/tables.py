import django_tables2 as tables
from enreg.models import Cargaison, Entrepot_echantillon, Dechargement

TEMPLATE = """
              <a href="" data-id="{{record.pk}}" id="idButton" data-toggle="modal" data-target="#Echantilloner" id="modalLink" class="btn btn-info" role="button">Echantillonnage</a>
           """

TEMPLATE1 = """
            <button type="button" data-id="{{record.pk}}" class="btn btn-primary" data-toggle="modal" data-target="#modal-lg">
                  Déchargement
                </button>
           """

TEMPLATE2 = """
    <a href="#" class="btn btn-success">Rapport</a>
"""


class EchantillonTable(tables.Table):
    Echantilloner = tables.TemplateColumn(TEMPLATE, verbose_name='')

    class Meta:
        attrs = {
            "class":"table table-hover text-nowrap table-striped",
            "id":"example2"
        }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['idcargaison','dateheurecargaison', 'importateur','declarant', 'produit','immatriculation', 't1d', 't1e','numdeclaration']
        exclude = ['voie','manifestdgda', 'fournisseur', 'numbtfh', 'valeurfacture',
                   'nomchauffeur', 'numdossier', 'codecargaison', 'tempcargaison', 'densitecargaison', 'idchauffeur',
                   'nationalite', 'qrcode', 'poids', 'provenance', 'transporteur', 'etat', 'frontiere', 'entrepot',
                   'impression', 'volume', 'volume_decl15', 'conformite', 'numact', 'user', 'tampon',
                   'printactdate','l_control']


class CargaisonEchantilloner(tables.Table):
    class Meta:
        model = Entrepot_echantillon


class CargaisonDechargement(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE1, verbose_name='')
    numdossier = tables.Column('# Dos.')
    codecargaison = tables.Column('# Camion')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id":"DechargementTable"
        }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        row_attrs = {
            "id": lambda record: record.pk
        }
        sequence = ['numdossier', 'codecargaison', 'immatriculation','produit']
        exclude = ['idcargaison', 'declarant', 'voie', 'tempcargaison', 'densitecargaison', 'idchauffeur', 't1d', 't1e',
                   'nationalite', 'dateheurecargaison', 'numdeclaration', 'manifestdgda', 'fournisseur',
                   'numbtfh', 'valeurfacture', 'qrcode', 'poids', 'transporteur', 'importateur', 'etat', 'frontiere',
                   'entrepot', 'conformite', 'impression', 'volume', 'volume_decl15', 'provenance', 'nomchauffeur',
                   'numact', 'user', 'tampon', 'printactdate','l_control']


class EchantillonEnregistrer(tables.Table):
    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'importateur', 'immatriculation', 'produit', 't1d', 't1e']
        exclude = ['idcargaison', 'declarant', 'voie', 'tempcargaison', 'densitecargaison', 'idchauffeur', 'nationalite'
            , 'qrcode', 'poids', 'transporteur', 'numdeclaration', 'manifestdgda', 'fournisseur', 'numbtfh',
                   'valeurfacture', 'etat', 'frontiere', 'entrepot', 'impression', 'volume', 'volume_decl15',
                   'nomchauffeur', 'conformite', 'provenance', 'numact', 'user', 'tampon', 'printactdate', 'numdossier',
                   'codecargaison', 'printactdate','l_control']


class CargaisonDechargee(tables.Table):
    # Actions = tables.TemplateColumn(TEMPLATE2)
    gov = tables.Column(verbose_name='GOV')
    gsv = tables.Column(verbose_name='GSV')
    mta = tables.Column(verbose_name='MTA')
    mtv = tables.Column(verbose_name='MTV')
    immatriculation = tables.Column(verbose_name='Immatr.')
    numdossier = tables.Column(verbose_name='# Dos.')
    codecargaison = tables.Column(verbose_name='# Camion')
    datedechargement = tables.Column(verbose_name='Date D.')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Dechargement
        sequence = ['datedechargement', 'numdossier', 'codecargaison', 'immatriculation', 'mta', 'mtv', 'gov', 'gsv']
        exclude = ['idcargaison_id','temperature', 'densite15','idcargaison']
