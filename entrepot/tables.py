import django_tables2 as tables
from enreg.models import Cargaison, Entrepot_echantillon, Dechargement

TEMPLATE = """
            <a href="{%url 'echantillonage' record.pk%}" class="btn btn-primary">ECHANTILLONNAGE</a>
           """

TEMPLATE1 = """
            <a href="{%url 'decharger' record.pk%}" class="btn btn-primary">DECHARGER</a>
           """

TEMPLATE2 = """
    <a href="{%url 'rapport' record.pk%}" class="btn btn-danger">RAPPORT D'INSPECTION</a>
    <a href="{%url 'printcert' record.pk%}" class="btn btn-primary">CERTIFICAT DE QUALITE</a>
            """

TEMPLATE3 = """
    <a href="{%url 'rapportechantillonage' record.pk%}" class="btn btn-danger">RAPPORT D'ECHANTILLONNAGE</a>
            """


class EchantillonTable(tables.Table):
    Echantilloner = tables.TemplateColumn(TEMPLATE, verbose_name='')
    dateheurecargaison = tables.Column(verbose_name="Date d'entree")
    idcargaison = tables.Column(verbose_name='N.Enr.')
    numreq = tables.Column(verbose_name='N.Requisition')
    numdos = tables.Column(verbose_name='N.Dossier')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'importateur', 'declarant', 'produit', 'immatriculation', 'numreq', 'numdos']
        exclude = ['voie', 'idcargaison', 'manifestdgda', 'fournisseur', 'numbtfh', 'valeurfacture',
                   'nomchauffeur', 'numdossier', 'codecargaison', 'tempcargaison', 'densitecargaison', 'idchauffeur',
                   'nationalite', 'qrcode', 'poids', 'provenance', 'transporteur', 'etat', 'frontiere', 'entrepot',
                   'impression', 'volume', 'volume_decl15', 'conformite', 'numact', 'user', 'tampon',
                   'printactdate', 'l_control', 'requisitionack', 'requisitiondackdate', 'origine', 't1d', 't1e',
                   'numdeclaration', 'rapechctrl']


class CargaisonEnAttenteRequisition(tables.Table):
    dateheurecargaison = tables.Column(verbose_name="Date d'entree")
    idcargaison = tables.Column(verbose_name='N.Enr.')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'importateur', 'produit', 'immatriculation']
        exclude = ['idcargaison', 'voie', 'manifestdgda', 'declarant', 't1d', 't1e', 'fournisseur', 'numbtfh',
                   'valeurfacture',
                   'nomchauffeur', 'numdossier', 'codecargaison', 'tempcargaison', 'densitecargaison', 'idchauffeur',
                   'nationalite', 'qrcode', 'poids', 'provenance', 'transporteur', 'etat', 'frontiere', 'entrepot',
                   'impression', 'volume', 'volume_decl15', 'conformite', 'numact', 'user', 'tampon',
                   'printactdate', 'l_control', 'requisitionack', 'requisitiondackdate', 'numdos', 'numreq', 'origine',
                   'numdeclaration', 'rapechctrl']


class RapportEchantillonage(tables.Table):
    impressionre = tables.TemplateColumn(TEMPLATE3, verbose_name='')
    dateheurecargaison = tables.Column(verbose_name="Date d'entree")
    idcargaison = tables.Column(verbose_name='N.Enr.')
    numreq = tables.Column(verbose_name='N.Requisition')
    numdos = tables.Column(verbose_name='N.Dossier')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'importateur', 'declarant', 'produit', 'immatriculation',
                    't1d', 't1e', 'numreq', 'numdos']
        exclude = ['idcargaison', 'voie', 'manifestdgda', 'fournisseur', 'numbtfh', 'valeurfacture',
                   'nomchauffeur', 'numdossier', 'codecargaison', 'tempcargaison', 'densitecargaison', 'idchauffeur',
                   'nationalite', 'qrcode', 'poids', 'provenance', 'transporteur', 'etat', 'frontiere', 'entrepot',
                   'impression', 'volume', 'volume_decl15', 'conformite', 'numact', 'user', 'tampon',
                   'printactdate', 'l_control', 'requisitionack', 'requisitiondackdate', 'origine',
                   'numdeclaration', 'rapechctrl']


class CargaisonDechargement(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE1, verbose_name='')
    # numdossier = tables.Column(verbose_name='Num. Dossier')
    # codecargaison = tables.Column(verbose_name='#Camion/Wagon/Navire')
    idcargaison__idcargaison__idcargaison__produit = tables.Column(verbose_name='Produit')
    massevolumique15 = tables.Column(verbose_name='Densité a 15°')
    idcargaison__idcargaison__idcargaison__immatriculation = tables.Column(verbose_name='Immatriculation')
    idcargaison__idcargaison__idcargaison__importateur = tables.Column(verbose_name='Importateur')
    # idcargaison__idcargaison__idcargaison__numreq = tables.Column(verbose_name='Ref. requisition Client')
    idcargaison__idcargaison__idcargaison__numdos = tables.Column(verbose_name='Num. Dossier')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "DechargementTable"
        }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        row_attrs = {
            "id": lambda record: record.pk
        }
        sequence = ['idcargaison__idcargaison__idcargaison__importateur',
                    'idcargaison__idcargaison__idcargaison__numdos',
                    'idcargaison__idcargaison__idcargaison__immatriculation',
                    'idcargaison__idcargaison__idcargaison__produit', 'massevolumique15']
        exclude = ['idcargaison', 'declarant', 'voie', 'tempcargaison', 'densitecargaison', 'idchauffeur', 't1d', 't1e',
                   'numreq', 'importateur', 'numdos', 'immatriculation', 'immatriculation', 'produit', 'nationalite',
                   'dateheurecargaison', 'numdeclaration', 'manifestdgda', 'fournisseur',
                   'numbtfh', 'valeurfacture', 'qrcode', 'poids', 'transporteur', 'etat', 'frontiere',
                   'entrepot', 'conformite', 'impression', 'volume', 'volume_decl15', 'provenance', 'nomchauffeur',
                   'numact', 'user', 'tampon', 'codecargaison', 'printactdate', 'l_control', 'numdossier', 'rapechctrl',
                   'requisitiondackdate', 'requisitionack', 'origine']


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
    Actions = tables.TemplateColumn(TEMPLATE2, verbose_name='')
    gov = tables.Column(verbose_name='GOV')
    gsv = tables.Column(verbose_name='GSV')
    mta = tables.Column(verbose_name='MTA')
    mtv = tables.Column(verbose_name='MTV')
    idcargaison__idcargaison__idcargaison__idcargaison__immatriculation = tables.Column(verbose_name='Immatriculation')
    idcargaison__idcargaison__idcargaison__idcargaison__numdos = tables.Column(verbose_name='Num. Dossier')
    idcargaison__idcargaison__idcargaison__idcargaison__numreq = tables.Column(verbose_name='Ref. Req.')
    datedechargement = tables.Column(verbose_name='Date D.')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Dechargement
        sequence = ['datedechargement', 'idcargaison__idcargaison__idcargaison__idcargaison__numdos',
                    'idcargaison__idcargaison__idcargaison__idcargaison__numreq',
                    'idcargaison__idcargaison__idcargaison__idcargaison__immatriculation', 'mta', 'mtv', 'gov', 'gsv']
        exclude = ['idcargaison_id', 'temperature', 'densite15', 'idcargaison', 'vcf', 'indexinitial', 'indexfinal',
                   'typescontainer']
